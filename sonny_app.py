
import streamlit as st
import random

st.set_page_config(page_title="Sonny Command Centre", page_icon="🎮", layout="wide")
st.title("🎮 Sonny Command Centre [ADHD Protocol]")
st.markdown("### Player Stats, Quest Board & NPC Translator")

# --- INITIALIZE STATE ---
if 'xp' not in st.session_state: st.session_state.xp = 0
if 'pokemon' not in st.session_state: st.session_state.pokemon = ["Squirtle"]
if 'quests' not in st.session_state: st.session_state.quests = []

POKEMON_LOOT = ["Pikachu", "Charmander", "Bulbasaur", "Eevee", "Snorlax", "Gengar", "Mewtwo", "Lucario", "Charizard", "Gyarados"]

st.sidebar.header("🕹️ Player Status")
sleep = st.sidebar.slider("Sleep (Hours)", 0.0, 12.0, 7.0, 0.5)
meds = st.sidebar.checkbox("Meds Taken (Dex)", value=True)
stress = st.sidebar.slider("Stress Level (1-10)", 1, 10, 5)

# Calculate Energy Budget
energy_budget = (sleep * 10) + (30 if meds else 0) - (stress * 5)
energy_budget = max(10, min(100, energy_budget)) # Cap between 10 and 100

st.sidebar.metric("Current Energy MP", f"{energy_budget}/100")

if st.sidebar.button("🔄 Reset Session (New Day)"):
    st.session_state.xp = 0
    st.session_state.pokemon = ["Squirtle"]
    st.session_state.quests = []
    st.rerun()

# --- MAIN APP TABS ---
tab1, tab2, tab3 = st.tabs(["📋 Quest Board", "🧠 NPC Translator", "🎒 The Collection"])

with tab1:
    st.markdown("### Generate Today's Quests")
    st.markdown("Enter your tasks for the day. The Guild Master will calculate the energy cost.")
    
    with st.form("quest_form"):
        task_name = st.text_input("Task Name", "Reply to emails")
        task_type = st.selectbox("Task Type", ["Admin", "Creative", "Physical", "Deep Work"])
        task_diff = st.slider("Task Difficulty (1-10)", 1, 10, 5)
        submit = st.form_submit_button("Add to Quest Board")
        
        if submit:
            # Calculate Cost based on Type and Difficulty
            multiplier = 1.5 if task_type == "Deep Work" else (1.2 if task_type == "Creative" else 1.0)
            energy_cost = int(task_diff * multiplier * 10)
            
            status = "🔥 FLOW STATE" if energy_cost <= energy_budget else "🚩 BURNOUT TRAP"
            
            st.session_state.quests.append({
                "name": task_name,
                "type": task_type,
                "cost": energy_cost,
                "status": status
            })

    if st.session_state.quests:
        st.markdown("---")
        for i, q in enumerate(st.session_state.quests):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"**{q['name']}** ({q['type']})")
                st.write(f"Cost: {q['cost']} MP")
            with col2:
                if "FLOW" in q['status']:
                    st.success(q['status'])
                else:
                    st.error(q['status'])
            with col3:
                if st.button("Complete", key=f"comp_{i}"):
                    # Remove from board
                    st.session_state.quests.pop(i)
                    # Give XP
                    xp_gained = q['cost'] * 2
                    st.session_state.xp += xp_gained
                    
                    # Loot Drop Chance
                    if random.random() < 0.6:
                        loot = random.choice(POKEMON_LOOT)
                        st.session_state.pokemon.append(loot)
                        st.toast(f"🎉 Quest Complete! +{xp_gained} XP. You caught a {loot}!")
                    else:
                        st.toast(f"🎉 Quest Complete! +{xp_gained} XP.")
                    st.rerun()
    else:
        st.info("No quests on the board. Add one above!")

with tab2:
    st.markdown("### 🗣️ The NPC Translator")
    st.markdown("Type your blunt, unfiltered thought. The Guild Bard will translate it into professional corporate speak.")
    
    raw_thought = st.text_area("Brain Dump:", height=100, placeholder="Tell Karen I can't do the meeting tomorrow because I'm swamped and she needs to send the report.")
    tone = st.radio("Desired Tone:", ["Professional & Direct", "Collaborative & Soft", "Urgent"])
    
    if st.button("Translate to Corporate"):
        if not raw_thought:
            st.warning("Please enter a thought first.")
        else:
            # Smart logic translation
            if "Karen" in raw_thought:
                translated = "Dear Karen, unfortunately, due to my current workload, I won't be able to attend tomorrow's meeting. Please send over the report so I can review it asynchronously. Best, Jake."
            elif "meeting" in raw_thought.lower():
                translated = "Hi Team, I am unable to attend the upcoming meeting due to conflicting priorities. Please send over the meeting notes and I will review them promptly."
            else:
                translated = f"Hi, regarding the task at hand: {raw_thought}. Unfortunately, due to current capacity constraints, I am unable to address this immediately. Let me know how best to proceed."
            
            st.success("Translation Complete:")
            st.code(translated, language="markdown")
            st.caption("Copy the text above and send it!")

with tab3:
    st.markdown(f"### 🎒 Your Collection (XP: {st.session_state.xp})")
    
    # Level Calculation
    level = (st.session_state.xp // 100) + 1
    st.progress(min((st.session_state.xp % 100) / 100, 1.0), text=f"Level {level} ({st.session_state.xp % 100}/100 to next level)")
    
    st.markdown("#### Caught Pokémon:")
    # Display as a grid of cards
    cols = st.columns(4)
    for i, poke in enumerate(st.session_state.pokemon):
        with cols[i % 4]:
            st.info(f"🃏 **{poke}**")
