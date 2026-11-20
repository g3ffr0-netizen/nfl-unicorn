import streamlit as st
import pandas as pd
import numpy as np
import math
import os
import base64
import json
import urllib.request
from datetime import date

st.set_page_config(
    page_title="Nebo Blokes NFL Command Centre | Locked Unicorn PLE Engine",
    page_icon="🏈",
    layout="wide",
)

# =====================================================================
# TEAM NICKNAMES, FRANCHISE HISTORY & DIVISIONS
# =====================================================================
SHORT_TO_FULL = {
    "Cardinals": "Arizona Cardinals", "Falcons": "Atlanta Falcons", "Ravens": "Baltimore Ravens",
    "Bills": "Buffalo Bills", "Panthers": "Carolina Panthers", "Bears": "Chicago Bears",
    "Bengals": "Cincinnati Bengals", "Browns": "Cleveland Browns", "Cowboys": "Dallas Cowboys",
    "Broncos": "Denver Broncos", "Lions": "Detroit Lions", "Packers": "Green Bay Packers",
    "Texans": "Houston Texans", "Colts": "Indianapolis Colts", "Jaguars": "Jacksonville Jaguars",
    "Chiefs": "Kansas City Chiefs", "Raiders": "Las Vegas Raiders", "Chargers": "Los Angeles Chargers",
    "Rams": "Los Angeles Rams", "Dolphins": "Miami Dolphins", "Vikings": "Minnesota Vikings",
    "Patriots": "New England Patriots", "Saints": "New Orleans Saints", "Giants": "New York Giants",
    "Jets": "New York Jets", "Eagles": "Philadelphia Eagles", "Steelers": "Pittsburgh Steelers",
    "49ers": "San Francisco 49ers", "Seahawks": "Seattle Seahawks", "Buccaneers": "Tampa Bay Buccaneers",
    "Titans": "Tennessee Titans", "Commanders": "Washington Commanders",
}

FRANCHISE_MAP = {
    "Baltimore Colts": "Indianapolis Colts",
    "Boston Patriots": "New England Patriots",
    "Houston Oilers": "Tennessee Titans",
    "Tennessee Oilers": "Tennessee Titans",
    "Los Angeles Raiders": "Las Vegas Raiders",
    "Oakland Raiders": "Las Vegas Raiders",
    "Phoenix Cardinals": "Arizona Cardinals",
    "St. Louis Cardinals": "Arizona Cardinals",
    "San Diego Chargers": "Los Angeles Chargers",
    "St. Louis Rams": "Los Angeles Rams",
    "Washington Redskins": "Washington Commanders",
    "Washington Football Team": "Washington Commanders",
}

TEAM_ID_TO_NAME = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LAC": "Los Angeles Chargers", "LAR": "Los Angeles Rams",
    "LVR": "Las Vegas Raiders", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
    "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks", "SF": "San Francisco 49ers", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}

TEAM_DIVISIONS = {
    "Buffalo Bills": "AFC East", "Miami Dolphins": "AFC East", "New England Patriots": "AFC East", "New York Jets": "AFC East",
    "Baltimore Ravens": "AFC North", "Cincinnati Bengals": "AFC North", "Cleveland Browns": "AFC North", "Pittsburgh Steelers": "AFC North",
    "Houston Texans": "AFC South", "Indianapolis Colts": "AFC South", "Jacksonville Jaguars": "AFC South", "Tennessee Titans": "AFC South",
    "Denver Broncos": "AFC West", "Kansas City Chiefs": "AFC West", "Las Vegas Raiders": "AFC West", "Los Angeles Chargers": "AFC West",
    "Dallas Cowboys": "NFC East", "New York Giants": "NFC East", "Philadelphia Eagles": "NFC East", "Washington Commanders": "NFC East",
    "Chicago Bears": "NFC North", "Detroit Lions": "NFC North", "Green Bay Packers": "NFC North", "Minnesota Vikings": "NFC North",
    "Atlanta Falcons": "NFC South", "Carolina Panthers": "NFC South", "New Orleans Saints": "NFC South", "Tampa Bay Buccaneers": "NFC South",
    "Arizona Cardinals": "NFC West", "Los Angeles Rams": "NFC West", "San Francisco 49ers": "NFC West", "Seattle Seahawks": "NFC West",
}

HIST_FILE = "spreadspoke_scores-selected-columns.csv"
RECENT_FILE = "nfl_2025.csv"
LIVE_LOG_FILE = "nfl_live_updates.csv"
REQUIRED_GAME_COLS = {"team_home", "team_away", "score_home", "score_away"}

def norm_team(name: str) -> str:
    s = str(name).strip()
    s = SHORT_TO_FULL.get(s, s)
    return FRANCHISE_MAP.get(s, s)

# =====================================================================
# GITHUB PERSISTENT STORAGE HELPER (LOCKS NEW DATA INTO REPO)
# =====================================================================
def push_csv_to_github(file_path: str, csv_content: str, commit_msg: str):
    """Commits an updated CSV straight back into GitHub so data persists permanently across reboots."""
    token = st.secrets.get("GITHUB_TOKEN", None) if hasattr(st, "secrets") else None
    repo = st.secrets.get("GITHUB_REPO", "g3ffr0-netizen/nfl-unicorn") if hasattr(st, "secrets") else "g3ffr0-netizen/nfl-unicorn"
    if not token:
        return False, "No `GITHUB_TOKEN` found in Streamlit Secrets (saved locally to session & downloadable below)."

    api_url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "Unicorn-NFL-Engine",
    }

    sha = None
    try:
        req_get = urllib.request.Request(api_url, headers=headers, method="GET")
        with urllib.request.urlopen(req_get) as resp:
            existing = json.loads(resp.read().decode("utf-8"))
            sha = existing.get("sha")
    except Exception:
        sha = None  # File does not exist yet on GitHub

    payload = {
        "message": commit_msg,
        "content": base64.b64encode(csv_content.encode("utf-8")).decode("utf-8"),
    }
    if sha:
        payload["sha"] = sha

    try:
        req_put = urllib.request.Request(api_url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="PUT")
        with urllib.request.urlopen(req_put) as resp:
            if resp.status in (200, 201):
                return True, f"Locked permanently into `{repo}/{file_path}` on GitHub!"
            return False, f"GitHub API returned status {resp.status}"
    except Exception as e:
        return False, f"GitHub sync error: {e}"

# =====================================================================
# QUANTITATIVE MATH: ODDS, SPREAD->PROB, PLE SHRINKAGE, KELLY
# =====================================================================
def american_to_decimal(odds: float) -> float:
    if 1.0 < odds < 100.0:
        return float(odds)
    if odds >= 100.0:
        return 1.0 + (odds / 100.0)
    if odds <= -100.0:
        return 1.0 + (100.0 / abs(odds))
    return 1.909

def spread_to_win_prob(spread: float, std_dev: float = 13.45) -> float:
    z = -spread / std_dev
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

def strip_vig_two_way(dec_a: float, dec_b: float):
    imp_a = 1.0 / dec_a
    imp_b = 1.0 / dec_b
    overround = imp_a + imp_b
    vig_pct = (overround - 1.0) * 100.0
    return imp_a / overround, imp_b / overround, vig_pct

def ple_calibrate_prob(p_market: float, p_raw_model: float, shrinkage_lambda: float) -> float:
    p_hat = p_market + shrinkage_lambda * (p_raw_model - p_market)
    return float(np.clip(p_hat, 0.005, 0.995))

def kelly_fraction(p_hat: float, dec_odds: float, kelly_mult: float = 0.25) -> float:
    b = dec_odds - 1.0
    if b <= 0:
        return 0.0
    full_kelly = ((b * p_hat) - (1.0 - p_hat)) / b
    return max(0.0, full_kelly * kelly_mult)

# =====================================================================
# MASTER DATABASE LOADER & SPREADSPOKE ELO ENGINE
# =====================================================================
def load_master_games():
    frames = []
    if os.path.exists(HIST_FILE):
        df_h = pd.read_csv(HIST_FILE)
        if REQUIRED_GAME_COLS.issubset(set(df_h.columns)):
            df_h = df_h[df_h["schedule_season"] < 2025] if "schedule_season" in df_h.columns else df_h
            frames.append(df_h)

    if os.path.exists(RECENT_FILE):
        df_25 = pd.read_csv(RECENT_FILE)
        if REQUIRED_GAME_COLS.issubset(set(df_25.columns)):
            frames.append(df_25)
    elif os.path.exists("spreadspoke_scores.csv"):
        df_sp = pd.read_csv("spreadspoke_scores.csv")
        if REQUIRED_GAME_COLS.issubset(set(df_sp.columns)):
            frames.append(df_sp)

    if os.path.exists(LIVE_LOG_FILE):
        df_live = pd.read_csv(LIVE_LOG_FILE)
        if REQUIRED_GAME_COLS.issubset(set(df_live.columns)):
            frames.append(df_live)

    if "extra_games_df" in st.session_state and not st.session_state["extra_games_df"].empty:
        frames.append(st.session_state["extra_games_df"])

    if not frames:
        return pd.DataFrame()
    master = pd.concat(frames, ignore_index=True)
    master = master.dropna(subset=["team_home", "team_away", "score_home", "score_away"]).copy()
    master["home_norm"] = master["team_home"].apply(norm_team)
    master["away_norm"] = master["team_away"].apply(norm_team)
    if "schedule_date" in master.columns:
        master = master.drop_duplicates(subset=["schedule_date", "home_norm", "away_norm"], keep="last")
    return master

@st.cache_data
def build_spreadspoke_engine(master_df: pd.DataFrame):
    if master_df.empty:
        default_teams = sorted(TEAM_ID_TO_NAME.values())
        profiles = {t: {"elo": 1500.0, "off_ppg_16": 21.0, "def_ppg_16": 21.0, "off_type": "neutral", "def_type": "neutral"} for t in default_teams}
        ratings_df = pd.DataFrame([{"Team": t, "Elo Rating": 1500.0} for t in default_teams])
        return profiles, ratings_df, pd.DataFrame()

    teams = sorted(set(master_df["home_norm"]).union(set(master_df["away_norm"])))
    elos = {t: 1500.0 for t in teams}
    team_history = {t: [] for t in teams}
    last_season = None

    for row in master_df.itertuples(index=False):
        season = int(row.schedule_season) if hasattr(row, "schedule_season") and pd.notna(row.schedule_season) else 2026
        if last_season is not None and season != last_season:
            for t in elos:
                elos[t] = 1500.0 + (elos[t] - 1500.0) * 0.67
        last_season = season

        h, a = row.home_norm, row.away_norm
        sh, sa = float(row.score_home), float(row.score_away)
        neutral = bool(getattr(row, "stadium_neutral", False)) if pd.notna(getattr(row, "stadium_neutral", False)) else False
        hfa = 0.0 if neutral else 55.0

        elo_diff = (elos[h] + hfa) - elos[a]
        exp_h = 1.0 / (1.0 + 10.0 ** (-elo_diff / 400.0))
        actual_h = 1.0 if sh > sa else (0.0 if sh < sa else 0.5)
        margin = abs(sh - sa)
        mov_mult = math.log(max(margin, 1.0) + 1.0) * (2.2 / ((abs(elo_diff) * 0.001) + 2.2))
        delta = (20.0 * mov_mult) * (actual_h - exp_h)
        elos[h] += delta
        elos[a] -= delta

        team_history[h].append((season, sh, sa))
        team_history[a].append((season, sa, sh))

    team_profiles = {}
    for t in teams:
        recent_16 = team_history[t][-16:] if len(team_history[t]) >= 16 else team_history[t]
        off_ppg = float(np.mean([g[1] for g in recent_16])) if recent_16 else 21.0
        def_ppg = float(np.mean([g[2] for g in recent_16])) if recent_16 else 21.0
        off_type = "strong" if off_ppg > 24.0 else ("weak" if off_ppg < 18.0 else "neutral")
        def_type = "strong" if def_ppg < 18.0 else ("weak" if def_ppg > 24.0 else "neutral")
        team_profiles[t] = {
            "elo": elos[t],
            "off_ppg_16": round(off_ppg, 1),
            "def_ppg_16": round(def_ppg, 1),
            "off_type": off_type,
            "def_type": def_type,
        }

    latest_season = master_df["schedule_season"].max() if "schedule_season" in master_df.columns else 2025
    d_latest = master_df[master_df["schedule_season"] == latest_season].copy() if "schedule_season" in master_df.columns else master_df.tail(285).copy()

    stats_rows = []
    for t in teams:
        h_g = d_latest[d_latest["home_norm"] == t]
        a_g = d_latest[d_latest["away_norm"] == t]
        gp = len(h_g) + len(a_g)
        wins = (h_g["score_home"] > h_g["score_away"]).sum() + (a_g["score_away"] > a_g["score_home"]).sum()

        ats_w, ats_l, overs, unders = 0, 0, 0, 0
        for g in pd.concat([h_g, a_g]).itertuples(index=False):
            fav_raw = str(getattr(g, "team_favorite_id", "")).strip()
            fav_name = TEAM_ID_TO_NAME.get(fav_raw, norm_team(fav_raw))
            sp = float(getattr(g, "spread_favorite", 0.0)) if pd.notna(getattr(g, "spread_favorite", np.nan)) else 0.0
            margin_h = float(g.score_home) - float(g.score_away)
            cover_h = (margin_h + sp) if fav_name == g.home_norm else ((margin_h - sp) if fav_name == g.away_norm else margin_h)
            team_cover = cover_h if g.home_norm == t else -cover_h
            if team_cover > 0:
                ats_w += 1
            elif team_cover < 0:
                ats_l += 1

            ou_line = getattr(g, "over_under_line", np.nan)
            if pd.notna(ou_line):
                tot = float(g.score_home) + float(g.score_away)
                if tot > float(ou_line):
                    overs += 1
                elif tot < float(ou_line):
                    unders += 1

        prof = team_profiles[t]
        stats_rows.append({
            "Team": t,
            "Division": TEAM_DIVISIONS.get(t, ""),
            "Elo Rating": round(prof["elo"], 1),
            f"{int(latest_season)} W-L": f"{int(wins)}-{int(gp - wins)}",
            f"{int(latest_season)} ATS": f"{ats_w}-{ats_l}",
            f"{int(latest_season)} O/U": f"{overs}-{unders}",
            "L16 Off PPG": prof["off_ppg_16"],
            "L16 Def PPG": prof["def_ppg_16"],
            "Off / Def Tier": f"{prof['off_type'].title()} / {prof['def_type'].title()}",
        })

    ratings_df = pd.DataFrame(stats_rows).sort_values("Elo Rating", ascending=False).reset_index(drop=True)
    ratings_df.index += 1
    return team_profiles, ratings_df, d_latest

def predict_game_spreadspoke(
    team_1: str, team_2: str, profiles: dict, team_1_is_home: bool = True,
    neutral_site: bool = False, wind_mph: float = 0.0, temp_f: float = 65.0,
    is_rain_snow: bool = False, rest_1: str = "Normal", rest_2: str = "Normal",
):
    p1 = profiles.get(team_1, {"elo": 1500.0, "off_ppg_16": 21.0, "def_ppg_16": 21.0, "off_type": "neutral", "def_type": "neutral"})
    p2 = profiles.get(team_2, {"elo": 1500.0, "off_ppg_16": 21.0, "def_ppg_16": 21.0, "off_type": "neutral", "def_type": "neutral"})

    div_game = (TEAM_DIVISIONS.get(team_1) == TEAM_DIVISIONS.get(team_2)) and (TEAM_DIVISIONS.get(team_1) is not None)
    hfa_1 = 0.0 if neutral_site else (55.0 if team_1_is_home else -55.0)
    rest_adj = (20.0 if rest_1 == "Bye Week" else (-15.0 if rest_1 == "Short Week" else 0.0)) - (
        20.0 if rest_2 == "Bye Week" else (-15.0 if rest_2 == "Short Week" else 0.0)
    )
    wind_damp = max(0.85, 1.0 - max(0.0, wind_mph - 12.0) * 0.01)
    div_damp = 0.94 if div_game else 1.0

    elo_diff = ((p1["elo"] + hfa_1 + rest_adj) - p2["elo"]) * wind_damp * div_damp
    p_win_1 = 1.0 / (1.0 + 10.0 ** (-elo_diff / 400.0))
    fair_spread_1 = -round(elo_diff / 25.0, 1)

    elo_h = p1["elo"] if team_1_is_home else p2["elo"]
