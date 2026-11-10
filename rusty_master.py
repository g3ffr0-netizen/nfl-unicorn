import streamlit as st
import math

st.set_page_config(page_title="Rusty's Hub", page_icon="⛳", layout="wide")
st.title("⛳ Rusty's Sovereign Caddy [v2.4 Aegis]")
st.markdown("### Play the percentages. Strip the ego. Execute the plan.")

tab1, tab2 = st.tabs(["🏌️‍♂️ The Mental Caddy", "🛠️ The Shroomozzle Solver"])

# ==========================================
# TAB 1: THE MENTAL CADDY
# ==========================================
with tab1:
    st.sidebar.header("🏌️‍♂️ Course & Player Inputs")
    
    # CORRECTED TOUKLEY GOLF CLUB DATABASE
    TOUKLEY_COURSE = {
        1: {"par": 5, "dist": 475}, 
        2: {"par": 4, "dist": 395}, 
        3: {"par": 4, "dist": 295},
        4: {"par": 5, "dist": 460}, 
        5: {"par": 4, "dist": 378}, 
        6: {"par": 3, "dist": 179},
        7: {"par": 4, "dist": 384}, 
        8: {"par": 3, "dist": 135}, 
        9: {"par": 4, "dist": 381},
        10: {"par": 4, "dist": 350}, 
        11: {"par": 4, "dist": 330}, 
        12: {"par": 5, "dist": 482},
        13: {"par": 3, "dist": 150}, 
        14: {"par": 4, "dist": 362}, 
        15: {"par": 5, "dist": 532},
        16: {"par": 4, "dist": 288}, 
        17: {"par": 3, "dist": 196}, 
        18: {"par": 4, "dist": 370}
    }
    
    hole = st.sidebar.selectbox("Select Hole", list(TOUKLEY_COURSE.keys()))
    par = TOUKLEY_COURSE[hole]["par"]
    distance = TOUKLEY_COURSE[hole]["dist"]
    
    st.sidebar.info(f"Hole {hole} is Par {par}, {distance}m")
    
    st.sidebar.markdown("---")
    st.sidebar.header("🌬️ Conditions")
    wind = st.sidebar.slider("Wind Speed (km/h)", 0, 50, 10)
    wind_dir = st.sidebar.selectbox("Wind Direction", ["Headwind", "Tailwind", "Crosswind"])
    
    st.sidebar.markdown("---")
    st.sidebar.header("🧠 Mental State")
    pressure = st.sidebar.slider("Mental Pressure (1-10)", 1, 10, 5)
    miss_tendency = st.sidebar.selectbox("Typical Miss", ["Straight", "Slice", "Hook"])

    def calculate_effective_distance(distance, wind, direction):
        if direction == "Headwind":
            return distance + (wind * 1.5)
        elif direction == "Tailwind":
            return max(0, distance - (wind * 1.5))
        return distance

    eff_distance = calculate_effective_distance(distance, wind, wind_dir)

    def get_club_and_strategy(eff_dist, pressure, miss):
        if pressure > 7 or wind > 25:
            club = "5-Iron or Hybrid (Safe)"
            strategy = "Swing easy. Keep it in play. Do not try to be a hero. The engine has flagged your ego."
            risk = "🚩 HIGH RISK - EGO DETECTED"
        elif eff_dist > 400 and pressure <= 5:
            club = "Driver"
            strategy = "Pick a specific target in the fairway, not the pin. Smooth tempo."
            risk = "🔥 VALUE PLAY (Aggressive)"
        elif eff_dist > 200:
            club = "5-Iron or 4-Hybrid"
            strategy = "Smooth tempo. Let the club do the work. Aim for the center of the green."
            risk = "🟢 STANDARD PLAY"
        else:
            club = "9-Iron or Wedge"
            strategy = "Aim for the fat of the green. Take one extra club."
            risk = "🟢 STANDARD PLAY"

        if miss == "Slice":
            strategy += " (Alignment: Close the clubface slightly or aim left)."
        elif miss == "Hook":
            strategy += " (Alignment: Open the clubface slightly or aim right)."

        return club, strategy, risk

    def mental_reset(pressure):
        if pressure >= 8:
            return "🚨 **SYSTEM OVERRIDE:** Your brain is over-aroused. Take 3 deep breaths. Look at a cloud. Step back. Do not swing until your heart rate drops."
        elif pressure >= 5:
            return "🟡 **MODERATE PRESSURE:** Stick to your exact pre-shot routine. Count to 3."
        else:
            return "🟢 **CALM STATE:** Trust your swing. Execute the plan."

    st.header(f"Toukley GC | Hole {hole} | Par {par}")
    
    col_dist1, col_dist2 = st.columns(2)
    with col_dist1: st.metric("Actual Distance", f"{distance}m")
    with col_dist2: st.metric("Effective Distance (Wind)", f"{int(eff_distance)}m")

    club, strategy, risk = get_club_and_strategy(eff_distance, pressure, miss_tendency)
    reset = mental_reset(pressure)

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Recommended Club", value=club)
        st.info(f"**Caddy Strategy:** {strategy}")
        
        if "HIGH RISK" in risk:
            st.error(risk)
        else:
            st.success(risk)

    with col2:
        st.warning(reset)

    st.markdown("---")
    st.subheader("🧘 Pre-Shot Routine Checklist")
    st.write("☐ Stand behind the ball and pick an exact target.")
    st.write("☐ Take one practice swing focusing *only* on smooth tempo.")
    st.write("☐ Step in, align the clubface, and breathe out.")
    st.write("☐ Swing. Do not try to 'hit' the ball; let the club swing.")

# ==========================================
# TAB 2: THE SHOO MOZZLE SOLVER
# ==========================================
with tab2:
    st.header("🛠️ GitHub & Streamlit Troubleshooting")
    st.markdown("Use this hardened checklist when deploying or sharing links with mobile users.")
    
    st.subheader("1. The Privacy Toggle")
    st.write("Streamlit apps are **Private** by default. You must make them Public for mobile access.")
    st.code("Streamlit Dashboard -> Click App -> Share (Bottom Right) -> Set to 'This app is public'")
    
    st.subheader("2. The Branch & File Path")
    st.write("Prevent 404 errors by matching your exact repository structure.")
    st.code("Branch: main\nMain file path: rusty_master.py")
    
    st.subheader("3. URL Sanitization Check")
    st.write("Ensure links shared via text contain zero trailing punctuation.")
    st.code("Correct: https://rusty-master.streamlit.app\nIncorrect: https://rusty-master.streamlit.app).")
