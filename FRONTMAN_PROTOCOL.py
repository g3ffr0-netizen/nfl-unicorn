import streamlit as st
import time
import pandas as pd

st.set_page_config(page_title="The Frontman Protocol", page_icon="🎤", layout="wide")

# --- CUSTOM CSS FOR THE STAGE VIBE ---
st.markdown("""
<style>
    .stApp {
        background-color: #121212;
        color: #e0e0e0;
    }
    h1 {
        color: #ff0033; /* Stage Red */
    }
    .stButton>button {
        background-color: #1e1e1e;
        color: #ff0033;
        border: 1px solid #ff0033;
    }
    .stButton>button:hover {
        background-color: #ff0033;
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎤 The Frontman Protocol")
st.markdown("### Vocal Stamina, Stage Presence, and Mental Fortitude.")

# --- SESSION STATE ---
if 'setlist' not in st.session_state: st.session_state.setlist = []
if 'history' not in st.session_state: st.session_state.history = []

# --- SIDEBAR: TELEMETRY ---
st.sidebar.header("🎛️ Soundcheck (Player Status)")
vocal_stamina = st.sidebar.slider("Vocal Stamina (1-100)", 0, 100, 80)
mood = st.sidebar.select_slider("Current State", options=["Depressed", "Low", "Stable", "Elevated", "Manic"], value="Stable")
anxiety = st.sidebar.slider("Stage Fright / Anxiety (1-10)", 1, 10, 3)
meds = st.sidebar.checkbox("Meds Taken", value=True)

# --- MAIN TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["🎸 The Setlist", "🧠 The Mind", "🎼 The Vocal", "📓 The Log"])

with tab1:
    st.header("Tonight's Setlist (Tasks)")
    st.markdown("Enter your tasks for the day. The engine calculates the Vocal Strain.")
    
    with st.form("setlist_form"):
        task_name = st.text_input("Song / Task Name", "Reply to band emails")
        task_type = st.selectbox("Intensity", ["Backstage (Admin)", "Rehearsal (Creative)", "The Gig (Deep Work)", "Heavy Metal (Physical)"])
        task_diff = st.slider("Difficulty (1-10)", 1, 10, 5)
        submit = st.form_submit_button("Add to Setlist")
        
        if submit:
            multiplier = 1.5 if task_type == "The Gig (Deep Work)" else (1.2 if task_type == "Rehearsal (Creative)" else 1.0)
            vocal_cost = int(task_diff * multiplier * 5)
            
            status = "🔥 PEAK PERFORMANCE" if vocal_cost <= vocal_stamina else "🚩 VOCAL STRAIN (Burnout Trap)"
            
            st.session_state.setlist.append({
                "name": task_name,
                "type": task_type,
                "cost": vocal_cost,
                "status": status
            })

    if st.session_state.setlist:
        st.markdown("---")
        for i, q in enumerate(st.session_state.setlist):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"**{q['name']}** ({q['type']})")
                st.write(f"Vocal Cost: {q['cost']}")
            with col2:
                if "PEAK" in q['status']:
                    st.success(q['status'])
                else:
                    st.error(q['status'])
            with col3:
                if st.button("Complete", key=f"comp_{i}"):
                    st.session_state.setlist.pop(i)
                    st.toast("🎸 Song complete. Take a bow.")
                    st.rerun()
    else:
        st.info("The stage is empty. Add a task above.")

with tab2:
    st.header("🧠 The Mind (Bipolar / ADHD Management)")
    
    if mood == "Manic" or mood == "Elevated":
        st.warning("🚨 **HYPOMANIC STATE DETECTED.** Energy is high but erratic. Do not make impulsive decisions tonight. Stick to the setlist.")
    elif mood == "Depressed" or vocal_stamina < 30:
        st.error("🛑 **LOW ENERGY / DEPRESSIVE STATE.** Cancel non-essential tasks. Rest your voice and your mind.")
    else:
        st.success("🟢 **STABLE STATE.** You are ready for the stage.")
        
    if st.button("Open The Green Room (60s Grounding)"):
        st.info("Starting 60-second reset. Deep diaphragmatic breathing. Follow the pace.")
        progress_bar = st.progress(0)
        status_text = st.empty()
        for i in range(100):
            time.sleep(0.03)
            progress_bar.progress(i + 1)
            if i < 25: status_text.text("Breathe in... (4 seconds)")
            elif i < 50: status_text.text("Hold gently... (4 seconds)")
            elif i < 75: status_text.text("Breathe out slowly... (4 seconds)")
            else: status_text.text("Rest in the quiet... (4 seconds)")
        st.success("Clarity restored. Go smash it.")

with tab3:
    st.header("🎼 The Vocal Shield (Opera Training)")
    st.markdown("Use your classical training to protect your heavy metal voice.")
    
    st.write("### The Pre-Show Checklist")
    st.write("☐ Hydration (Water at room temp).")
    st.write("☐ Lip trills and vocal fry warm-up.")
    st.write("☐ Diaphragmatic breathing exercises.")
    
    st.info("💡 **The Rule:** Stamina is everything. If your throat feels tight, cancel the scream and use the operatic belt. Protect the instrument.")

with tab4:
    st.header("📓 Tour Log")
    
    with st.form("log_form"):
        log_entry = st.text_input("Log an event or intervention:")
        submitted = st.form_submit_button("Save to Log")
        if submitted and log_entry:
            st.session_state.history.append(log_entry)
            st.success("Logged.")
            
    if st.session_state.history:
        for idx, entry in enumerate(st.session_state.history, 1):
            st.write(f"{idx}. {entry}")
            
        df_logs = pd.DataFrame({"Tour Log": st.session_state.history})
        csv_data = df_logs.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Tour Log", data=csv_data, file_name="frontman_log.csv", mime="text/csv")
    else:
        st.info("No logs yet.")

st.sidebar.markdown("---")
st.sidebar.write("**System Status:** Ready to Rock")
