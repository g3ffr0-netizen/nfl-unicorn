import os
import math
import pandas as pd
import streamlit as st
from google import genai
from google.genai.errors import APIError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

st.set_page_config(
    page_title="NRL Sovereign & Fair Engine",
    page_icon="🏉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- SECURE KEY FETCH ---
API_KEY = ""
try:
    API_KEY = str(st.secrets["GEMINI_API_KEY"]).strip()
except Exception:
    API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# ==========================================
# 1. NRL DATA & QUANT ENGINES
# ==========================================
DEFAULT_MATCHES = pd.DataFrame([
    {"Match": "Storm vs Panthers", "Home": "Storm", "Away": "Panthers", "Home_Odds": 1.85, "Away_Odds": 2.02, "Home_Exp_Pts": 21.5, "Away_Exp_Pts": 19.8, "Line_Home": -1.5, "Weather": "Dry / Calm"},
    {"Match": "Broncos vs Roosters", "Home": "Broncos", "Away": "Roosters", "Home_Odds": 1.72, "Away_Odds": 2.20, "Home_Exp_Pts": 24.2, "Away_Exp_Pts": 20.4, "Line_Home": -3.5, "Weather": "Dry / Calm"},
    {"Match": "Sharks vs Cowboys", "Home": "Sharks", "Away": "Cowboys", "Home_Odds": 1.64, "Away_Odds": 2.34, "Home_Exp_Pts": 25.0, "Away_Exp_Pts": 19.0, "Line_Home": -4.5, "Weather": "Light Wind"},
])

DEFAULT_PLAYERS = pd.DataFrame([
    {"Player": "Nathan Cleary", "Team": "Panthers", "Pos": "HFB", "Price": 945000, "Avg": 84.5, "Proj": 86.0, "BE": 78, "Base_Pts": 48.0, "Try_Share": 0.14, "ATS_Odds": 3.40, "Status": "Active", "Owned": True},
    {"Player": "Reece Walsh", "Team": "Broncos", "Pos": "FLB", "Price": 860000, "Avg": 78.4, "Proj": 84.0, "BE": 69, "Base_Pts": 28.0, "Try_Share": 0.22, "ATS_Odds": 2.15, "Status": "Active", "Owned": True},
    {"Player": "Tom Trbojevic", "Team": "Manly", "Pos": "FLB", "Price": 840000, "Avg": 76.0, "Proj": 79.0, "BE": 68, "Base_Pts": 31.0, "Try_Share": 0.20, "ATS_Odds": 2.30, "Status": "Active", "Owned": False},
    {"Player": "Harry Grant", "Team": "Storm", "Pos": "HOK", "Price": 875000, "Avg": 77.8, "Proj": 80.5, "BE": 70, "Base_Pts": 54.0, "Try_Share": 0.13, "ATS_Odds": 3.30, "Status": "Active", "Owned": True},
    {"Player": "Rookie Edge CashCow", "Team": "Storm", "Pos": "2RF", "Price": 245000, "Avg": 41.0, "Proj": 48.0, "BE": -12, "Base_Pts": 35.0, "Try_Share": 0.10, "ATS_Odds": 4.20, "Status": "Active", "Owned": True},
])

def safe_float(val, default: float = 0.0) -> float:
    num = pd.to_numeric(val, errors="coerce")
    if pd.isna(num) or math.isinf(float(num)):
        return default
    return float(num)

def poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0.0:
        return 1.0 if k == 0 else 0.0
    log_p = k * math.log(lam) - lam - math.lgamma(k + 1)
    return math.exp(log_p)

def simulate_match_poisson(home_pts: float, away_pts: float, max_tries: int = 12):
    h_pts = max(0.0, safe_float(home_pts, 18.0))
    a_pts = max(0.0, safe_float(away_pts, 18.0))
    lam_h = max(0.4, h_pts / 5.25)
    lam_a = max(0.4, a_pts / 5.25)

    p_home_win, p_away_win, p_draw = 0.0, 0.0, 0.0
    h_probs = [poisson_pmf(h, lam_h) for h in range(max_tries + 1)]
    a_probs = [poisson_pmf(a, lam_a) for a in range(max_tries + 1)]

    for h, ph in enumerate(h_probs):
        for a, pa in enumerate(a_probs):
            p = ph * pa
            if h > a:
                p_home_win += p
            elif a > h:
                p_away_win += p
            else:
                p_draw += p

    total_mass = p_home_win + p_away_win + p_draw
    if total_mass > 0:
        p_home_win /= total_mass
        p_away_win /= total_mass
        p_draw /= total_mass

    p_h = max(1e-4, min(0.9999, p_home_win + 0.5 * p_draw))
    p_a = max(1e-4, min(0.9999, p_away_win + 0.5 * p_draw))
    return lam_h, lam_a, p_h, p_a

def kelly_stake(prob: float, odds: float, bankroll: float, kelly_frac: float) -> float:
    if bankroll <= 0.0 or kelly_frac <= 0.0 or odds <= 1.0 or prob <= 0.0 or prob >= 1.0:
        return 0.0
    b = odds - 1.0
    full_k = (b * prob - (1.0 - prob)) / b
    if full_k <= 0.0:
        return 0.0
    return round(bankroll * full_k * kelly_frac, 2)

# ==========================================
# 2. FAIR ENGINE AI SCOUT (With Retry + Auto-Fallback)
# ==========================================
AVAILABLE_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-3.1-pro",
]

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=6),
    retry=retry_if_exception_type(APIError),
    reraise=True,
)
def _call_gemini(prompt: str, api_key: str, model_name: str) -> str:
    client = genai.Client(api_key=api_key, vertexai=False)
    response = client.models.generate_content(model=model_name, contents=prompt)
    return response.text or "No response text returned by model."

def run_ai_scout(prompt: str, api_key: str, model: str = "gemini-3.8-flash") -> str:
    if not api_key:
        return "⚠️ Running in Quant Mode. Add GEMINI_API_KEY to Streamlit Secrets to use the AI Scout."
    try:
        return _call_gemini(prompt, api_key, model)
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            for fallback in ["gemini-3.5-flash", "gemini-3.8-flash"]:
                if fallback != model:
                    try:
                        res = _call_gemini(prompt, api_key, fallback)
                        return f"*(Auto-switched from `{model}` to `{fallback}`)*\n\n{res}"
                    except Exception:
                        pass
            return f"🚨 **Model Not Found:** `{model}` returned 404. Switch to `gemini-3.5-flash` in the sidebar."
        elif "429" in error_msg:
            return "🚨 **Rate Limit Hit:** Too many requests right now. Wait a minute and try again."
        elif "401" in error_msg or "403" in error_msg:
            return "🚨 **Authentication Error:** Your API key is invalid or expired. Update `GEMINI_API_KEY` in Streamlit Secrets."
        else:
            return f"🚨 **API Error:** {error_msg}"

# ==========================================
# 3. UI LAYOUT
# ==========================================
st.markdown(
    """
    <style>
        .hero-bar { background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); color: #F8FAFC; border-left: 6px solid #10B981; border-radius: 12px; padding: 1rem 1.3rem; margin-bottom: 1rem; }
        .hero-title { font-size: 1.55rem; font-weight: 800; margin: 0; }
        .hero-sub { font-size: 0.9rem; color: #94A3B8; margin-top: 0.2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-bar">
        <div class="hero-title">🏉 NRL Sovereign & ⚖️ Fair Engine AI</div>
        <div class="hero-sub">Stress-Tested Poisson Match & Try EV · Fractional Kelly Staking · Late Mail Scout</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("⚙️ Settings")
    bankroll = st.number_input("Bankroll ($)", min_value=50.0, value=1000.0, step=50.0)
    kelly_pct = st.slider("Kelly Fraction (%)", min_value=5, max_value=50, value=10, step=5)
    min_ev_pct = st.slider("Min +EV Filter (%)", min_value=0.0, max_value=20.0, value=3.0, step=0.5)

    st.markdown("---")
    model_choice = st.selectbox("AI Model", AVAILABLE_MODELS, index=0)
    if not API_KEY:
        st.caption("ℹ️ Running in Quant Mode (no API key detected).")

kelly_frac = kelly_pct / 100.0

tab_ai, tab_punters, tab_data = st.tabs([
    "🤖 AI Scout (Fair Engine)",
    "💰 NRL Punters EV Engine",
    "📥 Live Data Editor",
])

# --- TAB 1: AI SCOUT ---
with tab_ai:
    st.subheader("Paste Late Mail or News Here")
    st.caption("The Fair Engine parses late mail and flags how to adjust match points, player projections, and SuperCoach trades.")

    news_text = st.text_area(
        "News Article / Late Mail:",
        height=200,
        placeholder="Example: Nathan Cleary is ruled out with a hamstring injury. Reece Walsh is a confirmed starter.",
    )

    if st.button("🔍 Analyze with AI", use_container_width=True, type="primary"):
        if not news_text.strip():
            st.warning("Please paste some text first.")
        else:
            with st.spinner("Fair Engine is reading..."):
                ai_prompt = (
                    "You are a professional NRL betting and SuperCoach analyst. "
                    "Read this late mail/news and give a sharp, practical breakdown of:\n"
                    "1) Match points / H2H line impact\n"
                    "2) Try-scorer / player projection shifts\n"
                    "3) SuperCoach captain / trade / cash-cow impact\n\n"
                    f"{news_text}"
                )
                response = run_ai_scout(ai_prompt, API_KEY, model_choice)
                if response.startswith("🚨") or response.startswith("⚠️"):
                    st.warning(response)
                else:
                    st.success("✅ Analysis Complete")
                    st.markdown(response)

# --- TAB 2: PUNTERS EV ENGINE ---
with tab_punters:
    matches_df = st.session_state.get("matches_df", DEFAULT_MATCHES.copy())
    players_df = st.session_state.get("players_df", DEFAULT_PLAYERS.copy())

    st.subheader("1. Match H2H & Poisson Fair Odds")
    match_rows = []
    team_try_rates = {}

    for _, m in matches_df.iterrows():
        h_odds = max(1.01, safe_float(m.get("Home_Odds"), 1.90))
        a_odds = max(1.01, safe_float(m.get("Away_Odds"), 1.90))
        h_pts = max(0.0, safe_float(m.get("Home_Exp_Pts"), 20.0))
        a_pts = max(0.0, safe_float(m.get("Away_Exp_Pts"), 20.0))

        lam_h, lam_a, p_h, p_a = simulate_match_poisson(h_pts, a_pts)
        home_team = str(m.get("Home", "Home"))
        away_team = str(m.get("Away", "Away"))
        team_try_rates[home_team] = lam_h
        team_try_rates[away_team] = lam_a

        ev_h = (p_h * h_odds - 1.0) * 100.0
        ev_a = (p_a * a_odds - 1.0) * 100.0

        stake_h = kelly_stake(p_h, h_odds, bankroll, kelly_frac) if ev_h >= min_ev_pct else 0.0
        stake_a = kelly_stake(p_a, a_odds, bankroll, kelly_frac) if ev_a >= min_ev_pct else 0.0

        signal = "PASS"
        if ev_h >= min_ev_pct and ev_h >= ev_a:
            signal = f"BET {home_team} (+{ev_h:.1f}% · ${stake_h:.2f})"
        elif ev_a >= min_ev_pct:
            signal = f"BET {away_team} (+{ev_a:.1f}% · ${stake_a:.2f})"

        match_rows.append({
            "Match": str(m.get("Match", f"{home_team} vs {away_team}")),
            "Fair Odds": f"{1/p_h:.2f} / {1/p_a:.2f}",
            "Book Odds": f"{h_odds:.2f} / {a_odds:.2f}",
            "EV % (H/A)": f"{ev_h:+.1f}% / {ev_a:+.1f}%",
            "Action": signal,
        })

    st.dataframe(pd.DataFrame(match_rows), use_container_width=True, hide_index=True)

    st.subheader("2. Try-Scorer Poisson Value & SuperCoach Watch")
    sc_rows = []
    for _, p in players_df.iterrows():
        status = str(p.get("Status", "Active"))
        if status.lower() != "active":
            continue
        team_name = str(p.get("Team", ""))
        team_lam = team_try_rates.get(team_name, 3.8)
        share = max(0.0, min(1.0, safe_float(p.get("Try_Share"), 0.12)))
        ats_odds = max(1.01, safe_float(p.get("ATS_Odds"), 3.00))
        proj = safe_float(p.get("Proj"), 50.0)
        be = safe_float(p.get("BE"), 45.0)

        p_lam = team_lam * share
        p_ats = max(1e-4, min(0.9999, 1.0 - math.exp(-p_lam)))
        fair_ats = 1.0 / p_ats
        ev_ats = (p_ats * ats_odds - 1.0) * 100.0
        stake_ats = kelly_stake(p_ats, ats_odds, bankroll, kelly_frac) if ev_ats >= min_ev_pct else 0.0

        owned = bool(p.get("Owned", False))
        sc_signal = ("Cash Out / Watch" if proj - be < -4 else "Hold") if owned else ("Buy / Cash Cow" if proj - be > 6 else "Pass")

        sc_rows.append({
            "Player": str(p.get("Player", "")),
            "Team": team_name,
            "Pos": str(p.get("Pos", "")),
            "ATS Prob %": round(p_ats * 100.0, 1),
            "Fair / Book ATS": f"${fair_ats:.2f} / ${ats_odds:.2f}",
            "Try EV %": round(ev_ats, 1),
            "Kelly ($)": stake_ats,
            "Proj / BE": f"{proj:.1f} / {be:.0f}",
            "SC Action": sc_signal,
        })

    if sc_rows:
        st.dataframe(pd.DataFrame(sc_rows).sort_values(by="Try EV %", ascending=False), use_container_width=True, hide_index=True)

# --- TAB 3: DATA EDITOR ---
with tab_data:
    st.subheader("Update Live Data")

    st.markdown("**Matches & Odds**")
    edited_matches = st.data_editor(
        st.session_state.get("matches_df", DEFAULT_MATCHES.copy()),
        use_container_width=True,
        num_rows="dynamic",
        key="ed_m",
    )
    st.session_state["matches_df"] = edited_matches

    st.markdown("**Players & SuperCoach Pool**")
    edited_players = st.data_editor(
        st.session_state.get("players_df", DEFAULT_PLAYERS.copy()),
        use_container_width=True,
        num_rows="dynamic",
        key="ed_p",
    )
    st.session_state["players_df"] = edited_players
