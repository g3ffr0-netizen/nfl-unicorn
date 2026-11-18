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
        st.info("No audit events recorded yet.")
