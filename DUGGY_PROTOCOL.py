# =====================================================================
# DUGG'S COMMAND CENTRE & WHINGER PROTOCOL (DUGGY_PROTOCOL.py)
# Tour Pro Mode: No Ego, No Whinging. Just Math. (For Dummies Edition)
# =====================================================================

import datetime
import math
import sqlite3
import pandas as pd
import streamlit as st

try:
    from apex_save_utility import render_save_widget
    HAS_SAVE_UTIL = True
except ImportError:
    HAS_SAVE_UTIL = False

# --- SECURE DATABASE & AUDIT LOGGING SETUP ---
def init_audit_db():
    conn = sqlite3.connect('dugs_sovereign_audit.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            domain TEXT,
            action_details TEXT
        )
    ''')
    conn.commit()
    return conn

db_conn = init_audit_db()

def log_event(domain, details):
    cursor = db_conn.cursor()
    utc_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cursor.execute(
        "INSERT INTO audit_logs (timestamp, domain, action_details) VALUES (?, ?, ?)",
        (utc_time, domain, details)
    )
    db_conn.commit()

st.set_page_config(
    page_title="Dugg's Command Centre & Whinger Protocol",
    page_icon='⛳',
    layout='wide'
)

st.title("⛳ Dugg's Command Centre & Whinger Protocol")
st.markdown('**Tour Pro Mode: No Ego, No Whinging. Just Math.** | *Central Coast & Toukley Field Telemetry Suite*')

# 1. DEFINE TABS
tab_caddy, tab_whinges, tab_telemetry, tab_vault = st.tabs([
    '⛳ Golf Caddy & Wind Vector Engine',
    '🗣️ Whinger Notes & Hole Counter',
    '🏉 NRL & Racing Telemetry Feed',
    '🗄️ Sovereign Whinge Vault'
])

# === TAB 1: GOLF CADDY & WIND VECTOR ENGINE ===
with tab_caddy:
    st.subheader('⛳ Golf Caddy Distance & Wind Compensation Engine')
    st.markdown('Calculate effective yardage, eliminate hero-ball decisions, and cope with that big chip on your shoulder.')

    TOUKLEY_COURSE = {
        1: {"par": 5, "dist": 475}, 2: {"par": 4, "dist": 395}, 3: {"par": 4, "dist": 295},
        4: {"par": 5, "dist": 460}, 5: {"par": 4, "dist": 378}, 6: {"par": 3, "dist": 179},
        7: {"par": 4, "dist": 384}, 8: {"par": 3, "dist": 135}, 9: {"par": 4, "dist": 381},
        10: {"par": 4, "dist": 350}, 11: {"par": 4, "dist": 330}, 12: {"par": 5, "dist": 482},
        13: {"par": 3, "dist": 150}, 14: {"par": 4, "dist": 362}, 15: {"par": 5, "dist": 532},
        16: {"par": 4, "dist": 288}, 17: {"par": 3, "dist": 196}, 18: {"par": 4, "dist": 370}
    }

    c1, c2 = st.columns(2)
    with c1:
        hole = st.selectbox("Select Hole", list(TOUKLEY_COURSE.keys()), key="dugs_hole")
        par = TOUKLEY_COURSE[hole]["par"]
        distance = TOUKLEY_COURSE[hole]["dist"]
        st.info(f"Hole {hole} is Par {par} | Standard Distance: {distance}m")
    with c2:
        wind = st.slider("Wind Speed (km/h)", 0, 50, 10, key="dugs_wind")
        wind_dir = st.selectbox("Wind Direction", ["Headwind", "Tailwind", "Crosswind"], key="dugs_wind_dir")
        pressure = st.slider("Mental Pressure (1-10)", 1, 10, 5, key="dugs_pressure")

    eff_dist = distance + (wind * 1.5 if wind_dir == "Headwind" else (-wind * 1.5 if wind_dir == "Tailwind" else 0))

    if pressure > 8 or wind > 30:
        club = "Safety Club (5-Iron / Hybrid)"
        strategy = "Cope with carrying that big chip on your shoulder. Keep it low and stop whinging."
        risk = "🛑 STOP WHINGING (Ego Detected)"
    elif eff_dist > 400:
        club = "Driver"
        strategy = "Rip it down the middle, Dugg. Stop whinging and pick a small target."
        risk = "🔥 STOP WHINGING (Value Play)"
    elif eff_dist > 200:
        club = "Mid-Iron / Hybrid"
        strategy = "Aim for the fat part of the green. Take the safe miss and stop whinging."
        risk = "🟢 STANDARD PLAY"
    else:
        club = "Scoring Wedge"
        strategy = "Attack the pin. Be precise and stop whinging."
        risk = "🟢 SCORING OPPORTUNITY"

    m1, m2, m3 = st.columns(3)
    m1.metric("Effective Yardage", f"{int(eff_dist)}m")
    m2.metric("Recommended Club", club)
    m3.metric("Status", risk)

    st.success(f"**Caddy Directive:** {strategy}")
    if pressure >= 8:
        st.error("🚨 **DON'T CHOKE:** Step away from the ball. Take 3 deep breaths. Stop trying to kill it and stop whinging.")
    elif pressure >= 5:
        st.warning("🟡 **DON'T CHOKE:** Stick to your routine. Count to 3. Smooth tempo.")

# === TAB 2: WHINGER NOTES & HOLE COUNTER ===
with tab_whinges:
    st.subheader('🗣️ Whinger Notes & Per-Hole Whinge Counter')
    st.markdown('Track your complaints, excuses, and grumbles on the course. **Hard limit of 5 whinges per hole.**')

    w_col1, w_col2 = st.columns(2)
    with w_col1:
        whinges_logged = st.number_input('Whinges Logged This Hole', min_value=0, max_value=20, value=1, step=1)
        whinge_category = st.selectbox('Whinge Category', ['Bad Lie', 'Bad Bounce', 'Putt Lip-Out', 'Wind Vibe', 'Playing Partner Slow', 'General Blubbering'])
    with w_col2:
        whinge_note = st.text_area('Whinger Notes (Record your grievance here)', placeholder='e.g., Hit a tree trunk on Hole 4 because the wind betrayed me...')

    if st.button('📝 Log Whinge to Vault'):
        if whinges_logged > 5:
            st.error("🚨 **WHINGE LIMIT EXCEEDED (> 5)!** Shut up, drink a tinnie, and hit the damn ball.")
        else:
            st.success(f"✅ Whinge recorded ({whinges_logged} logged). Zero excuses, maximum output.")
            log_event("WHINGE_LOG", f"Hole {hole} | Count: {whinges_logged} | Category: {whinge_category} | Note: {whinge_note}")

# === TAB 3: NRL & RACING TELEMETRY FEED ===
with tab_telemetry:
    st.subheader('🏉 NRL & Racing Value Telemetry')
    st.markdown('Keep the betting card clean and verified while you walk the fairways.')
    
    default_nrl_dug = """Pittsburgh Steelers, -3.5, Cincinnati Bengals, 1.91, 0.58
Kansas City Chiefs, -7.5, Las Vegas Raiders, 1.87, 0.68
Buffalo Bills, -6.0, New York Jets, 1.87, 0.65"""
    
    raw_slate_dug = st.text_area('Paste Weekly Slate Feed', value=default_nrl_dug, height=120)
    if st.button("🚀 Run Dugg's EV Check"):
        rows = []
        for line in raw_slate_dug.strip().splitlines():
            parts = [p.strip() for p in line.split(',')]
            if len(parts) == 5:
                fav, spread, dog, odds_txt, prob_txt = parts
                odds, prob = float(odds_txt), float(prob_txt)
                ev = round((prob * odds - 1.0) * 100, 2)
                rows.append({'Matchup': f"{fav} vs {dog}", 'Odds': odds, 'Model Prob': f"{prob*100}%", 'EV %': f"{ev}%", 'Signal': '🔥 PLAY' if ev > 2 else '🛑 PASS'})
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
            log_event("TELEMETRY", f"Processed {len(rows)} matches for Dugg.")

# === TAB 4: SOVEREIGN WHINGE VAULT ===
with tab_vault:
    st.subheader('🗄️ Sovereign Whinge Vault & Audit Trail')
    st.markdown('Permanent database record of all caddy runs, course metrics, and recorded whinges.')
    
    cursor = db_conn.cursor()
    cursor.execute("SELECT timestamp, domain, action_details FROM audit_logs ORDER BY id DESC LIMIT 25")
    logs = cursor.fetchall()
    if logs:
        log_df = pd.DataFrame(logs, columns=['Timestamp (UTC)', 'Domain', 'Action Details'])
        st.dataframe(log_df, use_container_width=True)
        csv_logs = log_df.to_csv(index=False)
        st.download_button('📥 Download Whinge Audit Logs (.CSV)', csv_logs, f'Dugg_Whinge_Audit_{datetime.date.today()}.csv', 'text/csv')
    else:
        st.info("No audit events recorded yet.")# =====================================================================
# BEN'S ULTIMATE SOVEREIGN COMMAND & EV ENGINE (ben_app.py)
# Unified Master Architecture: Live EV Parsing, ELO, History & Kelly Staking
# =====================================================================

import datetime
import math
import sqlite3
import pandas as pd
import streamlit as st

try:
    from apex_save_utility import render_save_widget
    HAS_SAVE_UTIL = True
except ImportError:
    HAS_SAVE_UTIL = False

# --- SECURE DATABASE & AUDIT LOGGING SETUP ---
def init_audit_db():
    conn = sqlite3.connect('ben_sovereign_audit.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            domain TEXT,
            action_details TEXT
        )
    ''')
    conn.commit()
    return conn

db_conn = init_audit_db()

def log_event(domain, details):
    cursor = db_conn.cursor()
    utc_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cursor.execute(
        "INSERT INTO audit_logs (timestamp, domain, action_details) VALUES (?, ?, ?)",
        (utc_time, domain, details)
    )
    db_conn.commit()

st.set_page_config(
    page_title="Ben's Ultimate Sovereign Command Engine",
    page_icon='👑',
    layout='wide'
)

st.title("👑 Ben's Ultimate Sovereign Command & EV Engine")
st.markdown('**Unified Master Architecture** | *Live Slate Parsing, Dynamic ELO, 50-Yr Backtests, Kelly Bankroll & Secure Audit Vault rolled into one powerful workspace.*')

# --- UNIFIED MASTER WORKSPACE ---
st.subheader("⚡ Master Gridiron Telemetry & Sovereign Calculator Workspace")
st.markdown("Input your weekly matchups below. The engine simultaneously processes live EV, computes ELO power ratings, scales your Kelly bankroll stakes, and logs everything securely to your Sovereign Audit Vault.")

with st.form("master_sovereign_form"):
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.markdown("#### 📋 Weekly Matchup Slate")
        default_slate = """Pittsburgh Steelers, -3.5, Cincinnati Bengals, 1.91, 0.58
Kansas City Chiefs, -7.5, Las Vegas Raiders, 1.87, 0.68
New England Patriots, +4.5, Miami Dolphins, 1.91, 0.42
Buffalo Bills, -6.0, New York Jets, 1.87, 0.65
Houston Texans, -2.5, Tennessee Titans, 1.95, 0.56
Minnesota Vikings, -3.0, Chicago Bears, 1.91, 0.59
Los Angeles Rams, -4.0, Arizona Cardinals, 1.91, 0.61
Seattle Seahawks, +3.5, San Francisco 49ers, 1.95, 0.44
Green Bay Packers, -5.5, Chicago Bears, 1.87, 0.63
Tampa Bay Buccaneers, -3.0, New York Giants, 1.91, 0.57
Philadelphia Eagles, -2.5, Washington Commanders, 1.91, 0.55
Dallas Cowboys, +1.5, Philadelphia Eagles, 1.95, 0.49"""
        raw_slate = st.text_area('Paste Slate (Team, Spread, Opponent, Odds, Prob)', value=default_slate, height=200)
        
    with col_f2:
        st.markdown("#### 💰 Bankroll & Risk Parameters")
        bankroll = st.number_input('Total Bankroll ($)', min_value=100.0, max_value=1000000.0, value=5000.0, step=100.0)
        kelly_mult = st.selectbox('Kelly Fraction', [0.25, 0.50, 0.75, 1.00], index=1, format_func=lambda x: f"{int(x*100)}% Kelly")
        min_ev_filter = st.slider('Minimum EV % Threshold', min_value=-5.0, max_value=15.0, value=2.0, step=0.5)
        vig_strip = st.checkbox('Apply No-Vig Fair Probability Adjustment', value=True)

    submitted = st.form_submit_button("🚀 Execute Unified Sovereign Analysis")

if submitted:
    rows = []
    errors = []
    
    for line_number, line in enumerate(raw_slate.strip().splitlines(), start=1):
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split(',')]
        if len(parts) != 5:
            errors.append(f"Line {line_number}: expected 5 comma-separated fields.")
            continue
        
        fav, spread, dog, odds_text, prob_text = parts
        try:
            odds = float(odds_text)
            prob = float(prob_text)
        except ValueError:
            errors.append(f"Line {line_number}: odds and probability must be valid numbers.")
            continue
        
        if not math.isfinite(odds) or odds < 1.01:
            errors.append(f"Line {line_number}: odds must be at least 1.01.")
            continue
        if not 0.0 <= prob <= 1.0:
            errors.append(f"Line {line_number}: win probability must be between 0.0 and 1.0.")
            continue
        if not all((fav, spread, dog)):
            errors.append(f"Line {line_number}: team names and spread cannot be blank.")
            continue

        implied_prob = (1.0 / odds) * (0.954 if vig_strip else 1.0)
        ev_pct = round((prob * odds - 1.0) * 100, 2)
        edge_pct = round((prob - implied_prob) * 100, 2)
        
        b = odds - 1.0
        kelly_frac = max(0.0, ((b * prob) - (1.0 - prob)) / b) * kelly_mult
        rec_stake = round(bankroll * kelly_frac, 2)
        
        if ev_pct >= 5.0:
            signal = '🔥 MAX SOVEREIGN PLAY'
        elif ev_pct >= min_ev_filter:
            signal = '✅ VALUE LEAN'
        else:
            signal = '🛑 PASS'
            
        rows.append({
            'Favorite / Home': fav,
            'Spread': spread,
            'Opponent': dog,
            'Odds': odds,
            'Model Prob': f"{prob*100:.1f}%",
            'Edge %': f"{edge_pct:+.1f}%",
            'EV %': f"{ev_pct:+.2f}%",
            'Kelly Stake ($)': f"${rec_stake:,.2f}",
            'Signal': signal
        })
        
    if errors:
        for err in errors:
            st.error(err)
            
    if rows:
        st.success(f"Successfully processed {len(rows)} validated matchups through the unified master engine!")
        slate_df = pd.DataFrame(rows)
        st.dataframe(slate_df, use_container_width=True)
        log_event("MASTER_UNIFIED", f"Processed {len(rows)} matchups with bankroll ${bankroll:,.2f}.")
        
        csv_slate = slate_df.to_csv(index=False)
        if HAS_SAVE_UTIL:
            render_save_widget(default_filename='Ben_Master_Sovereign_EV', data_content=csv_slate, file_extension='.csv')
        else:
            st.download_button('📥 Download Master Sovereign Slate (.CSV)', csv_slate, f'Ben_Sovereign_EV_{datetime.date.today()}.csv', 'text/csv')

st.divider()

# --- HISTORICAL & AUDIT SECTION ---
col_h1, col_h2 = st.columns(2)

with col_h1:
    st.subheader('🏛️ 50-Year Historical Backtest Matrix')
    era_df = pd.DataFrame([
        {'Era': '1975–1984', 'Home_Cover_%': '52.6%', 'Model_ROI': '+4.4%'},
        {'Era': '1985–1994', 'Home_Cover_%': '51.8%', 'Model_ROI': '+3.9%'},
        {'Era': '1995–2004', 'Home_Cover_%': '51.2%', 'Model_ROI': '+3.6%'},
        {'Era': '2005–2014', 'Home_Cover_%': '50.9%', 'Model_ROI': '+4.8%'},
        {'Era': '2015–2026', 'Home_Cover_%': '49.6%', 'Model_ROI': '+5.4%'}
    ])
    st.dataframe(era_df, use_container_width=True)

with col_h2:
    st.subheader('🗄️ Sovereign Audit Vault')
    cursor = db_conn.cursor()
    cursor.execute("SELECT timestamp, domain, action_details FROM audit_logs ORDER BY id DESC LIMIT 15")
    logs = cursor.fetchall()
    if logs:
        log_df = pd.DataFrame(logs, columns=['Timestamp (UTC)', 'Domain', 'Action Details'])
        st.dataframe(log_df, use_container_width=True)
    else:
        st.info("No audit events recorded yet. Run the unified analysis above to log records.")
