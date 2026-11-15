# =====================================================================
# DRAGONFIRE TACTICAL COMMAND ASSISTANT (AMY_APP_V2.py)
# Theme: Game of Thrones: Dragonfire (Targaryen Civil War Era)
# =====================================================================

import streamlit as st
import random

st.set_page_config(page_title="Dragonfire Tactical Assistant", page_icon="🐉", layout="wide")

# --- VALYRIAN STYLING & HEADER ---
st.markdown("""
<style>
    .main {background-color: #0e1117; color: #e0e0e0;}
    h1, h2, h3 {color: #d4af37; font-family: 'Georgia', serif;}
    .stButton>button {background-color: #8b0000; color: white; border-radius: 4px; font-weight: bold;}
    .stButton>button:hover {background-color: #a52a2a; color: white;}
</style>
""", unsafe_allow_html=True)

st.title("🐉 Dragonfire: Westeros Tactical & Campaign Assistant")
st.markdown("### *Valyrian Noble House Command Center & Hexagonal Warfare Engine*")

# --- NAVIGATION TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🏰 The Throne Room", 
    "⚔️ Hexagonal Tile Warfare", 
    "🐉 The Dragon Pit", 
    "🛡️ Army Formations & Counter-Matrix"
])

# =====================================================================
# TAB 1: THE THRONE ROOM (House Personalization & Profile)
# =====================================================================
with tab1:
    st.header("🏰 The Throne Room: House Configuration")
    st.markdown("Customize your noble house, heraldry, and overarching ambition for the Nine Kingdoms.")
    
    col1, col2 = st.columns(2)
    with col1:
        house_name = st.text_input("Noble House Name", "House Leaudais of Dragonstone")
        banner_color = st.selectbox("Heraldic Banner Colors", ["Black & Crimson Red", "Gold & Obsidian", "Silver & Sea Green", "Bronze & Iron"])
        ruler_title = st.text_input("Current Title", "First Rider of the Sovereign Flame")
    with col2:
        ambition = st.selectbox("House Ambition", [
            "Seize King's Landing & Claim the Iron Throne", 
            "Secure Autonomous Control of Dragonstone", 
            "Establish Trade Monopoly Across the Narrow Sea", 
            "Purge Rival Factions in Total Hexagonal War"
        ])
        st.info(f"🏛️ **Current Reign Status:** Active Campaign | Faction Allegiance: **Targaryen Loyalist**")

    if st.button("💾 Save Throne Room Settings"):
        st.success(f"🔥 House configuration locked for **{house_name}**. The realm acknowledges your claim.")

# =====================================================================
# TAB 2: HEXAGONAL TILE WARFARE (Resource & Territory Control)
# =====================================================================
with tab2:
    st.header("🗺️ Hexagonal Tile Warfare & Territory Control")
    st.markdown("Manage resource acquisition and territory movement across the grid map of Westeros.")
    
    col_x, col_y, col_tile = st.columns(3)
    with col_x:
        grid_q = st.number_input("Hex Coordinate Q", -10, 10, 0)
    with col_y:
        grid_r = st.number_input("Hex Coordinate R", -10, 10, 0)
    with col_tile:
        tile_type = st.selectbox("Tile Classification", [
            "Resource: Iron (High Armor Yield)", 
            "Resource: Stone (Stronghold Fortification)", 
            "Resource: Food (Army Sustenance)", 
            "Seat of Power: Regional Castle", 
            "Impassable Terrain: Mountain / Coastal Cliff"
        ])
        
    if st.button("🔍 Scan Hex Tile Status"):
        st.write(f"📍 **Coordinates:** Q:{grid_q}, R:{grid_r} | **Type:** `{tile_type}`")
        if "Impassable" in tile_type:
            st.error("⚠️ **Navigation Warning:** Impassable terrain. Rerouting aerial or ground forces required.")
        else:
            st.success("🟢 **Territory Viable:** Ready for resource extraction or garrison deployment.")

# =====================================================================
# TAB 3: THE DRAGON PIT (Dragon Raising & Stats)
# =====================================================================
with tab3:
    st.header("🐉 The Dragon Pit: Stats & Habit Mastery")
    st.markdown("Inspect and upgrade your bonded dragons using Relics, Meat, and Dragonfire Keys.")
    
    dragon_choice = st.selectbox("Select Dragon", ["Syrax", "Vhagar", "Caraxes", "Seasmoke", "Solstryker", "Sunfyre", "Custom Sovereign Dragon"])
    
    d_col1, d_col2, d_col3 = st.columns(3)
    with d_col1:
        d_strength = st.slider("Strength (Physical Might)", 1, 100, 85)
    with d_col2:
        d_instinct = st.slider("Instinct (Combat Reflexes)", 1, 100, 90)
    with d_col3:
        d_intel = st.slider("Intelligence (Tactical Acumen)", 1, 100, 88)
        
    total_power = (d_strength + d_instinct + d_intel) * 125
    st.metric(label=f"🔥 Total Combat Power Rating: {dragon_choice}", value=f"{total_power:,}")
    
    if st.button("🍖 Feed & Train Dragon"):
        st.success(f"⚡ **{dragon_choice}** has been conditioned with Dragonfire Keys and fresh meat. Reign level increased!")

# =====================================================================
# TAB 4: ARMY FORMATIONS & COUNTER-MATRIX (Tactical Combat)
# =====================================================================
with tab4:
    st.header("🛡️ Army Formations & Rock-Paper-Scissors Counter System")
    st.markdown("Calculate best troop counters and estimate battle outcomes before marching into King's Landing.")
    
    col_enemy, col_mine = st.columns(2)
    with col_enemy:
        enemy_troop = st.selectbox("Enemy's Main Troop Type", ["Cavalry", "Shieldbearers", "Archers", "Spearmen", "Siege Units"])
        enemy_power = st.number_input("Enemy Troop Count", 1000, 1000000, 100000)
    with col_mine:
        my_troop = st.selectbox("Your Deployed Troop Type", ["Shieldbearers", "Archers", "Spearmen", "Cavalry", "Siege Units"])
        my_power = st.number_input("Your Troop Count", 1000, 1000000, 120000)
        
    if st.button("⚔️ Calculate Battle Strategy"):
        # Counter Logic Matrix
        counters = {
            "Cavalry": "Archers",
            "Shieldbearers": "Spearmen",
            "Archers": "Cavalry",
            "Spearmen": "Shieldbearers",
            "Siege Units": "Shieldbearers"
        }
        
        advantage = "Neutral Engagement"
        if counters.get(enemy_troop) == my_troop:
            advantage = "🔥 Tactical Advantage! Your formation hard-counters the enemy."
        elif counters.get(my_troop) == enemy_troop:
            advantage = "⚠️ Disadvantage! Enemy formation counters your troops. Deploy dragons to break lines."
            
        st.info(f"📊 **Engagement Analysis:** {advantage}")
        est_victory_chance = min(95, max(10, int((my_power / (enemy_power + 1)) * 50)))
        st.success(f"🏆 **Estimated Victory Probability:** {est_victory_chance}%")

st.sidebar.markdown("---")
st.sidebar.write("**Realm:** Westeros (Targaryen Civil War)")
st.sidebar.write("**Build:** v2.0 Dragonfire Edition")
