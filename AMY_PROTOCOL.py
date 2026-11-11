import streamlit as st
import time
import pandas as pd

st.set_page_config(page_title="Amy's Command Centre", page_icon="🧠", layout="wide")

# =====================================================================
# SECURE LOGIN PROTOCOL (Hardcoded for Amy)
# =====================================================================
# Note: In a real production app, use st.secrets. For this test, we hardcode.
AMY_USER = "amy"
AMY_PASS = "sovereign2026"

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Amy's Sovereign Command Centre")
    st.markdown("### Secure Access Required")
    
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Username")
    with col2:
        password = st.text_input("Password", type="password")
    
    if st.button("Log In"):
        if username == AMY_USER and password == AMY_PASS:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Access Denied. Invalid credentials.")
    st.stop() # Stops the app from loading until logged in

# =====================================================================
# MAIN APP (Only loads if authenticated)
# =====================================================================
st.title("🧠 Amy's Sovereign Command Centre")
st.markdown("### Dual-Carer Shield: Managing Bipolar & Parkinson's Care")

if st.sidebar.button("Log Out"):
    st.session_state.authenticated = False
    st.rerun()

# --- SIDEBAR: TELEMETRY ---
st.sidebar.header("📊 Personal Telemetry")
energy = st.sidebar.slider("My Energy Level (Spoons)", 0, 100, 50)
mood = st.sidebar.select_slider("My Mood State", options=["Depressed", "Low", "Stable", "Elevated", "Manic"], value="Stable")
stress = st.sidebar.slider("My Stress Level (1-10)", 1, 10, 3)

st.sidebar.markdown("---")
st.sidebar.header("🏥 Client Telemetry")
client_tremor = st.sidebar.slider("Client Tremor Severity (1-10)", 1, 10, 3)
client_mobility = st.sidebar.select_slider("Client Mobility", options=["Rigid", "Slow", "Stable", "Good"], value="Stable")

# --- MAIN TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["🧠 My Brain (Bipolar/ADHD)", "🏥 Client Care (Parkinson's)", "🛡️ Carer Killswitch", "⚙️ System Logs"])

with tab1:
    st.header("My Brain: The Cognitive Exoskeleton")
    st.markdown("Manage your own neurodivergence first. You cannot pour from an empty cup.")
    
    if mood == "Manic" or mood == "Elevated":
        st.warning("🚨 **MANIC/HYPOMANIC STATE DETECTED.** Your energy is artificially high. Do not make major financial or life decisions today. The engine recommends a grounding protocol.")
    elif mood == "Depressed" or energy < 30:
        st.error("🛑 **LOW ENERGY / DEPRESSIVE STATE.** Executive function is compromised. Cancel all non-essential tasks. Focus only on basic survival (food, water, rest).")
    else:
        st.success("🟢 **STABLE STATE.** Biometrics are nominal. You have the capacity for standard daily tasks.")
        
    if st.button("Open the Third Eye (60s Grounding)"):
        st.info("Starting 60-second reset. Close your eyes. Follow the pace.")
        progress_bar = st.progress(0)
        status_text = st.empty()
        for i in range(100):
            time.sleep(0.03)
            progress_bar.progress(i + 1)
            if i < 25: status_text.text("Breathe in... (4 seconds)")
            elif i < 50: status_text.text("Hold gently... (4 seconds)")
            elif i < 75: status_text.text("Breathe out slowly... (4 seconds)")
            else: status_text.text("Rest in the quiet... (4 seconds)")
        st.success("Clarity restored.")

with tab2:
    st.header("Client Care: Parkinson's Behavioral Decipher")
    st.markdown("Translate raw client observations into clinical data.")
    
    observation = st.text_area("Log Client Observation:", placeholder="e.g., 'Tremors worsening in left hand, shuffling gait, speech is very quiet today.'")
    
    if st.button("Run Decipher"):
        if not observation.strip():
            st.warning("Please enter an observation.")
        else:
            text_lower = observation.lower()
            if "tremor" in text_lower or "shuffling" in text_lower or "rigid" in text_lower:
                st.error("🚨 **MOTOR FLUCTUATION DETECTED.** Symptoms are worsening. Check medication schedule (is it time for the next dose?). Recommend gentle stretching and rest.")
            elif "quiet" in text_lower or "speech" in text_lower:
                st.warning("🟡 **HYPOPHONIA (Low Voice) DETECTED.** Encourage vocal exercises or use text-to-speech if communication is frustrating.")
            elif "fall" in text_lower or "dizzy" in text_lower:
                st.error("🚨 **FALL RISK HIGH.** Assist immediately. Check blood pressure (orthostatic hypotension is common).")
            else:
                st.success("🟢 **STATE: STABLE.** Continue monitoring.")
            
with tab3:
    st.header("The Carer Killswitch")
    st.markdown("Protect your own mental health. You are a professional, but you are also human.")
    
    if stress >= 8:
        st.error("🚨 **CARER OVERLOAD DETECTED.** Your stress is at critical levels. Tag out if possible. Step outside. You cannot provide safe care if you are in a state of panic or burnout.")
        
    st.info("💡 **The Rule:** It is not selfish to rest. It is a clinical necessity.")
    
    if st.button("Log Carer Reset"):
        st.success("Carer reset logged. Please take a 10-minute break.")

with tab4:
    st.header("System Logs")
    if "logs" not in st.session_state:
        st.session_state.logs = []
        
    with st.form("log_form"):
        log_entry = st.text_input("Add manual log:")
        if st.form_submit_button("Save") and log_entry:
            st.session_state.logs.append(log_entry)
            
    for idx, entry in enumerate(st.session_state.logs, 1):
        st.write(f"{idx}. {entry}")