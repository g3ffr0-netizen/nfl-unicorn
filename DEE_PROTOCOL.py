import streamlit as st
import time
import pandas as pd

st.set_page_config(page_title="Dee Protocol [Sovereign Edition v1.6]", page_icon="🎗️", layout="wide")

st.title("🎗️ Dee Protocol [Sovereign Patient Advocate v1.6]")
st.markdown("### Decode the medical noise. Protect your peace. Fight the system together.")

# --- SESSION STATE INITIALIZATION ---
if 'history' not in st.session_state: st.session_state.history = []
if 'carer_lockdown' not in st.session_state: st.session_state.carer_lockdown = False
if 'carer_override' not in st.session_state: st.session_state.carer_override = False

# --- SIDEBAR: BIO-METRIC & ENERGY TELEMETRY ---
st.sidebar.header("📊 Patient & Carer Telemetry")
st.sidebar.write("Track the invisible load of treatment.")

energy = st.sidebar.slider("Patient Energy Level (Spoons)", 0, 100, 50)
pain = st.sidebar.slider("Patient Pain Level (1-10)", 1, 10, 3)
brain_fog = st.sidebar.slider("Patient Brain Fog Level (1-10)", 1, 10, 5)

st.sidebar.markdown("---")
carer_stress = st.sidebar.slider("Carer Stress Level (1-10)", 1, 10, 3)

# Carer Overload Protection (Infinite Loop Proof)
if carer_stress >= 9 and not st.session_state.carer_override:
    st.session_state.carer_lockdown = True

if st.session_state.carer_lockdown:
    st.sidebar.error("🚨 **CARER OVERLOAD DETECTED.**")
    if st.sidebar.button("Acknowledge & Clear Carer Alert"):
        st.session_state.carer_lockdown = False
        st.session_state.carer_override = True 
        st.rerun()
        
if carer_stress < 8:
    st.session_state.carer_override = False

# --- SIDEBAR: EMERGENCY THRESHOLD & QUICK-CARD ---
st.sidebar.markdown("---")
st.sidebar.header("🚨 Emergency Hospital Triggers")
st.sidebar.markdown("- **Temperature:** > 38.0°C (Fever + Low Blood Counts = Immediate ER)\n- **Bleeding:** Unstopped nosebleed or bruising\n- **Breathing:** Sudden shortness of breath")

st.sidebar.markdown("---")
st.sidebar.header("📇 Emergency Quick-Card")
st.sidebar.info("**Oncologist/Hospital:** [Insert Number]\n**Triage Hotline:** [Insert Number]\n**Pharmacy:** [Insert Number]")

# --- COGNITIVE VETO BANNER ---
if energy < 30 or brain_fog >= 8:
    st.error("🛑 **COGNITIVE VETO ACTIVE:** Patient energy is critically low or brain fog is high. **DO NOT MAKE MAJOR MEDICAL DECISIONS TODAY.** Ask the medical team for a 24-hour deferment to consult family.")

# --- MAIN TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["🩺 Medical Translator", "🛡️ The Shield (For Husband)", "🧘 Grounding (For Dee)", "⚙️ Treatment Logs"])

with tab1:
    st.header("🩺 The Medical Translator (Stripping the Jargon)")
    st.markdown("Paste confusing medical notes, blood test results, or doctor emails here. The engine translates them into plain English and hard questions.")
    
    medical_text = st.text_area("Paste Medical Jargon:", height=150, placeholder="e.g., 'Patient presents with elevated bilirubin and signs of aplastic anemia...'")
    
    if st.button("Translate & Generate Questions"):
        if not medical_text.strip():
            st.warning("⚠️ Please paste medical text first.")
        else:
            st.success("Translation Complete.")
            st.markdown("### 🔍 What this actually means:")
            
            text_lower = medical_text.lower()
            critical_flags = 0
            
            # EXPANDED CLINICAL DICTIONARY
            if any(word in text_lower for word in ["bilirubin", "liver", "hepatomegaly", "ascites", "alt", "ast", "enzymes"]):
                st.error("🚩 **LIVER ALERT:** The liver is struggling to filter toxins (bilirubin/enzymes). This causes jaundice, fluid retention (ascites), and severe fatigue. Immediate oncology review required.")
                critical_flags += 1
                
            if any(word in text_lower for word in ["anemia", "platelet", "bone marrow", "thrombocytopenia", "bleeding", "bruising"]):
                st.error("🚩 **BLOOD ALERT:** Aplastic anemia / low blood counts confirmed. High risk for bleeding and bruising. Extra caution with hygiene and crowds is mandatory.")
                critical_flags += 1
                
            if any(word in text_lower for word in ["leukocyte", "neutrophil", "wbc", "neutropenia", "sepsis", "infection", "fever"]):
                st.error("🚨 **IMMUNE SYSTEM CRITICAL:** White blood cell counts are low (neutropenia) or infection is present (sepsis). Any fever means IMMEDIATE hospital contact. Do not wait.")
                critical_flags += 1
                
            if critical_flags == 0:
                st.warning("🟡 **NO RED FLAGS DETECTED IN TEXT.** However, this does not mean the results are clear. **You must ask the doctor for a plain-English summary.**")

            st.markdown("### ❓ Questions to ask the Doctor (The Fair Go Shield):")
            st.write("1. What is our primary priority right now: stabilizing the blood counts or managing liver function?")
            st.write("2. Are there specific numerical thresholds (e.g., neutrophils, platelets) that should trigger an emergency hospital visit?")
            st.write("3. What side effects should we expect over the next 48 hours, and what is our home management protocol?")
            st.write("4. Can we get this explanation written down or emailed so we don't have to rely on memory during brain fog?")
            
            st.session_state.history.append(f"Translated medical note: {medical_text[:50]}...")

with tab2:
    st.header("🛡️ The Shield (For the Husband)")
    st.markdown("Police officers and problem-solvers are trained to fix things. Cancer and systemic illness cannot simply be 'fixed'—they must be managed with pacing and protection.")
    
    st.write("### The Admin Triage")
    st.write("- **One Task Rule:** If Dee needs a scan or a blood test today, that is the *only* task on the board. Everything else is cancelled.")
    st.write("- **Outsource the Friction:** Use support networks, meal delivery, or community assistance. Protect your physical bandwidth.")
    
    st.write("### The Emotional Triage")
    st.write("- **You are allowed to break:** If you need to walk outside, punch a bag, or cry in the car, do it. Carrying it all in silence helps nobody.")
    st.write("- **Be Specific with Help:** Never say 'let me know if you need anything.' Say: 'Can you pick up the groceries on Tuesday?'")
    
    st.info("💡 **Carer Reset:** If your stress hits 9/10, step away. Call Geoff. Tag out. You cannot pour from an empty cup.")

with tab3:
    st.header("🧘 Grounding (For Dee)")
    st.markdown("When the fear of blood tests, scans, or the future hits, use this 60-second biological reset.")
    
    st.info("💡 **The Sovereign Rule:** You do not have to fight the whole future today. You only have to survive this exact moment.")
    
    if st.button("Start Grounding Timer (60s)"):
        st.warning("Starting 60-second reset. Close your eyes. Soften your shoulders. Follow the pace.")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(100):
            time.sleep(0.04)
            progress_bar.progress(i + 1)
            if i < 25: status_text.text("Breathe in... (4 seconds)")
            elif i < 50: status_text.text("Hold gently... (4 seconds)")
            elif i < 75: status_text.text("Breathe out slowly... (4 seconds)")
            elif i < 100: status_text.text("Rest in the quiet... (4 seconds)")
            
        st.success("Clarity restored. You are still here. You are still surrounded by love.")
        st.session_state.history.append("Completed 60s grounding reset.")

with tab4:
    st.header("⚙️ Treatment Logs & Medical History Trail")
    st.markdown("Keep a clean, chronological record of translated notes, questions asked, and critical decisions.")
    
    with st.form("manual_log"):
        custom_note = st.text_input("Add manual treatment log entry:")
        if st.form_submit_button("Add to Log") and custom_note:
            st.session_state.history.append(custom_note)
            st.success("Note added.")
            
    if st.session_state.history:
        for idx, entry in enumerate(st.session_state.history, 1):
            st.write(f"{idx}. {entry}")
            
        df_logs = pd.DataFrame({"Dee Protocol Log": st.session_state.history})
        csv_data = df_logs.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Treatment Log (CSV)", data=csv_data, file_name="dee_protocol_log.csv", mime="text/csv")
    else:
        st.info("No activity logged yet today.")

st.sidebar.markdown("---")
st.sidebar.write("**System Status:** Sovereign Protection Active")