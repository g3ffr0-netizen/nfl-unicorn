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
from datetime import date

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


def harville
