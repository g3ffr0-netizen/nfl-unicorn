# =====================================================================
# SOVEREIGN COMMAND CENTRE: DRAGONFIRE EDITION (AMY_APP_V2.py)
# Integrated Sonny & Roz Protocols + Restored Biometrics & Telemetry
# =====================================================================

import time
import datetime
import pandas as pd
import streamlit as st

try:
    from apex_save_utility import render_save_widget
    HAS_SAVE_UTIL = True
except ImportError:
    HAS_SAVE_UTIL = False

# --- PAGE CONFIGURATION & DRAGONFIRE THEME ---
st.set_page_config(
    page_title='Dragonfire Command Centre | Sonny & Roz',
    page_icon='🐉',
    layout='wide',
    initial_sidebar_state='expanded'
)

# High-Fantasy Valyrian / Westerosi Styling (Dark Stone, Forged Iron, Dragonfire Embers)
st.markdown('''
<style>
    .stApp {
        background-color: #121113;
        color: #E6DFD3;
    }
    h1, h2, h3 {
        color: #FF6B35 !important;
        font-family: 'Georgia', serif;
    }
    .stMetric {
        background-color: #1E1C21;
        border: 1px solid #4A2511;
        border-radius: 8px;
        padding: 12px;
    }
    .stButton>button {
        background-color: #8B261D;
        color: #F4EFE6;
        border: 1px solid #FF6B35;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #B8332A;
        border-color: #FFA07A;
    }
</style>
''', unsafe_allow_html=True)

# --- AUTHENTICATION GATE ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title('🐉 Dragonfire Stronghold Gate')
    st.markdown('*Enter your Valyrian credentials to unlock the Sonny & Roz Command Centre.*')
    col1, col2 = st.columns([1, 2])
    with col1:
        user_input = st.text_input('Commander Name', placeholder='amy')
        pass_input = st.text_input('Passphrase', type='password', placeholder='••••••••••••')
        if st.button('Enter Throne Room'):
            if user_input.strip().lower() == 'amy' and pass_input == 'sovereign2026':
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error('🚨 Access Denied: Invalid House credentials.')
    st.stop()

# --- INITIALIZE SESSION STATE (HEIRLOOMS & BIOMETRICS) ---
if 'biometric_logs' not in st.session_state:
    st.session_state.biometric_logs = pd.DataFrame([
        {
            'Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
            'Heart_Rate_BPM': 72,
            'HRV_ms': 58,
            'Sleep_Hours': 7.5,
            'Stress_Level': 3,
            'Energy_MP': 80,
            'Biological_State': '🔥 Flow State'
        }
    ])

if 'quest_log' not in st.session_state:
    st.session_state.quest_log = []

# --- SIDEBAR: THRONE ROOM & BIOMETRIC TELEMETRY INPUTS ---
with st.sidebar:
    st.header('🏰 Throne Room & Biometrics')
    st.caption('Restored Physiological & Energy MP Telemetry')

    st.subheader('💓 Live Biometric Sensors')
    hr_bpm = st.slider('Resting / Current Heart Rate (BPM)', 45, 160, 72)
    hrv_ms = st.slider('Heart Rate Variability — HRV (ms)', 10, 130, 58)
    sleep_hrs = st.slider('Sleep Cycle (Hours)', 0.0, 12.0, 7.5, 0.5)
    meds_taken = st.checkbox('Daily Potion / Meds Taken', value=True)

    st.subheader('🛡️ Carer & Environmental Load')
    carer_stress = st.slider('Carer Stress Index (1–10)', 1, 10, 3)
    sensory_load = st.slider('Sensory / Environment Noise (1–10)', 1, 10, 4)

    # Stress-Tested Energy MP Engine (Bounded 5 to 100)
    base_mp = (sleep_hrs / 8.0) * 50 + (hrv_ms / 100.0) * 30 + (15 if meds_taken else 0)
    strain_penalty = max(0, (hr_bpm - 75) * 0.4) + (carer_stress * 2.5) + (sensory_load * 1.5)
    energy_mp = int(max(5, min(100, base_mp - strain_penalty + 15)))

    if st.button('📥 Log Biometric Snapshot', use_container_width=True):
        if carer_stress >= 9:
            bio_state = '🛑 KILLSWITCH ENGAGED'
        elif energy_mp < 35:
            bio_state = '🚩 Burnout Trap'
        elif energy_mp >= 65:
            bio_state = '🔥 Flow State'
        else:
            bio_state = '⚖️ Steady Reign'

        new_entry = pd.DataFrame([{
            'Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
            'Heart_Rate_BPM': hr_bpm,
            'HRV_ms': hrv_ms,
            'Sleep_Hours': sleep_hrs,
            'Stress_Level': carer_stress,
            'Energy_MP': energy_mp,
            'Biological_State': bio_state
        }])
        st.session_state.biometric_logs = pd.concat([new_entry, st.session_state.biometric_logs], ignore_index=True)
        st.success('Biometric snapshot recorded to Heirlooms!')

# --- KILLSWITCH OVERRIDE CHECK (ROZ PROTOCOL) ---
if carer_stress >= 9:
    st.error('🛑 **ROZ PROTOCOL KILLSWITCH ACTIVATED (Carer Stress ≥ 9/10)**')
    st.markdown('> *"You cannot pour from an empty cup."* High-stress quests and major decisions are locked. Step away, tag out, and initiate **The Third Eye** reset below.')

# --- MAIN HEADER & BIOMETRIC HUD ---
st.title('🐉 Dragonfire Command Centre')
st.markdown('**Integrated Sonny & Roz Protocols** | *Cognitive Exoskeleton & Biometric Telemetry*')

m1, m2, m3, m4 = st.columns(4)
m1.metric('⚡ Energy MP (Mental Power)', f'{energy_mp} / 100', delta=f'{energy_mp - 50} vs baseline')
m2.metric('💓 Heart Rate', f'{hr_bpm} BPM', delta='Elevated' if hr_bpm > 95 else 'Optimal', delta_color='inverse')
m3.metric('📈 HRV (Recovery)', f'{hrv_ms} ms', delta='High Resilience' if hrv_ms >= 50 else 'Low Recovery')
m4.metric('🛡️ Carer Shield Stress', f'{carer_stress} / 10', delta='CRITICAL' if carer_stress >= 8 else 'Protected', delta_color='inverse')

st.markdown('---')

# --- NAVIGATION TABS (WESTEROSI MODULES) ---
tab_bio, tab_quests, tab_roz, tab_thirdeye, tab_npc = st.tabs([
    '💓 Biometrics & Vitals (Restored)',
    '⚔️ Quest Board (Sonny)',
    '🛡️ Roz & Animal Instincts',
    '👁️ The Third Eye (Reset)',
    '📜 NPC Raven Translator'
])

# === TAB 1: RESTORED BIOMETRICS & TELEMETRY ===
with tab_bio:
    st.subheader('💓 Biometric Telemetry & Recovery Matrix')
    st.markdown('Track resting heart rate, HRV, sleep debt, and Energy MP trends across your current Reign.')

    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown('#### 📊 Energy MP & Heart Rate Trend')
        chart_df = st.session_state.biometric_logs[['Timestamp', 'Energy_MP', 'Heart_Rate_BPM', 'HRV_ms']].iloc[::-1]
        st.line_chart(chart_df.set_index('Timestamp'))
    with c2:
        st.markdown('#### 🧬 Physiological Diagnostics')
        if hrv_ms < 35 or hr_bpm > 100:
            st.warning('⚠️ **Autonomic Strain Detected:** Elevated heart rate / low HRV suggests sympathetic nervous system overload. Prioritize low-cost quests.')
        else:
            st.success('✅ **Autonomic Balance Optimal:** Nervous system recovery supports moderate-to-high cognitive load.')

        if energy_mp < 35:
            st.error('🚫 **Cognitive Veto Active:** Energy MP critically low. Defer major financial or medical decisions today.')

    st.markdown('#### 📜 Heirloom Biometric History')
    st.dataframe(st.session_state.biometric_logs, use_container_width=True)

    csv_export = st.session_state.biometric_logs.to_csv(index=False)
    if HAS_SAVE_UTIL:
        render_save_widget(default_filename='Amy_Biometrics_Heirloom', data_content=csv_export, file_extension='.csv')
    else:
        st.download_button(
            label='📥 Save Biometric Heirlooms (.CSV) to PC',
            data=csv_export,
            file_name=f'Amy_Biometrics_Heirloom_{datetime.date.today()}.csv',
            mime='text/csv',
            use_container_width=True
        )

# === TAB 2: QUEST BOARD (SONNY PROTOCOL) ===
with tab_quests:
    st.subheader('⚔️ Sonny Protocol: Energy-Budgeted Quest Board')
    q_col1, q_col2 = st.columns([2, 1])
    with q_col1:
        quest_name = st.text_input('New Quest / Task', placeholder='e.g., Grocery shopping at Lake Haven')
    with q_col2:
        quest_cost = st.number_input('Energy MP Cost', min_value=5, max_value=80, value=20, step=5)

    if st.button('Evaluate & Add Quest'):
        if quest_name.strip():
            if carer_stress >= 9:
                st.error('🛑 Killswitch Active: Cannot add high-load quests right now.')
            elif quest_cost > energy_mp:
                status = '🚩 Burnout Trap (Exceeds Current Energy MP)'
                st.warning(f'{status} — Added to backlog.')
            else:
                status = '🔥 Flow State (Within Energy Budget)'
                st.success(f'{status} — Quest cleared for action!')
            st.session_state.quest_log.append({
                'Quest': quest_name,
                'MP_Cost': quest_cost,
                'Status': status
            })

    if st.session_state.quest_log:
        q_df = pd.DataFrame(st.session_state.quest_log)
        st.table(q_df)
        if HAS_SAVE_UTIL:
            render_save_widget(default_filename='Amy_Quest_Log', data_content=q_df.to_csv(index=False), file_extension='.csv')

# === TAB 3: ROZ PROTOCOL & ANIMAL INSTINCTS ===
with tab_roz:
    st.subheader('🛡️ Roz Behavioral Decipher & Animal Instincts Telemetry')
    st.markdown('Strip away emotional guesswork. Log raw physiological or behavioral observations for definitive diagnostic output.')

    subject_type = st.radio('Telemetry Subject', ['Human / Carer Observation', 'Animal Instincts (Trainer Mode)'], horizontal=True)
    obs_text = st.text_area('Raw Observation', placeholder='e.g., Tremors increasing, voice quiet, pacing OR Dog panting, tail tucked, ears pinned back...')

    if st.button('Run EV Diagnostic Decipher'):
        txt = obs_text.lower()
        if any(w in txt for w in ['tremor', 'pacing', 'rigid', 'freeze', 'fall', 'dizzy']):
            st.error('🚨 **Clinical State:** High-risk motor fluctuation detected. Check medication schedule immediately, reduce environmental stimuli, and enforce fall-prevention protocol.')
        elif any(w in txt for w in ['panting', 'tucked', 'ears back', 'growl', 'whale eye', 'stiff']):
            st.warning('🚩 **Biological State:** High Anxiety / Cortisol Spike (Fear Response). Remove environmental trigger immediately. Do not crowd or force interaction.')
        elif obs_text.strip():
            st.info('⚖️ **Diagnostic State:** Baseline variance within normal parameters. Continue routine monitoring and log biometric check in 60 minutes.')

# === TAB 4: THE THIRD EYE (60-SECOND PHYSIOLOGICAL RESET) ===
with tab_thirdeye:
    st.subheader('👁️ The Third Eye: 60-Second Autonomic Reset')
    st.markdown('When a spiral or heart-rate spike hits, use this guided physiological pacing timer to manually stimulate the vagus nerve.')

    if st.button('🔥 Ignite 60-Second Vagal Reset'):
        progress_bar = st.progress(0)
        status_text = st.empty()
        for sec in range(60):
            cycle = sec % 10
            if cycle < 4:
                phase = '🌬️ INHALE DEEPLY through the nose (4s)...'
            elif cycle < 6:
                phase = '⏸️ HOLD steady (2s)...'
            else:
                phase = '💨 EXHALE SLOWLY through the mouth (4s)...'
            status_text.markdown(f'### {phase} ({60 - sec}s remaining)')
            progress_bar.progress((sec + 1) / 60)
            time.sleep(1)
        status_text.success('✅ **Physiological Reset Complete.** Heart rate and nervous system stabilized.')

# === TAB 5: NPC RAVEN TRANSLATOR ===
with tab_npc:
    st.subheader('📜 NPC Raven Translator')
    st.markdown('Convert exhausted, blunt, or frustrated thoughts into calm, diplomatic communication.')
    raw_thought = st.text_area('Raw Blunt Thought', placeholder="e.g., I'm completely fried today and can't deal with another last-minute meeting.")
    if st.button('Summon Diplomatic Raven'):
        if raw_thought.strip():
            st.info('**Polished Response:**\n\n> *Thank you for reaching out. Due to current scheduling commitments and capacity today, I will need to review this tomorrow when I can give it my full attention. Appreciate your understanding!*')
