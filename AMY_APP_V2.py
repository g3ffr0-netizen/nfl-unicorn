import streamlit as st

# ... (Your existing Amy Protocol code) ...

st.markdown("---") # Adds a nice divider line
st.header("🐉 Dragonfire Tactical Assistant")
st.markdown("Calculate the best troop counters and estimate battle outcomes.")

# Use columns so it looks clean on the page
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Enemy Intel")
    enemy_troop = st.selectbox("Enemy's Main Troop Type", 
                               ["Cavalry", "Shieldbearers", "Archers", "Spearmen"], 
                               key="amy_enemy_type")
    enemy_power = st.number_input("Enemy Troop Power (Total)", 
                                  min_value=0, value=100000, step=10000, 
                                  key="amy_enemy_power")

with col2:
    st.subheader("2. Your Army")
    my_troop_count = st.number_input("How many troops are you sending?", 
                                     min_value=0, value=120000, step=10000, 
                                     key="amy_my_troops")

if st.button("Calculate Battle Strategy", type="primary", key="amy_calc_btn"):
    # Rock-paper-scissors logic
    counters = {
        "Cavalry": "Shieldbearers",     
        "Shieldbearers": "Archers",     
        "Archers": "Spearmen",          
        "Spearmen": "Cavalry"           
    }
    
    best_troop = counters[enemy_troop]
    
    st.success(f"### Recommended Counter: **{best_troop}**")
    st.write(f"Because **{best_troop}** have a type advantage against **{enemy_troop}**.")
    
    # Basic Combat Math
    st.subheader("📊 Battle Estimation")
    my_effective_power = my_troop_count * 1.2 # 20% counter buff
    
    if my_effective_power > enemy_power:
        st.info(f"**Predicted Outcome: Victory.** Your effective power ({int(my_effective_power):,}) overwhelms the enemy ({enemy_power:,}).")
    elif my_effective_power == enemy_power:
        st.warning("**Predicted Outcome: Even Match.** This will be a bloody battle. Send more troops.")
    else:
        st.error(f"**Predicted Outcome: Defeat.** You do not have enough power. The enemy has the advantage.")
