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
            if "schedule_season" in df_h.columns:
                df_h["schedule_season"] = pd.to_numeric(df_h["schedule_season"], errors="coerce")
                df_h = df_h[df_h["schedule_season"] < 2025]
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
    master["score_home"] = pd.to_numeric(master["score_home"], errors="coerce")
    master["score_away"] = pd.to_numeric(master["score_away"], errors="coerce")
    if "schedule_season" in master.columns:
        master["schedule_season"] = pd.to_numeric(master["schedule_season"], errors="coerce")
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
                try:
                    tot = float(g.score_home) + float(g.score_away)
                    if tot > float(ou_line):
                        overs += 1
                    elif tot < float(ou_line):
                        unders += 1
                except ValueError:
                    pass

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
    elo_a = p2["elo"] if team_1_is_home else p1["elo"]
    off_h = p1["off_type"] if team_1_is_home else p2["off_type"]
    def_h = p1["def_type"] if team_1_is_home else p2["def_type"]
    off_a = p2["off_type"] if team_1_is_home else p1["off_type"]
    def_a = p2["def_type"] if team_1_is_home else p1["def_type"]

    pred_total = (
        34.7
        + 0.001934 * elo_h
        + 0.004540 * elo_a
        + (3.495672 if off_h == "strong" else (-1.387331 if off_h == "weak" else 0.0))
        + (-1.880359 if def_a == "strong" else (1.888973 if def_a == "weak" else 0.0))
        + (2.691029 if off_a == "strong" else (-1.176916 if off_a == "weak" else 0.0))
        + (-1.867485 if def_h == "strong" else (2.280479 if def_h == "weak" else 0.0))
    )
    if wind_mph > 12.0:
        pred_total -= (wind_mph - 12.0) * 0.25
    if temp_f < 36.0:
        pred_total -= 1.5
    if is_rain_snow:
        pred_total -= 1.5

    return p_win_1, 1.0 - p_win_1, fair_spread_1, round(pred_total, 1), div_game

# =====================================================================
# BOOT ENGINE FROM LOCKED REPO DATA
# =====================================================================
master_df = load_master_games()
profiles, ratings_df, d_latest = build_spreadspoke_engine(master_df)

st.sidebar.header("🦄 Locked Unicorn Engine")
if not master_df.empty:
    st.sidebar.success(f"🔒 LOCKED DB: {len(master_df):,} NFL games loaded (1966–Latest)")
else:
    st.sidebar.warning("⚠️ Upload `spreadspoke_scores-selected-columns.csv` & `nfl_2025.csv` to GitHub repo to lock permanently.")

mode = st.sidebar.radio(
    "Command Centre Mode",
    [
        "1. Week Ahead Slate Scanner (Spread + O/U + PLE)",
        "2. Full Matchup Lab (Weather, Rest, ML, Spread, O/U)",
        "3. Feed & Lock New Results / Weekly Data",
        "4. Power Rankings, ATS & Historical Log",
    ],
)

st.sidebar.divider()
shrinkage_lambda = st.sidebar.slider("PLE Shrinkage (λ)", 0.0, 1.0, 0.55, 0.05)
min_ev = st.sidebar.slider("Minimum EV Gate (%)", 1.0, 15.0, 5.0, 0.5) / 100.0
bankroll = st.sidebar.number_input("Bankroll ($)", min_value=50.0, value=1000.0, step=50.0)
kelly_mult = st.sidebar.selectbox("Kelly Fraction", [0.10, 0.25, 0.50, 1.00], index=0, format_func=lambda x: f"{int(x*100)}% Kelly")

# =====================================================================
# HEADER
# =====================================================================
st.title("🏈 Nebo Blokes NFL Command Centre")
st.caption("Locked 60-Year Historical Elo + Spreadspoke Rolling Offense/Defense Engine + Persistent Data Memory")

# =====================================================================
# MODE 1: WEEK AHEAD SLATE SCANNER (WITH QB / KEY INJURY ADJUSTMENTS)
# =====================================================================
if mode == "1. Week Ahead Slate Scanner (Spread + O/U + PLE)":
    st.subheader("⚡ Week Ahead Slate Scanner (`Team 1, Team 2, Spread, O/U, Injury_Adj_T1`)")
    st.caption(
        "Optional 5th column = **Net Injury Point Adjustment for Team 1** "
        "(e.g. `-5.5` if Team 1's starting QB is out; `+5.5` if Team 2's starting QB is out; `0` if healthy)."
    )

    c_up, c_home = st.columns([2, 1])
    with c_up:
        up_txt = st.file_uploader("Drop `todays nfl games.txt` or weekly slate `.csv`", type=["txt", "csv"])
    with c_home:
        team_1_is_home = st.radio(
            "Home Team Order",
            [True, False],
            format_func=lambda x: "Team 1 is Home" if x else "Team 1 is Away (Team 2 Home)",
        )

    default_slate = """Chargers, Ravens, 3.5, 45.5, 0.0
Patriots, Lions, -2.5, 48.5, 0.0
Chiefs, Falcons, -7.5, 47.5, 0.0
Texans, Browns, -1.5, 41.5, 0.0
Vikings, Packers, -2.5, 45.5, 0.0
Dolphins, Colts, 1.5, 45.5, 0.0
Panthers, Saints, -3.5, 43.5, 0.0
Bills, Jets, -1.5, 40.5, 0.0
Jaguars, Titans, -1.5, 39.5, 0.0
Rams, Cardinals, -7.5, 48.5, 0.0
Seahawks, Raiders, -2.5, 41.5, 0.0
49ers, Cowboys, -7.5, 47.5, 0.0
Steelers, Bengals, 2.5, 46.5, 0.0"""

    slate_text = up_txt.read().decode("utf-8") if up_txt is not None else st.text_area("Or paste week ahead games:", value=default_slate, height=210)

    if slate_text.strip():
        parsed_games = []
        for line in slate_text.strip().splitlines():
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 3:
                continue
            try:
                sp1 = float(parts[2])
            except ValueError:
                continue
            ou_line = float(parts[3]) if len(parts) >= 4 and parts[3] != "" else np.nan
            inj_adj = float(parts[4]) if len(parts) >= 5 and parts[4] != "" else 0.0
            parsed_games.append({
                "Team 1": parts[0],
                "Team 2": parts[1],
                "Spread (T1)": sp1,
                "O/U Line": ou_line,
                "T1 Injury Pts": inj_adj,
            })

        if parsed_games:
            st.markdown("#### 🏥 Interactive QB & Key Injury Override Table")
            st.caption("Edit **T1 Injury Pts** directly below (`-6.0` = T1 backup QB, `+6.0` = T2 backup QB) to recalculate live:")
            edited_slate = st.data_editor(
                pd.DataFrame(parsed_games),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Team 1": st.column_config.TextColumn(disabled=True),
                    "Team 2": st.column_config.TextColumn(disabled=True),
                    "Spread (T1)": st.column_config.NumberColumn(format="%.1f"),
                    "O/U Line": st.column_config.NumberColumn(format="%.1f"),
                    "T1 Injury Pts": st.column_config.NumberColumn(
                        min_value=-14.0,
                        max_value=14.0,
                        step=0.5,
                        format="%+.1f",
                        help="Negative = Team 1 hurt by injuries; Positive = Team 2 hurt by injuries",
                    ),
                },
            )

            rows = []
            for g in edited_slate.itertuples(index=False):
                raw_t1, raw_t2 = g[0], g[1]
                sp1 = float(g[2])
                ou_line = None if pd.isna(g[3]) else float(g[3])
                inj_adj_t1 = float(g[4]) if pd.notna(g[4]) else 0.0

                t1, t2 = norm_team(raw_t1), norm_team(raw_t2)
                _, _, base_fair_sp1, base_pred_tot, div_game = predict_game_spreadspoke(
                    t1, t2, profiles, team_1_is_home=team_1_is_home
                )

                # Apply QB / Key Injury adjustment (positive inj_adj_t1 makes T1 stronger / more negative spread)
                fair_sp1 = round(base_fair_sp1 - inj_adj_t1, 1)
                pred_tot = round(base_pred_tot - (0.35 * abs(inj_adj_t1)), 1)

                cover_margin_1 = (-fair_sp1) - (-sp1)
                p_raw_1 = spread_to_win_prob(-cover_margin_1)
                p_hat_1 = ple_calibrate_prob(0.50, p_raw_1, shrinkage_lambda)
                p_hat_2 = 1.0 - p_hat_1

                dec_line = 1.909
                ev_1, ev_2 = (p_hat_1 * dec_line) - 1.0, (p_hat_2 * dec_line) - 1.0
                best_ev = max(ev_1, ev_2)

                if ev_1 >= min_ev and ev_1 >= ev_2:
                    sig, pick, stk = "🔥 VALUE BET", f"{raw_t1} ({sp1:+.1f})", bankroll * kelly_fraction(p_hat_1, dec_line, kelly_mult)
                elif ev_2 >= min_ev and ev_2 > ev_1:
                    sig, pick, stk = "🔥 VALUE BET", f"{raw_t2} ({-sp1:+.1f})", bankroll * kelly_fraction(p_hat_2, dec_line, kelly_mult)
                else:
                    sig, pick, stk = "⚪ PASS", "—", 0.0

                ou_pick = "—"
                if ou_line is not None:
                    diff_ou = pred_tot - ou_line
                    if abs(diff_ou) >= 2.0:
                        ou_pick = f"{'OVER' if diff_ou > 0 else 'UNDER'} {ou_line} (Model: {pred_tot})"
                    else:
                        ou_pick = f"Lean {'Over' if diff_ou > 0 else 'Under'} ({pred_tot})"

                inj_badge = f" ({inj_adj_t1:+.1f} inj)" if inj_adj_t1 != 0 else ""
                rows.append({
                    "Matchup": f"{raw_t1} vs {raw_t2}" + (" 🏟️DIV" if div_game else ""),
                    "Spread Line": f"{raw_t1} {sp1:+.1f}",
                    "Model Fair": f"{raw_t1} {fair_sp1:+.1f}{inj_badge}",
                    "Signal": sig,
                    "Best Spread Pick": pick,
                    "PLE Cover %": round(max(p_hat_1, p_hat_2) * 100, 1),
                    "EV @ -110": round(best_ev * 100, 2),
                    "Kelly Stake": f"${stk:,.2f}",
                    "O/U Model Pick": ou_pick,
                })

            df_out = pd.DataFrame(rows).sort_values("EV @ -110", ascending=False).reset_index(drop=True)
            m1, m2, m3 = st.columns(3)
            m1.metric("Games Scanned", len(df_out))
            m2.metric("🔥 Value Spread Bets", int(df_out["Signal"].str.contains("VALUE").sum()))
            m3.metric("Top Spread EV", f"{df_out['EV @ -110'].max():+.2f}%")
            st.dataframe(df_out, use_container_width=True, hide_index=True)

# =====================================================================
# MODE 2: FULL MATCHUP LAB
# =====================================================================
elif mode == "2. Full Matchup Lab (Weather, Rest, ML, Spread, O/U)":
    st.subheader("🔬 Full Spreadspoke + PLE Matchup Simulator")
    teams_list = sorted(profiles.keys())

    c1, c2, c3 = st.columns(3)
    with c1:
        home_team = st.selectbox("Home Team", teams_list, index=teams_list.index("Seattle Seahawks") if "Seattle Seahawks" in teams_list else 0)
        odds_home = st.number_input(f"{home_team} ML Odds", value=-180.0, step=5.0)
        rest_h = st.selectbox(f"{home_team} Rest Status", ["Normal", "Bye Week", "Short Week"])
    with c2:
        away_team = st.selectbox("Away Team", teams_list, index=teams_list.index("New England Patriots") if "New England Patriots" in teams_list else 1)
        odds_away = st.number_input(f"{away_team} ML Odds", value=155.0, step=5.0)
        rest_a = st.selectbox(f"{away_team} Rest Status", ["Normal", "Bye Week", "Short Week"])
    with c3:
        book_ou = st.number_input("Sportsbook Over/Under Line", value=45.5, step=0.5)
        wind_mph = st.slider("Forecast Wind (mph)", 0, 35, 7)
        temp_f = st.slider("Forecast Temp (°F)", 0, 100, 62)
        c_chk1, c_chk2 = st.columns(2)
        neutral = c_chk1.checkbox("Neutral Site", value=False)
        rain_snow = c_chk2.checkbox("Rain / Snow", value=False)

    p_elo_h, p_elo_a, fair_sp, pred_tot, div_game = predict_game_spreadspoke(
        home_team, away_team, profiles, True, neutral, wind_mph, temp_f, rain_snow, rest_h, rest_a
    )
    dec_h, dec_a = american_to_decimal(odds_home), american_to_decimal(odds_away)
    p_mkt_h, p_mkt_a, vig_pct = strip_vig_two_way(dec_h, dec_a)
    p_hat_h = ple_calibrate_prob(p_mkt_h, p_elo_h, shrinkage_lambda)
    p_hat_a = 1.0 - p_hat_h
    ev_h, ev_a = (p_hat_h * dec_h) - 1.0, (p_hat_a * dec_a) - 1.0

    st.divider()
    if ev_h >= min_ev and ev_h >= ev_a:
        stk = bankroll * kelly_fraction(p_hat_h, dec_h, kelly_mult)
        st.success(f"### 🔥 VALUE ML BET: **{home_team}** @ `{dec_h:.2f}` | EV: **+{ev_h*100:.2f}%** | Kelly Stake: **${stk:,.2f}**")
    elif ev_a >= min_ev and ev_a > ev_h:
        stk = bankroll * kelly_fraction(p_hat_a, dec_a, kelly_mult)
        st.success(f"### 🔥 VALUE ML BET: **{away_team}** @ `{dec_a:.2f}` | EV: **+{ev_a*100:.2f}%** | Kelly Stake: **${stk:,.2f}**")
    else:
        st.info(f"### ⚪ PASS MONEYLINE — Best EV ({max(ev_h, ev_a)*100:+.2f}%) below {min_ev*100:.1f}% gate.")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Model Fair Spread", f"{home_team.split()[-1]} {fair_sp:+.1f}")
    m2.metric("Model Total vs Book", f"{pred_tot} pts", delta=f"{pred_tot - book_ou:+.1f} vs {book_ou}")
    m3.metric(f"{home_team.split()[-1]} PLE Win %", f"{p_hat_h*100:.1f}%", delta=f"Raw Model: {p_elo_h*100:.1f}%")
    m4.metric(f"{away_team.split()[-1]} PLE Win %", f"{p_hat_a*100:.1f}%", delta=f"Raw Model: {p_elo_a*100:.1f}%")

# =====================================================================
# MODE 3: FEED & LOCK NEW RESULTS / WEEKLY DATA (PERSISTENT STORAGE)
# =====================================================================
elif mode == "3. Feed & Lock New Results / Weekly Data":
    st.subheader("💾 Feed & Lock Completed Game Results Into Engine Memory")
    st.markdown(
        "Any completed games you enter or upload here are **immediately added to Elo & 16-game rolling stats** "
        "and committed permanently to `nfl_live_updates.csv` in your GitHub repository (when `GITHUB_TOKEN` is set in Secrets)."
    )

    tab_quick, tab_csv = st.tabs(["✍️ Quick Paste Completed Scores", "📂 Upload CSV Batch"])

    with tab_quick:
        st.markdown("Format: `Date (YYYY-MM-DD), Season, Week, Home Team, Home Score, Away Score, Away Team, Fav Team, Spread, O/U`")
        sample_new = f"{date.today()}, 2026, 1, Los Angeles Chargers, 24, 20, Baltimore Ravens, Ravens, -3.5, 45.5"
        new_lines = st.text_area("Paste completed results:", value=sample_new, height=130)

        if st.button("🔒 Lock Scores & Recalculate Engine", type="primary"):
            new_rows = []
            for line in new_lines.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) < 7:
                    continue
                new_rows.append({
                    "schedule_date": parts[0],
                    "schedule_season": int(parts[1]),
                    "schedule_week": parts[2],
                    "schedule_playoff": False,
                    "team_home": norm_team(parts[3]),
                    "score_home": float(parts[4]),
                    "score_away": float(parts[5]),
                    "team_away": norm_team(parts[6]),
                    "team_favorite_id": parts[7] if len(parts) >= 8 else "",
                    "spread_favorite": float(parts[8]) if len(parts) >= 9 else 0.0,
                    "over_under_line": float(parts[9]) if len(parts) >= 10 else np.nan,
                    "stadium_neutral": False,
                })

            if new_rows:
                df_added = pd.DataFrame(new_rows)
                existing_live = pd.read_csv(LIVE_LOG_FILE) if os.path.exists(LIVE_LOG_FILE) else pd.DataFrame()
                if "extra_games_df" in st.session_state:
                    existing_live = pd.concat([existing_live, st.session_state["extra_games_df"]], ignore_index=True)

                combined_live = pd.concat([existing_live, df_added], ignore_index=True).drop_duplicates(
                    subset=["schedule_date", "team_home", "team_away"], keep="last"
                )
                st.session_state["extra_games_df"] = combined_live
                combined_live.to_csv(LIVE_LOG_FILE, index=False)

                ok, msg = push_csv_to_github(
                    LIVE_LOG_FILE,
                    combined_live.to_csv(index=False),
                    f"Lock {len(df_added)} new NFL game result(s) into Unicorn Engine",
                )
                st.cache_data.clear()
                if ok:
                    st.success(f"✅ {msg}")
                else:
                    st.info(f"✅ Loaded into active engine! ({msg})")

                st.download_button(
                    "📥 Download Updated `nfl_live_updates.csv` Backup",
                    data=combined_live.to_csv(index=False).encode("utf-8"),
                    file_name=LIVE_LOG_FILE,
                    mime="text/csv",
                )

    with tab_csv:
        up_batch = st.file_uploader("Upload Completed Games CSV (Spreadspoke schema)", type=["csv"])
        if up_batch is not None:
            df_up = pd.read_csv(up_batch)
            if not REQUIRED_GAME_COLS.issubset(set(df_up.columns)):
                st.error(f"CSV must contain columns: {REQUIRED_GAME_COLS}")
            else:
                st.dataframe(df_up.head(10), use_container_width=True)
                if st.button("🔒 Merge & Lock CSV Into Database", type="primary"):
                    existing_live = pd.read_csv(LIVE_LOG_FILE) if os.path.exists(LIVE_LOG_FILE) else pd.DataFrame()
                    combined_live = pd.concat([existing_live, df_up], ignore_index=True).drop_duplicates(
                        subset=["schedule_date", "team_home", "team_away"], keep="last"
                    )
