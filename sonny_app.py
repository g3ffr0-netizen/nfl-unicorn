import streamlit as st
import random

st.set_page_config(page_title="Jake's Command Zone", page_icon="🃏", layout="wide")

# --- CUSTOM CSS FOR THE MTG VIBE ---
st.markdown("""
<style>
    .stApp {
        background-color: #1a1a1a;
        color: #e0e0e0;
    }
    h1, h2, h3 {
        color: #d4af37; /* Gold text */
    }
    .stButton>button {
        background-color: #2b2b2b;
        color: #d4af37;
        border: 1px solid #d4af37;
    }
    .stButton>button:hover {
        background-color: #d4af37;
        color: #1a1a1a;
    }
</style>
""", unsafe_allow_html=True)

st.title("🃏 Jake's Command Zone")
st.markdown("### Battlefield Management & Mana Tracking")

# --- MTG CARD LOOT POOL ---
MTG_LOOT = [
    "Black Lotus", "Mox Sapphire", "Time Walk", "Ancestral Recall", 
    "Ragavan, Nimble Pilferer", "Sheoldred, the Apocalypse", "The One Ring", 
    "Orcish Bowmasters", "Ulamog, the Ceaseless Hunger", "Wrenn and Six", 
    "Fable of the Mirror-Breaker", "Oko, Thief of Crowns", "Lightning Bolt"
]

# --- INITIALIZE STATE ---
if 'xp' not in st.session_state: st.session_state.xp = 0
if 'collection' not in st.session_state: st.session_state.collection = []
if 'quests' not in st.session_state: st.session_state.quests = []

# --- SIDEBAR: MANA & LIFE TOTALS ---
st.sidebar.header("📊 Player Status")
life_total = st.sidebar.slider("Life Total (Sleep/Health)", 0, 40, 20)
meds = st.sidebar.checkbox("Meds Taken (Dex)", value=True)
strain = st.sidebar.slider("Bio-Chemical Strain (T-Supps/Dex)", 0, 10, 3)

# Calculate Mana Pool (Energy)
mana_pool = (life_total * 2) + (10 if meds else 0) - (strain * 3)
mana_pool = max(0, min(100, mana_pool)) 

st.sidebar.metric("Available Mana", f"{mana_pool}/100")

if st.sidebar.button("🔄 New Turn (Reset Day)"):
    st.session_state.quests = []
    st.rerun()

# --- MAIN APP TABS ---
tab1, tab2, tab3 = st.tabs(["⚔️ The Battlefield", "🗣️ The Bard (Translator)", "🎒 The Command Zone"])

with tab1:
    st.markdown("### Cast Spells (Tasks)")
    st.markdown("Enter your tasks. The engine will calculate the Mana Cost. If you don't have enough Mana, you'll tap out.")
    
    with st.form("spell_form"):
        task_name = st.text_input("Spell Name (Task)", "Reply to emails")
        task_type = st.selectbox("Card Type", ["Instant (Admin)", "Sorcery (Creative)", "Creature (Physical)", "Enchantment (Deep Work)"])
        task_diff = st.slider("Mana Value (Difficulty 1-10)", 1, 10, 5)
        submit = st.form_submit_button("Cast Spell")
        
        if submit:
            multiplier = 1.5 if "Deep Work" in task_type else (1.2 if "Creative" in task_type else 1.0)
            mana_cost = int(task_diff * multiplier * 5) # Scaled to Mana Pool
            
            status = "🔥 CASTABLE (Flow State)" if mana_cost <= mana_pool else "🚩 TAPPED OUT (Burnout Trap)"
            
            st.session_state.quests.append({
                "name": task_name,
                "type": task_type,
                "cost": mana_cost,
                "status": status
            })

    if st.session_state.quests:
        st.markdown("---")
        for i, q in enumerate(st.session_state.quests):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"**{q['name']}** ({q['type']})")
                st.write(f"Mana Cost: {q['cost']}")
            with col2:
                if "CASTABLE" in q['status']:
                    st.success(q['status'])
                else:
                    st.error(q['status'])
            with col3:
                if st.button("Resolve", key=f"comp_{i}"):
                    st.session_state.quests.pop(i)
                    xp_gained = q['cost'] * 2
                    st.session_state.xp += xp_gained
                    
                    if random.random() < 0.6:
                        loot = random.choice(MTG_LOOT)
                        st.session_state.collection.append(loot)
                        st.toast(f"🎉 Spell Resolved! +{xp_gained} XP. You pulled a {loot}!")
                    else:
                        st.toast(f"🎉 Spell Resolved! +{xp_gained} XP.")
                    st.rerun()
    else:
        st.info("The stack is empty. Cast a spell above!")

with tab2:
    st.markdown("### 🗣️ The Bard's Translation")
    st.markdown("Type your blunt, unfiltered thought. The Bard will translate it into diplomatic Elvish (Corporate Speak).")
    
    raw_thought = st.text_area("Brain Dump:", height=100, placeholder="Tell Karen I can't do the meeting tomorrow because I'm swamped and she needs to send the report.")
    tone = st.radio("Desired Tone:", ["Professional & Direct", "Collaborative & Soft", "Urgent"])
    
    if st.button("Translate"):
        if not raw_thought:
            st.warning("Please enter a thought first.")
        else:
            if "Karen" in raw_thought:
                translated = "Dear Karen, unfortunately, due to my current workload, I won't be able to attend tomorrow's meeting. Please send over the report so I can review it asynchronously. Best, Jake."
            elif "meeting" in raw_thought.lower():
                translated = "Hi Team, I am unable to attend the upcoming meeting due to conflicting priorities. Please send over the meeting notes and I will review them promptly."
            else:
                translated = f"Hi, regarding the task at hand: {raw_thought}. Unfortunately, due to current capacity constraints, I am unable to address this immediately. Let me know how best to proceed."
            
            st.success("Translation Complete:")
            st.code(translated, language="markdown")

with tab3:
    st.markdown(f"### 🎒 The Command Zone (XP: {st.session_state.xp})")
    
    level = (st.session_state.xp // 100) + 1
    st.progress(min((st.session_state.xp % 100) / 100, 1.0), text=f"Commander Level {level} ({st.session_state.xp % 100}/100 to next level)")
    
    st.markdown("#### Your Collection:")
    cols = st.columns(4)
    for i, card in enumerate(st.session_state.collection):
        with cols[i % 4]:
            st.info(f"🃏 **{card}**")
