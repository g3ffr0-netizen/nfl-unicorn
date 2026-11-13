import os
import json
import time
import pandas as pd
import streamlit as st

st.set_page_config(page_title="ROZ Protocol", page_icon="🤖", layout="wide")

st.title("🤖 ROZ Protocol [Nilovea Exoskeleton Brain v1.6]")
st.markdown("### Biometric Telemetry, Behavioral Intercept & Hard Sovereign Override")

# --- SESSION STATE INITIALIZATION ---
if 'system_status' not in st.session_state: st.session_state.system_status = "NOMINAL"
if 'killswitch_active' not in st.session_state: st.session_state.killswitch_active = False
if 'killswitch_reason' not in st.session_state: st.session_state.killswitch_reason = ""
if 'history' not in st.session_state: st.session_state.history = []
if 'safe_reset' not in st.session_state: st.session_state.safe_reset = False

# --- TELEMETRY INPUTS (Sidebar) ---
st.sidebar.header("📡 Biometric & Environmental Telemetry")

if st.session_state.safe_reset:
    default_hr = 75
    default_cortisol = 3
    default_energy = 80
    default_noise = 50
    st.session_state.safe_reset = False 
else:
    default_hr = 75
    default_cortisol = 3
    default_energy = 80
    default_noise = 50

heart_rate = st.sidebar.slider("Heart Rate (BPM)", 40, 200, default_hr)
cortisol_level = st.sidebar.slider("Stress/Cortisol Level (1-10)", 1, 10, default_cortisol)
energy_mp = st.sidebar.slider("Estimated Energy MP", 0, 100, default_energy)
environmental_noise = st.sidebar.slider("Environmental Noise (dB)", 30, 120, default_noise)

# --- GLOBAL EMERGENCY KILLSWITCH ---
if st.sidebar.button("🛑 EMERGENCY KILLSWITCH"):
    st.session_state.killswitch_active = True
    st.session_state.killswitch_reason = "Manual Override Activated by Carer."

# --- AUTOMATIC FAIL-SAFE TRIGGER ---
if heart_rate > 160:
    st.session_state.killswitch_active = True
    st.session_state.killswitch_reason = f"CRITICAL HEART RATE: {heart_rate} BPM. Risk of cardiovascular event."
    st.session_state.history.append(f"AUTO-KILLSWITCH: Heart Rate {heart_rate} BPM.")
elif cortisol_level >= 9:
    st.session_state.killswitch_active = True
    st.session_state.killswitch_reason = f"CRITICAL CORTISOL LEVEL: {cortisol_level}/10. Risk of system meltdown."
    st.session_state.history.append(f"AUTO-KILLSWITCH: Cortisol Level {cortisol_level}/10.")

# --- THE KILLSWITCH UI ---
if st.session_state.killswitch_active:
    st.error("🚨🚨 **SYSTEM HALTED. PHYSICAL OVERRIDE ENGAGED.** 🚨🚨")
    st.markdown(f"### Reason for Override:\n**{st.session_state.killswitch_reason}**")
    st.markdown("**ACTION:** Exoskeleton joints locked into safe position. Background noise silenced. Step away and protect your peace.")
    
    if st.button("Acknowledge & Reset System"):
        st.session_state.killswitch_active = False
        st.session_state.system_status = "NOMINAL"
        st.session_state.killswitch_reason = ""
        st.session_state.safe_reset = True 
        st.warning("System reset. Telemetry returned to safe defaults.")
        st.rerun()
    st.stop()

# --- MAIN APP TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["🧠 Cognitive State", "🐾 Animal Instinct", "⚙️ System Logs", "🪞 Carer Shield"])

with tab1:
    st.header("Cognitive State Analysis & Burnout Guard")
    
    if st.button("Run Cognitive Assessment"):
        st.info("Analyzing biometric telemetry...")
        time.sleep(0.5)
        
        total_strain = cortisol_level + (environmental_noise / 20)
        
        if energy_mp < 30 and total_strain > 8:
            st.error("🚩 **BURNOUT TRAP DETECTED.** High stress, low energy, and sensory load. Roz recommends immediate rest.")
        elif environmental_noise > 85 and energy_mp < 60:
            st.warning("🟡 **SENSORY OVERLOAD RISK.** Environmental noise is high and your energy is draining. Seek quiet immediately.")
        elif energy_mp < 50:
            st.warning("🟡 **MODERATE STRAIN.** Low-focus tasks only. Take a mandatory break.")
        else:
            st.success("🟢 **FLOW STATE STABLE.** Biometrics nominal. Capacity available for complex execution.")

with tab2:
    st.header("🐾 Animal Instinct (Behavioral Decipher)")
    raw_input = st.text_area("Enter raw observation:", height=100)
    
    if st.button("Decipher Behavioral State"):
        if not raw_input.strip():
            st.warning("⚠️ Please enter observation data first.")
        else:
            text_lower = raw_input.lower()
            if "pacing" in text_lower or "repeating" in text_lower or "map" in text_lower:
                st.error("🚨 **HIGH-RISK DEVIATION DETECTED.** Immediate grounding required. Hand the physical map to the user. Do not argue.")
            elif "quiet" in text_lower or "still" in text_lower:
                st.success("🟢 **STATE: CALM.** Maintain current environmental baseline.")
            else:
                st.info("🟡 **STATE: ELEVATED.** Monitor closely. Reduce environmental stimuli.")

with tab3:
    st.header("⚙️ System Logs & Intervention Memory")
    with st.form("log_form"):
        log_entry = st.text_input("Log an event manually:")
        submitted = st.form_submit_button("Save to Log")
        if submitted and log_entry:
            st.session_state.history.append(log_entry)
            
    if st.session_state.history:
        for idx, entry in enumerate(st.session_state.history, 1):
            st.write(f"{idx}. {entry}")
        df_logs = pd.DataFrame({"Intervention Log": st.session_state.history})
        csv_data = df_logs.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Logs", data=csv_data, file_name="roz_logs.csv", mime="text/csv")

with tab4:
    st.header("🪞 Sonny's Carer Shield & Grounding")
    st.info("💡 **Core Truth:** No corporate battle, system error, or technical hurdle is worth your peace of mind.")
    if st.button("🛑 Activate Mental Killswitch"):
        st.warning("🔌 **Killswitch Activated:** Step away from the laptop. Take a mandatory break.")

st.sidebar.markdown("---")
st.sidebar.write("**System Status:** Sovereign Protection Active")
