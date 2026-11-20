import streamlit as st
import pandas as pd
import numpy as np
import math
import os
import base64
import json
import urllib.request
import urllib.error
from itertools import permutations
from datetime import date, datetime

# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="Nilovea Racing Command Centre | PLE & Trifecta Engine",
    page_icon="🐎",
    layout="wide",
)

LIVE_RESULTS_FILE = "racing_live_results.csv"


# ==============================================================================
# GITHUB PERSISTENT STORAGE HELPER (LOCKS RESULTS INTO REPO)
# ==============================================================================
def push_csv_to_github(file_path: str, csv_content: str, commit_msg: str) -> tuple[bool, str]:
    """Commits updated racing results straight back into GitHub so data persists permanently."""
    token = st.secrets.get("GITHUB_TOKEN", None) if hasattr(st, "secrets") else None
    repo = (
        st.secrets.get("GITHUB_REPO", "g3ffr0-netizen/nfl-unicorn")
        if hasattr(st, "secrets")
        else "g3ffr0-netizen/nfl-unicorn"
    )
    if not token:
        return False, "No `GITHUB_TOKEN` found in Streamlit Secrets (saved locally & downloadable below)."

    api_url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "Nilovea-Racing-App",
    }

    sha = None
    try:
        req_get = urllib.request.Request(api_url, headers=headers, method="GET")
        with urllib.request.urlopen(req_get, timeout=10) as resp:
            existing_data = json.loads(resp.read().decode("utf-8"))
            sha = existing_data.get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            return False, f"GitHub lookup error ({e.code}): {e.reason}"
    except Exception as e:
        return False, f"GitHub connection error: {e}"

    payload = {
        "message": commit_msg,
        "content": base64.b64encode(csv_content.encode("utf-8")).decode("utf-8"),
        "branch": "main",
    }
    if sha:
        payload["sha"] = sha

    try:
        req_put = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="PUT",
        )
        with urllib.request.urlopen(req_put, timeout=15) as resp:
            if resp.status in (200, 201):
                return True, f"Synced `{file_path}` to `{repo}`."
            return False, f"Unexpected GitHub response status: {resp.status}"
    except Exception as e:
        return False, f"Failed to commit CSV to GitHub: {e}"


def load_live_results() -> pd.DataFrame:
    """Loads existing live results CSV from local workspace or initializes an empty ledger."""
    cols = [
        "Date",
        "Venue",
        "Race",
        "Distance_m",
        "Track",
        "Top_Pick",
        "Actual_1st",
        "Actual_2nd",
        "Actual_3rd",
        "Bet_Type",
        "Outlay",
        "Return",
        "Profit",
        "Notes",
    ]
    if os.path.exists(LIVE_RESULTS_FILE):
        try:
            df = pd.read_csv(LIVE_RESULTS_FILE)
            for c in cols:
                if c not in df.columns:
                    df[c] = ""
            return df[cols]
        except Exception:
            pass
    return pd.DataFrame(columns=cols)


# ==============================================================================
# PROBABILITY, VIG STRIPPING, PLE SHRINKAGE & KELLY FUNCTIONS
# ==============================================================================
def strip_field_vig(odds: np.ndarray) -> tuple[np.ndarray, float]:
    """Converts decimal odds into vig-free implied probabilities and returns overround %."""
    clean_odds = np.where(np.asarray(odds, dtype=float) > 1.0, np.asarray(odds, dtype=float), np.nan)
    raw_implied = np.where(np.isnan(clean_odds), 0.0, 1.0 / clean_odds)
    overround = float(np.sum(raw_implied))
    if overround <= 0:
        n = len(odds)
        return np.full(n, 1.0 / max(n, 1)), 0.0
    fair_probs = raw_implied / overround
    return fair_probs, overround * 100.0


def ratings_to_probs(fr_scores: np.ndarray, rating_temp: float = 2.2, aggressive: bool = False) -> np.ndarray:
    """
    Converts Superform Final Ratings (kg) to win probabilities via softmax.
    Aggressive price line compresses temperature by 28% to tighten top contenders.
    """
    scores = np.asarray(fr_scores, dtype=float)
    if len(scores) == 0:
        return np.array([])
    eff_temp = max(0.25, rating_temp * (0.72 if aggressive else 1.0))
    shifted = (scores - np.max(scores)) / eff_temp
    exp_s = np.exp(np.clip(shifted, -50, 50))
    total = np.sum(exp_s)
    return exp_s / total if total > 0 else np.full(len(scores), 1.0 / len(scores))


def ple_shrinkage_field(
    model_probs: np.ndarray,
    market_probs: np.ndarray,
    shrinkage_lambda: float = 0.35,
    mode: str = "PLE Shrinkage Blend",
) -> np.ndarray:
    """Blends model probabilities with vig-stripped market prior under PLE shrinkage."""
    m_p = np.asarray(model_probs, dtype=float)
    mkt_p = np.asarray(market_probs, dtype=float)
    if mode == "Pure Model (Superform FR)":
        blended = m_p
    elif mode == "Market Anchored (70% Market)":
        blended = 0.30 * m_p + 0.70 * mkt_p
    else:
        lam = float(np.clip(shrinkage_lambda, 0.0, 1.0))
        blended = (1.0 - lam) * m_p + lam * mkt_p
    s = np.sum(blended)
    return blended / s if s > 0 else m_p


def kelly_fraction(prob: float, decimal_odds: float, kelly_mult: float = 0.25, max_cap: float = 0.05) -> float:
    """Fractional Kelly staking with safety cap."""
    if decimal_odds <= 1.0 or prob <= 0.0 or prob >= 1.0:
        return 0.0
    b = decimal_odds - 1.0
    q = 1.0 - prob
    full_kelly = (b * prob - q) / b
    if full_kelly <= 0:
        return 0.0
    return float(min(max_cap, full_kelly * kelly_mult))


def harville_exacta_prob(probs: np.ndarray, i: int, j: int) -> float:
    """Harville probability that runner i finishes 1st and runner j finishes 2nd."""
    if i == j:
        return 0.0
    p_i = probs[i]
    p_j = probs[j]
    denom = 1.0 - p_i
    if p_i <= 0 or p_j <= 0 or denom <= 1e-9:
        return 0.0
    return float(p_i * (p_j / denom))


def harville_trifecta_prob(probs: np.ndarray, i: int, j: int, k: int) -> float:
    """Harville probability for exact 1st=i, 2nd=j, 3rd=k finishing order."""
    if len({i, j, k}) < 3:
        return 0.0
    p_i, p_j, p_k = probs[i], probs[j], probs[k]
    d1 = 1.0 - p_i
    d2 = 1.0 - p_i - p_j
    if p_i <= 0 or p_j <= 0 or p_k <= 0 or d1 <= 1e-9 or d2 <= 1e-9:
        return 0.0
    return float(p_i * (p_j / d1) * (p_k / d2))


# ==============================================================================
# SUPERFORM ONLINE V1.4 SITUATIONAL, DUAL-MODEL & EASY RATER ENGINE
# ==============================================================================
def compute_situational_ratings(
    df: pd.DataFrame,
    race_dist: int,
    track_cond: str,
    limit_weight: float,
    rating_temp: float,
    shrinkage_lambda: float,
    mode: str,
    market_level_pct: float = 85.0,
    aggressive_odds: bool = False,
    factor_weights: dict[str, float] | None = None,
    max_rank_cap: int = 25,
) -> pd.DataFrame:
    """
    Full Superform Online v1.4 + PLE Pipeline:
      1. Filters scratched runners & shifts outside barriers inward by 1 gate.
      2. Applies modular kg adjustments (Base, Form, Cond, Cons, BP_Adj, Own, JocRat penalty,
         JAllow, Weight Over Limit, Jockey-Won-On-Horse switch bonus, +4kg rise penalty,
         GR >= 50% consistency, WT wet handling, Spell/Let-up timing curves, Field Strength delta,
         and +/- 10% distance band reliability).
      3. Computes MOD1 (Career + Weight Regression), MOD2 (Pure Weight Ensemble), and
         Rank-Capped Easy Rater Scoreline.
      4. Converts Final Rating (FR) to 1.5kg/length margins, PLE probabilities, and
         80%-90% Value Market Minimum Acceptable Odds.
    """
    work = df.copy()
    if "Scratched" not in work.columns:
        work["Scratched"] = False

    # 1. Dynamic Scratching & Barrier Shift
    scratched_bps = sorted(work.loc[work["Scratched"] == True, "BP"].dropna().astype(int).tolist())
    active = work[work["Scratched"] != True].copy().reset_index(drop=True)
    if active.empty:
        return active

    active["Eff_BP"] = active["BP"].astype(int).apply(lambda b: max(1, b - sum(sb < b for sb in scratched_bps)))
    gate_shift_gain = (active["BP"].astype(int) - active["Eff_BP"]) * 0.25
    active["Adj_BP_kg"] = active["BP_Adj"].astype(float) + gate_shift_gain

    # 2. Superform Situational Deltas
    # Jockey switch bonus: previous rider non-winner on horse -> today's rider has won on horse
    jock_win_bonus = np.where(
        (active["Jockey_Horse_Wins"] > 0) & (active["Prev_Jockey_Won"] == False),
        1.0,
        0.0,
    )

    # Heavy weight rise flag (+4.0 kg or more = negative; +2 to +3 kg = neutral)
    weight_diff = active["Weight"].astype(float) - active["Prev_Weight"].astype(float)
    weight_rise_pen = np.where(weight_diff >= 4.0, -1.5, np.where(weight_diff <= -3.0, 0.5, 0.0))

    # Good Run Index (GR % within 3 lengths): >= 50% indicates true consistency
    gr_bonus = np.where(active["GR_Pct"] >= 50.0, 0.5, np.where(active["GR_Pct"] < 35.0, -0.5, 0.0))

    # Track Condition / Wet Track Index (WT % within 3 lengths on Dead/Soft/Heavy)
    is_wet = track_cond in ("Soft (Slow)", "Heavy")
    wet_bonus = np.where(
        is_wet,
        np.where(active["WT_Pct"] >= 50.0, 1.0, np.where(active["WT_Pct"] < 30.0, -1.5, 0.0)),
        0.0,
    )

    # Spell (63+ days) & Let-Up (35-62 days) + Distance Timing Curve
    is_sprint = race_dist <= 1300
    is_staying = race_dist >= 1600
    prep_run = active["Prep_Run"].astype(int)
    timing_bonus = np.where(
        is_sprint & prep_run.isin([1, 2, 3]),
        0.5,
        np.where(is_staying & prep_run.isin([3, 4, 5]), 0.5, 0.0),
    )

    # +/- 10% Distance Band & Field Strength Kg Adjustment
    dist_band_bonus = np.where(active["Dist_10pct_Match"] == True, 0.75, -0.5)
    # Field_Strength_Diff: +1.5 means today's race is 1.5kg stronger than last start
    fs_adj = -0.5 * active["Field_Strength_Diff"].astype(float)

    # Weight Over Limit (WOL)
    active["WOL"] = active["Weight"].astype(float) - float(limit_weight)

    # Superform Final Rating (FR) in kg
    # Note: JocRat is a penalty (lower = stronger jockey), so it is subtracted
    active["Auto_Sit_kg"] = (
        jock_win_bonus
        + weight_rise_pen
        + gr_bonus
        + wet_bonus
        + timing_bonus
        + dist_band_bonus
        + fs_adj
    )

    active["FR"] = (
        active["Base"].astype(float)
        + active["Form"].astype(float)
        + active["Cond"].astype(float)
        + active["Cons"].astype(float)
        + active["Adj_BP_kg"]
        + active["Own"].astype(float)
        - active["JocRat"].astype(float)
        + active["JAllow"].astype(float)
        - active["WOL"]
        + active["Auto_Sit_kg"]
    )

    # Predicted Margin (1.5 kg = 1 length)
    top_fr = float(active["FR"].max())
    active["Margin_kg"] = (top_fr - active["FR"]).round(2)
    active["Margin_Len"] = (active["Margin_kg"] / 1.5).round(2)

    # 3. Dual Regression Models (MOD1 Career+Weight vs. MOD2 Pure Weight Ensemble)
    career_score = (
        0.35 * active["Win_Pct"].astype(float)
        + 0.25 * active["GR_Pct"].astype(float)
        + 0.20 * active["Dist_Win_Pct"].astype(float)
        + 2.0 * active["FR"]
    )
    weight_ensemble_score = (
        0.45 * active["FR"]
        + 0.25 * active["Ex_Pk"].astype(float)
        + 0.20 * active["Base"].astype(float)
        + 0.10 * active["Class_Rat"].astype(float)
    )

    active["MOD1_Rank"] = career_score.rank(ascending=False, method="min").astype(int)
    active["MOD2_Rank"] = weight_ensemble_score.rank(ascending=False, method="min").astype(int)

    # Sub-factor rankings for Easy Rater
    factor_ranks = {
        "MOD1": active["MOD1_Rank"],
        "MOD2": active["MOD2_Rank"],
        "Improve": (active["Ex_Pk"].astype(float) - active["Base"].astype(float) + active["Form"].astype(float)).rank(
            ascending=False, method="min"
        ),
        "Dist_10pct": (active["Dist_Win_Pct"].astype(float) + np.where(active["Dist_10pct_Match"], 15.0, 0.0)).rank(
            ascending=False, method="min"
        ),
        "Ability_GR": active["GR_Pct"].astype(float).rank(ascending=False, method="min"),
        "Ex_Pk": active["Ex_Pk"].astype(float).rank(ascending=False, method="min"),
        "Class": active["Class_Rat"].astype(float).rank(ascending=False, method="min"),
        "Wet_WT": active["WT_Pct"].astype(float).rank(ascending=False, method="min"),
    }

    default_weights = {
        "MOD1": 1.25,
        "MOD2": 1.25,
        "Improve": 1.00,
        "Dist_10pct": 1.15,
        "Ability_GR": 1.00,
        "Ex_Pk": 0.90,
        "Class": 1.00,
        "Wet_WT": 1.20 if is_wet else 0.40,
    }
    weights = factor_weights if factor_weights is not None else default_weights

    easy_sum = np.zeros(len(active), dtype=float)
    for fname, r_series in factor_ranks.items():
        w = float(weights.get(fname, 1.0))
        if w > 0:
            capped_rank = np.minimum(r_series.astype(float), float(max_rank_cap))
            easy_sum += w * capped_rank

    active["Easy_Sum"] = easy_sum.round(2)
    active["Easy_Rank"] = active["Easy_Sum"].rank(ascending=True, method="min").astype(int)

    # 4. Probabilities, PLE Shrinkage & Value Market Book (80%-90%)
    model_probs = ratings_to_probs(active["FR"].to_numpy(), rating_temp=rating_temp, aggressive=aggressive_odds)
    mkt_probs, overround = strip_field_vig(active["Tote_Odds"].to_numpy())
    ple_probs = ple_shrinkage_field(model_probs, mkt_probs, shrinkage_lambda=shrinkage_lambda, mode=mode)

    active["Model_Pct"] = (model_probs * 100.0).round(1)
    active["Mkt_Fair_Pct"] = (mkt_probs * 100.0).round(1)
    active["PLE_Prob"] = ple_probs
    active["PLE_Pct"] = (ple_probs * 100.0).round(1)

    # Value Book Scaling (e.g. 85% market level -> requires 15% edge before betting)
    book_scale = float(market_level_pct) / 100.0
    scaled_probs = np.clip(ple_probs * book_scale, 1e-5, 0.99)
    active["Min_Accept_Odds"] = (1.0 / scaled_probs).round(2)
    active["Fair_Odds"] = (1.0 / np.clip(ple_probs, 1e-5, 0.99)).round(2)
    active["EV_Pct"] = ((ple_probs * active["Tote_Odds"].astype(float) - 1.0) * 100.0).round(1)
    active["Value_Flag"] = np.where(
        active["Tote_Odds"].astype(float) >= active["Min_Accept_Odds"],
        "✅ VALUE",
        "—",
    )
    active.attrs["overround"] = overround
    return active


# ==============================================================================
# SAMPLE FIELD INITIALIZER (FLEMINGTON / METRO BENCHMARK)
# ==============================================================================
def get_default_field() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Scratched": False,
                "TAB": 1,
                "Horse": "DARALIMARA",
                "BP": 4,
                "Weight": 58.5,
                "Prev_Weight": 57.0,
                "Ex_Pk": 54.0,
                "Base": 51.5,
                "Form": 2.0,
                "Cond": 0.0,
                "Cons": 0.0,
                "BP_Adj": 0.5,
                "Own": 0.0,
                "JocRat": 1.0,
                "JAllow": 0.0,
                "Jockey_Horse_Wins": 2,
                "Prev_Jockey_Won": False,
                "GR_Pct": 62.0,
                "WT_Pct": 55.0,
                "Win_Pct": 24.0,
                "Dist_Win_Pct": 33.0,
                "Class_Rat": 52.0,
                "DLR": 14,
                "Prep_Run": 3,
                "Dist_10pct_Match": True,
                "Field_Strength_Diff": -1.0,
                "Tote_Odds": 4.20,
            },
            {
                "Scratched": False,
                "TAB": 2,
                "Horse": "PORTLAND SINGA",
                "BP": 7,
                "Weight": 57.0,
                "Prev_Weight": 53.0,
                "Ex_Pk": 53.5,
                "Base": 51.0,
                "Form": 1.0,
                "Cond": 0.0,
                "Cons": 0.0,
                "BP_Adj": -0.5,
                "Own": 0.0,
                "JocRat": 1.5,
                "JAllow": 0.0,
                "Jockey_Horse_Wins": 1,
                "Prev_Jockey_Won": True,
                "GR_Pct": 54.0,
                "WT_Pct": 48.0,
                "Win_Pct": 20.0,
                "Dist_Win_Pct": 25.0,
                "Class_Rat": 51.5,
                "DLR": 21,
                "Prep_Run": 4,
                "Dist_10pct_Match": True,
                "Field_Strength_Diff": 0.5,
                "Tote_Odds": 5.50,
            },
            {
                "Scratched": False,
                "TAB": 3,
                "Horse": "BRAVE PLAYER",
                "BP": 2,
                "Weight": 56.0,
                "Prev_Weight": 56.5,
                "Ex_Pk": 53.0,
                "Base": 50.0,
                "Form": 2.5,
                "Cond": 0.0,
                "Cons": -0.5,
                "BP_Adj": 1.0,
                "Own": 0.5,
                "JocRat": 1.5,
                "JAllow": 0.0,
                "Jockey_Horse_Wins": 1,
                "Prev_Jockey_Won": False,
                "GR_Pct": 58.0,
                "WT_Pct": 60.0,
                "Win_Pct": 22.0,
                "Dist_Win_Pct": 30.0,
                "Class_Rat": 50.5,
                "DLR": 14,
                "Prep_Run": 2,
                "Dist_10pct_Match": True,
                "Field_Strength_Diff": -1.5,
                "Tote_Odds": 6.50,
            },
            {
                "Scratched": False,
                "TAB": 4,
                "Horse": "WEST COUNTRY",
                "BP": 10,
                "Weight": 55.5,
                "Prev_Weight": 55.0,
                "Ex_Pk": 51.5,
                "Base": 49.5,
                "Form": 1.0,
                "Cond": 0.0,
                "Cons": 0.0,
                "BP_Adj": -1.0,
                "Own": 0.0,
                "JocRat": 2.0,
                "JAllow": 1.5,
                "Jockey_Horse_Wins": 0,
                "Prev_Jockey_Won": False,
                "GR_Pct": 50.0,
                "WT_Pct": 40.0,
                "Win_Pct": 16.0,
                "Dist_Win_Pct": 20.0,
                "Class_Rat": 49.0,
                "DLR": 14,
                "Prep_Run": 3,
                "Dist_10pct_Match": True,
                "Field_Strength_Diff": 0.0,
                "Tote_Odds": 8.00,
            },
            {
                "Scratched": False,
                "TAB": 5,
                "Horse": "LYMAN HALL",
                "BP": 5,
                "Weight": 54.5,
                "Prev_Weight": 55.5,
                "Ex_Pk": 52.0,
                "Base": 48.5,
                "Form": 1.5,
                "Cond": -1.0,
                "Cons": 0.0,
                "BP_Adj": 0.0,
                "Own": 0.0,
                "JocRat": 2.5,
                "JAllow": 0.0,
                "Jockey_Horse_Wins": 1,
                "Prev_Jockey_Won": True,
                "GR_Pct": 46.0,
                "WT_Pct": 52.0,
                "Win_Pct": 15.0,
                "Dist_Win_Pct": 22.0,
                "Class_Rat": 48.5,
                "DLR": 42,
                "Prep_Run": 1,
                "Dist_10pct_Match": False,
                "Field_Strength_Diff": -0.5,
                "Tote_Odds": 11.00,
            },
            {
                "Scratched": False,
                "TAB": 6,
                "Horse": "DANZARBER",
                "BP": 8,
                "Weight": 54.0,
                "Prev_Weight": 54.0,
                "Ex_Pk": 49.0,
                "Base": 48.0,
                "Form": 0.5,
                "Cond": 0.0,
                "Cons": -1.0,
                "BP_Adj": -0.5,
                "Own": 0.0,
                "JocRat": 2.0,
                "JAllow": 0.0,
                "Jockey_Horse_Wins": 0,
                "Prev_Jockey_Won": False,
                "GR_Pct": 41.0,
                "WT_Pct": 35.0,
                "Win_Pct": 12.0,
                "Dist_Win_Pct": 15.0,
                "Class_Rat": 47.5,
                "DLR": 28,
                "Prep_Run": 5,
                "Dist_10pct_Match": True,
                "Field_Strength_Diff": 1.5,
                "Tote_Odds": 15.00,
            },
            {
                "Scratched": False,
                "TAB": 7,
                "Horse": "ASHWORTH",
                "BP": 1,
                "Weight": 54.0,
                "Prev_Weight": 54.0,
                "Ex_Pk": 50.5,
                "Base": 46.5,
                "Form": -1.0,
                "Cond": 0.0,
                "Cons": -1.5,
                "BP_Adj": 1.0,
                "Own": 0.0,
                "JocRat": 3.0,
                "JAllow": 2.0,
                "Jockey_Horse_Wins": 0,
                "Prev_Jockey_Won": False,
                "GR_Pct": 33.0,
                "WT_Pct": 25.0,
                "Win_Pct": 10.0,
                "Dist_Win_Pct": 12.0,
                "Class_Rat": 46.0,
                "DLR": 14,
                "Prep_Run": 4,
                "Dist_10pct_Match": False,
                "Field_Strength_Diff": 2.0,
                "Tote_Odds": 26.00,
            },
            {
                "Scratched": False,
                "TAB": 8,
                "Horse": "MY SOUTHERN BELLE",
                "BP": 9,
                "Weight": 54.0,
                "Prev_Weight": 54.0,
                "Ex_Pk": 46.0,
                "Base": 44.0,
                "Form": -0.5,
                "Cond": -1.5,
                "Cons": -1.5,
                "BP_Adj": -1.0,
                "Own": 0.0,
                "JocRat": 3.5,
                "JAllow": 0.0,
                "Jockey_Horse_Wins": 0,
                "Prev_Jockey_Won": False,
                "GR_Pct": 28.0,
                "WT_Pct": 20.0,
                "Win_Pct": 8.0,
                "Dist_Win_Pct": 10.0,
                "Class_Rat": 44.5,
                "DLR": 70,
                "Prep_Run": 1,
                "Dist_10pct_Match": False,
                "Field_Strength_Diff": 2.5,
                "Tote_Odds": 51.00,
            },
        ]
    )


if "race_df" not in st.session_state:
    st.session_state["race_df"] = get_default_field()


# ==============================================================================
# SIDEBAR CONTROLS (PLE ENGINE + SUPERFORM PREFERENCES)
# ==============================================================================
st.sidebar.header("⚙️ Engine & Superform Settings")

venue_name = st.sidebar.text_input("Venue / Meeting", value="FLEMINGTON")
race_label = st.sidebar.text_input("Race Number & Name", value="R7 - Benchmark 84 Handicap")
race_dist = st.sidebar.number_input("Distance (m)", min_value=800, max_value=3600, value=1400, step=50)
track_cond = st.sidebar.selectbox("Track Condition", ["Good (Firm/Good)", "Soft (Slow)", "Heavy"], index=0)
limit_weight = st.sidebar.number_input("Limit Weight (kg)", min_value=50.0, max_value=58.0, value=54.0, step=0.5)

st.sidebar.markdown("---")
st.sidebar.subheader("📐 PLE Shrinkage & Price Framing")
mode = st.sidebar.selectbox(
    "Probability Engine Mode",
    ["PLE Shrinkage Blend", "Pure Model (Superform FR)", "Market Anchored (70% Market)"],
    index=0,
)
shrinkage_lambda = st.sidebar.slider("Market Shrinkage (λ)", min_value=0.0, max_value=1.0, value=0.35, step=0.05)
rating_temp = st.sidebar.slider("Rating Softmax Temp (kg)", min_value=0.8, max_value=5.0, value=2.2, step=0.1)
aggressive_odds = st.sidebar.checkbox("Use Aggressive Price Line (Tighten Tops)", value=False)
market_level_pct = st.sidebar.slider("Value Market Book (%)", min_value=75, max_value=100, value=85, step=1)
min_ev = st.sidebar.slider("Minimum Win EV Edge (%)", min_value=0.0, max_value=30.0, value=5.0, step=1.0)

st.sidebar.markdown("---")
st.sidebar.subheader("💰 Bankroll & Kelly Sizing")
bankroll = st.sidebar.number_input("Bankroll ($)", min_value=50.0, max_value=100000.0, value=1000.0, step=50.0)
kelly_mult = st.sidebar.slider("Fractional Kelly Multiplier", min_value=0.05, max_value=1.0, value=0.25, step=0.05)
hist_count = len(load_live_results())
st.sidebar.caption(f"Logged Live Races in Ledger: **{hist_count}**")


# ==============================================================================
# MAIN HEADER & TABS
# ==============================================================================
st.title("🐎 Nilovea Racing Command Centre | PLE & Trifecta Engine")
st.caption(
    f"**{venue_name}** • **{race_label}** • **{race_dist}m** • **{track_cond}** • Limit Weight: **{limit_weight:.1f} kg**"
)

tab_handicap, tab_models, tab_trifecta, tab_results = st.tabs(
    [
        "1️⃣ Handicap Card & Scratchings",
        "2️⃣ Dual Models (MOD1/MOD2) & Easy Rater",
        "3️⃣ Comparative Trifecta & Target Takeout",
        "4️⃣ Live Results & GitHub Sync",
    ]
)

# ==============================================================================
# TAB 1: HANDICAP CARD, SCRATCHING BARRIER SHIFTS & WIN VALUE
# ==============================================================================
with tab_handicap:
    col_upload, col_reset = st.columns([3, 1])
    with col_upload:
        uploaded_csv = st.file_uploader(
            "Optional: Upload Race Card CSV (columns matching editor below)", type=["csv"]
        )
        if uploaded_csv is not None:
            try:
                loaded_df = pd.read_csv(uploaded_csv)
                st.session_state["race_df"] = loaded_df
                st.success("Loaded race card CSV into session.")
            except Exception as exc:
                st.error(f"CSV load error: {exc}")
    with col_reset:
        st.write("")
        st.write("")
        if st.button("Reset Sample Field", use_container_width=True):
            st.session_state["race_df"] = get_default_field()
            st.rerun()

    st.subheader("Interactive Runner Inputs (Tick 'Scratched' to Auto-Shift Outer Barriers)")
    edited_df = st.data_editor(
        st.session_state["race_df"],
        num_rows="dynamic",
        use_container_width=True,
        key="runner_editor",
    )
    st.session_state["race_df"] = edited_df

    # Run Superform + PLE computation
    rated_df = compute_situational_ratings(
        df=edited_df,
        race_dist=race_dist,
        track_cond=track_cond,
        limit_weight=limit_weight,
        rating_temp=rating_temp,
        shrinkage_lambda=shrinkage_lambda,
        mode=mode,
        market_level_pct=market_level_pct,
        aggressive_odds=aggressive_odds,
    )

    if rated_df.empty:
        st.warning("All runners are scratched or field is empty.")
    else:
        # Compute Kelly Stakes
        rated_df["Kelly_Pct"] = [
            round(kelly_fraction(p, o, kelly_mult=kelly_mult) * 100.0, 2)
            if ev >= min_ev and o >= min_o
            else 0.0
            for p, o, ev, min_o in zip(
                rated_df["PLE_Prob"],
                rated_df["Tote_Odds"],
                rated_df["EV_Pct"],
                rated_df["Min_Accept_Odds"],
            )
        ]
        rated_df["Stake_$"] = (rated_df["Kelly_Pct"] / 100.0 * bankroll).round(2)

        overround_pct = rated_df.attrs.get("overround", 100.0)
        m1, m2, m3, m4 = st.columns(4)
        top_runner = rated_df.sort_values(by="FR", ascending=False).iloc[0]
        m1.metric("Top FR Contender", f"#{int(top_runner['TAB'])} {top_runner['Horse']}", f"FR {top_runner['FR']:.2f} kg")
        m2.metric("Live Market Overround", f"{overround_pct:.1f}%", f"Value Book: {market_level_pct}%")
        m3.metric("Value Runners Flagged", int((rated_df["Value_Flag"] == "✅ VALUE").sum()))
        m4.metric("Total Win Outlay", f"${rated_df['Stake_$'].sum():.2f}")

        st.subheader("Superform Final Rating (FR), Predicted Margins (1.5 kg = 1L) & Value Book")
        display_cols = [
            "TAB",
            "Horse",
            "BP",
            "Eff_BP",
            "Weight",
            "WOL",
            "Base",
            "Auto_Sit_kg",
            "FR",
            "Margin_Len",
            "Model_Pct",
            "Mkt_Fair_Pct",
            "PLE_Pct",
            "Fair_Odds",
            "Min_Accept_Odds",
            "Tote_Odds",
            "EV_Pct",
            "Value_Flag",
            "Stake_$",
        ]
        st.dataframe(
            rated_df[display_cols].sort_values(by="FR", ascending=False),
            use_container_width=True,
            hide_index=True,
        )


# ==============================================================================
# TAB 2: DUAL MODELS (MOD1 / MOD2) & RANK-CAPPED EASY RATER
# ==============================================================================
with tab_models:
    st.subheader("Easy Rater Formula Weightings & Max Rank Cutoff")
    st.caption(
        "Set any factor weight to `0.0` to exclude it for this venue, or cap ranks (e.g., Top 5) to suppress tail noise."
    )

    c_w1, c_w2, c_w3, c_w4 = st.columns(4)
    w_mod1 = c_w1.number_input("Weight: MOD1 (Career+Wgt)", 0.0, 5.0, 1.25, 0.25)
    w_mod2 = c_w2.number_input("Weight: MOD2 (Pure Weight)", 0.0, 5.0, 1.25, 0.25)
    w_imp = c_w3.number_input("Weight: Improvement", 0.0, 5.0, 1.00, 0.25)
    w_dist = c_w4.number_input("Weight: Distance ±10%", 0.0, 5.0, 1.15, 0.25)

    c_w5, c_w6, c_w7, c_w8 = st.columns(4)
    w_gr = c_w5.number_input("Weight: GR Consistency", 0.0, 5.0, 1.00, 0.25)
    w_expk = c_w6.number_input("Weight: Expected Peak", 0.0, 5.0, 0.90, 0.25)
    w_cls = c_w7.number_input("Weight: Class Rating", 0.0, 5.0, 1.00, 0.25)
    w_wet = c_w8.number_input(
        "Weight: Wet Track (WT)", 0.0, 5.0, 1.20 if track_cond != "Good (Firm/Good)" else 0.40, 0.25
    )

    max_rank_cap = st.slider("Max Rank Cutoff per Factor (Superform Rank Restriction)", 3, 24, 8, 1)

    custom_weights = {
        "MOD1": w_mod1,
        "MOD2": w_mod2,
        "Improve": w_imp,
        "Dist_10pct": w_dist,
        "Ability_GR": w_gr,
        "Ex_Pk": w_expk,
        "Class": w_cls,
        "Wet_WT": w_wet,
    }

    er_df = compute_situational_ratings(
        df=st.session_state["race_df"],
        race_dist=race_dist,
        track_cond=track_cond,
        limit_weight=limit_weight,
        rating_temp=rating_temp,
        shrinkage_lambda=shrinkage_lambda,
        mode=mode,
        market_level_pct=market_level_pct,
        aggressive_odds=aggressive_odds,
        factor_weights=custom_weights,
        max_rank_cap=max_rank_cap,
    )

    if not er_df.empty:
        er_cols = [
            "TAB",
            "Horse",
            "MOD1_Rank",
            "MOD2_Rank",
            "GR_Pct",
            "WT_Pct",
            "Ex_Pk",
            "Base",
            "FR",
            "Easy_Sum",
            "Easy_Rank",
            "Fair_Odds",
            "Tote_Odds",
        ]
        st.dataframe(
            er_df[er_cols].sort_values(by="Easy_Sum", ascending=True),
            use_container_width=True,
            hide_index=True,
        )


# ==============================================================================
# TAB 3: HARVILLE COMPARATIVE TRIFECTA & TARGET-TAKEOUT ENGINE
# ==============================================================================
with tab_trifecta:
    st.subheader("Comparative Trifecta Engine (Own Harville Odds vs. Tote Comparative Odds)")
    st.caption(
        "Retains only combinations where **Own Trifecta Odds ≤ Comparative Tote Odds** and sizes units inversely to hit your Target Takeout."
    )

    if rated_df.empty or len(rated_df) < 3:
        st.warning("At least 3 active runners are required for Trifecta & Exacta combinations.")
    else:
        t_c1, t_c2, t_c3, t_c4 = st.columns(4)
        target_takeout = t_c1.number_input("Target Takeout ($)", min_value=50.0, max_value=50000.0, value=1000.0, step=50.0)
        bet_unit_val = t_c2.number_input("Base Bet Unit ($)", min_value=0.5, max_value=50.0, value=1.0, step=0.5)
        min_tri_odds = t_c3.number_input("Min Trifecta Odds ($)", min_value=2.0, max_value=200.0, value=6.0, step=1.0)
        max_tri_odds = t_c4.number_input("Max Trifecta Odds ($)", min_value=50.0, max_value=5000.0, value=1000.0, step=50.0)

        require_value_tri = st.checkbox(
            "Strict Superform Value Filter (Require Own Trifecta Odds ≤ Tote Comparative Odds)", value=True
        )

        # Positional Standout Matrix (1st / 2nd / 3rd)
        st.markdown("**Positional Standout Matrix (Uncheck a box to exclude a runner from that placing):**")
        standout_init = pd.DataFrame(
            {
                "TAB": rated_df["TAB"].astype(int),
                "Horse": rated_df["Horse"],
                "PLE_Pct": rated_df["PLE_Pct"],
                "1st": rated_df["PLE_Pct"] >= 8.0,
                "2nd": rated_df["PLE_Pct"] >= 5.0,
                "3rd": True,
            }
        )
        standout_grid = st.data_editor(
            standout_init,
            use_container_width=True,
            hide_index=True,
            disabled=["TAB", "Horse", "PLE_Pct"],
            key="standout_matrix",
        )

        # Build Harville permutations
        n_active = len(rated_df)
        own_p_vec = rated_df["PLE_Prob"].to_numpy(dtype=float)
        comp_p_vec, _ = strip_field_vig(rated_df["Tote_Odds"].to_numpy(dtype=float))
        tabs_arr = rated_df["TAB"].astype(int).to_numpy()
        names_arr = rated_df["Horse"].to_numpy()

        allow_1st = set(standout_grid.loc[standout_grid["1st"] == True, "TAB"].astype(int))
        allow_2nd = set(standout_grid.loc[standout_grid["2nd"] == True, "TAB"].astype(int))
        allow_3rd = set(standout_grid.loc[standout_grid["3rd"] == True, "TAB"].astype(int))

        tri_rows = []
        for i, j, k in permutations(range(n_active), 3):
            t1, t2, t3 = int(tabs_arr[i]), int(tabs_arr[j]), int(tabs_arr[k])
            if not (t1 in allow_1st and t2 in allow_2nd and t3 in allow_3rd):
                continue

            p_own = harville_trifecta_prob(own_p_vec, i, j, k)
            p_comp = harville_trifecta_prob(comp_p_vec, i, j, k)
            if p_own <= 1e-8 or p_comp <= 1e-8:
                continue

            own_odds = 1.0 / p_own
            # Apply standard ~20% TAB trifecta takeout pool adjustment to comparative dividend estimate
            comp_div = (1.0 / p_comp) * 0.80

            if not (min_tri_odds <= own_odds <= max_tri_odds):
                continue
            if require_value_tri and own_odds > comp_div:
                continue

            units = max(1, int(round(target_takeout / max(comp_div * bet_unit_val, 1.0))))
            cost = round(units * bet_unit_val, 2)
            est_return = round(units * bet_unit_val * comp_div, 2)
            tri_ev_pct = round(((p_own * comp_div) - 1.0) * 100.0, 1)

            tri_rows.append(
                {
                    "1st": t1,
                    "2nd": t2,
                    "3rd": t3,
                    "Combo": f"{t1}-{t2}-{t3} ({names_arr[i]} / {names_arr[j]} / {names_arr[k]})",
                    "Own_Odds": round(own_odds, 1),
                    "Est_Tote_Div": round(comp_div, 1),
                    "Edge_%": tri_ev_pct,
                    "Units": units,
                    "Cost_$": cost,
                    "Est_Takeout_$": est_return,
                }
            )

        if not tri_rows:
            st.info(
                "No trifecta combinations passed your standout & value filters. Try widening 1st/2nd/3rd checkboxes or unchecking Strict Value."
            )
        else:
            tri_df = pd.DataFrame(tri_rows).sort_values(by="Edge_%", ascending=False).reset_index(drop=True)
            total_combos = len(tri_df)
            total_outlay = float(tri_df["Cost_$"].sum())
            avg_takeout = float(tri_df["Est_Takeout_$"].mean())

            k1, k2, k3 = st.columns(3)
            k1.metric("Qualifying Trifecta Tickets", total_combos)
            k2.metric("Total Ticket Outlay", f"${total_outlay:.2f}")
            k3.metric("Avg Est. Takeout / Hit", f"${avg_takeout:.2f}")

            st.dataframe(tri_df, use_container_width=True, hide_index=True)

            # Exacta Quick Summary
            with st.expander("View Top Harville Value Exactas"):
                ex_rows = []
                for i, j in permutations(range(n_active), 2):
                    t1, t2 = int(tabs_arr[i]), int(tabs_arr[j])
                    if not (t1 in allow_1st and t2 in allow_2nd):
                        continue
                    pe_own = harville_exacta_prob(own_p_vec, i, j)
                    pe_comp = harville_exacta_prob(comp_p_vec, i, j)
                    if pe_own > 1e-7 and pe_comp > 1e-7:
                        o_ex = 1.0 / pe_own
                        c_ex = (1.0 / pe_comp) * 0.85
                        if not require_value_tri or o_ex <= c_ex:
                            ex_rows.append(
                                {
                                    "Exacta": f"{t1}-{t2} ({names_arr[i]} / {names_arr[j]})",
                                    "Own_Exacta_Odds": round(o_ex, 1),
                                    "Est_Tote_Exacta": round(c_ex, 1),
                                    "Edge_%": round(((pe_own * c_ex) - 1.0) * 100.0, 1),
                                }
                            )
                if ex_rows:
                    st.dataframe(
                        pd.DataFrame(ex_rows).sort_values(by="Edge_%", ascending=False).head(15),
                        use_container_width=True,
                        hide_index=True,
                    )


# ==============================================================================
# TAB 4: LIVE RESULTS LEDGER & GITHUB REPO SYNC
# ==============================================================================
with tab_results:
    st.subheader("Log Race Outcome & Persist to GitHub (`racing_live_results.csv`)")
    ledger_df = load_live_results()

    with st.form("log_result_form"):
        r_c1, r_c2, r_c3 = st.columns(3)
        res_date = r_c1.date_input("Race Date", value=date.today())
        res_venue = r_c2.text_input("Venue", value=venue_name)
        res_race = r_c3.text_input("Race", value=race_label)

        r_c4, r_c5, r_c6 = st.columns(3)
        res_1st = r_c4.text_input("Actual 1st (TAB & Name)", value="")
        res_2nd = r_c5.text_input("Actual 2nd (TAB & Name)", value="")
        res_3rd = r_c6.text_input("Actual 3rd (TAB & Name)", value="")

        r_c7, r_c8, r_c9 = st.columns(3)
        res_bet_type = r_c7.selectbox("Bet Type", ["Win (PLE Value)", "Trifecta (Target Takeout)", "Exacta", "Paper Track"])
        res_outlay = r_c8.number_input("Total Outlay ($)", min_value=0.0, max_value=50000.0, value=0.0, step=5.0)
        res_return = r_c9.number_input("Total Return ($)", min_value=0.0, max_value=250000.0, value=0.0, step=5.0)
        res_notes = st.text_input("Post-Race Notes (Track bias, pace, stewards, etc.)", value="")

        submitted = st.form_submit_button("Save Result & Sync to GitHub")
        if submitted:
            top_fr_name = (
                rated_df.sort_values(by="FR", ascending=False).iloc[0]["Horse"] if not rated_df.empty else ""
            )
            new_row = pd.DataFrame(
                [
                    {
                        "Date": str(res_date),
                        "Venue": res_venue,
                        "Race": res_race,
                        "Distance_m": race_dist,
                        "Track": track_cond,
                        "Top_Pick": top_fr_name,
                        "Actual_1st": res_1st,
                        "Actual_2nd": res_2nd,
                        "Actual_3rd": res_3rd,
                        "Bet_Type": res_bet_type,
                        "Outlay": round(res_outlay, 2),
                        "Return": round(res_return, 2),
                        "Profit": round(res_return - res_outlay, 2),
                        "Notes": res_notes,
                    }
                ]
            )
            updated_ledger = pd.concat([ledger_df, new_row], ignore_index=True)
            csv_str = updated_ledger.to_csv(index=False)
            with open(LIVE_RESULTS_FILE, "w", encoding="utf-8") as f:
                f.write(csv_str)

            ok, msg = push_csv_to_github(
                LIVE_RESULTS_FILE,
                csv_str,
                f"Log racing result: {res_venue} {res_race} ({res_date})",
            )
            if ok:
                st.success(msg)
            else:
                st.warning(msg)
            ledger_df = updated_ledger

    if not ledger_df.empty:
        tot_out = pd.to_numeric(ledger_df["Outlay"], errors="coerce").fillna(0).sum()
        tot_ret = pd.to_numeric(ledger_df["Return"], errors="coerce").fillna(0).sum()
        net_pl = tot_ret - tot_out
        roi_pct = (net_pl / tot_out * 100.0) if tot_out > 0 else 0.0

        s1, s2, s3 = st.columns(3)
        s1.metric("Cumulative Outlay", f"${tot_out:.2f}")
        s2.metric("Net Profit / Loss", f"${net_pl:+.2f}")
        s3.metric("Cumulative ROI", f"{roi_pct:+.1f}%")

        st.dataframe(ledger_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download `racing_live_results.csv`",
            data=ledger_df.to_csv(index=False),
            file_name=LIVE_RESULTS_FILE,
            mime="text/csv",
        )
