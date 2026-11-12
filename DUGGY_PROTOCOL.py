import streamlit as st
import math

st.set_page_config(page_title="Duggy's Caddy", page_icon="⛳", layout="wide")

# --- CUSTOM CSS FOR THE GAMER VIBE ---
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #f0f2f6;
    }
    h1 {
        color: #00ffcc; /* Neon Cyan for Duggy */
    }
    .stButton>button {
        background-color: #1e1e1e;
        color: #00ffcc;
        border: 1px solid #00ffcc;
    }
    .stButton>button:hover {
        background-color: #00ffcc;
        color: #0e1117;
    }
</style>
""", unsafe_allow_html=True)

st.title("⛳ Duggy's Advanced Command Centre")
st.markdown("### Tour Pro Mode: No Ego. Just Math.")

# --- TOUKLEY GOLF CLUB DATABASE (We can update this to Waratah later) ---
TOUKLEY_COURSE = {
    1: {"par": 5, "dist": 475}, 2: {"par": 4, "dist": 395}, 3: {"par": 4, "dist": 295},
    4: {"par": 5, "dist": 460}, 5: {"par": 4, "dist": 378}, 6: {"par": 3, "dist": 179},
    7: {"par": 4, "dist": 384}, 8: {"par": 3, "dist": 135}, 9: {"par": 4, "dist": 381},
    10: {"par": 4, "dist": 350}, 11: {"par": 4, "dist": 330}, 12: {"par": 5, "dist": 482},
    13: {"par": 3, "dist": 150}, 14: {"par": 4, "dist": 362}, 15: {"par": 5, "dist": 532},
    16: {"par": 4, "dist": 288}, 17: {"par": 3, "dist": 196}, 18: {"par": 4, "dist": 370}
}

# --- SIDEBAR: PRE-FLIGHT CHECKLIST ---
st.sidebar.header("🎒 Bag Check (Pre-Flight)")
tinnies = st.sidebar.checkbox("Tinnies & Ice Packed?", value=False)
water = st.sidebar.checkbox("Water Bottle?", value=False)
balls = st.sidebar.checkbox("Enough Balls?", value=False)
routine = st.sidebar.checkbox("Pre-Shot Routine Locked?", value=False)

if not all([tinnies, water, balls, routine]):
    st.sidebar.warning("⚠️ **BAG CHECK INCOMPLETE.** Do not tee off until your mind is clear.")
else:
    st.sidebar.success("✅ **BAG CHECK COMPLETE.** Go play the percentages.")

st.sidebar.markdown("---")

# --- SIDEBAR: COURSE INPUTS ---
st.sidebar.header("🏌️‍♂️ Course Inputs")
hole = st.sidebar.selectbox("Select Hole", list(TOUKLEY_COURSE.keys()))
par = TOUKLEY_COURSE[hole]["par"]
distance = TOUKLEY_COURSE[hole]["dist"]
st.sidebar.info(f"Hole {hole} is Par {par}, {distance}m")

# --- SIDEBAR: CONDITIONS ---
st.sidebar.markdown("---")
st.sidebar.header("🌬️ Conditions")
wind = st.sidebar.slider("Wind Speed (km/h)", 0, 50, 10)
wind_dir = st.sidebar.selectbox("Wind Direction", ["Headwind", "Tailwind", "Crosswind"])

# --- SIDEBAR: MENTAL STATE ---
st.sidebar.markdown("---")
st.sidebar.header("🧠 Mental State")
pressure = st.sidebar.slider("Mental Pressure (1-10)", 1, 10, 5)
miss_tendency = st.sidebar.selectbox("Typical Miss", ["Straight", "Slice", "Hook"])

# --- LOGIC ENGINE ---
def calculate_effective_distance(distance, wind, direction):
    if direction == "Headwind":
        return distance + (wind * 1.5)
    elif direction == "Tailwind":
        return max(0, distance - (wind * 1.5))
    return distance

eff_distance = calculate_effective_distance(distance, wind, wind_dir)

def get_club_and_strategy(eff_dist, pressure, miss, wind_speed):
    # Advanced logic for single-figure handicapper
    if pressure > 8 or wind_speed > 30:
        club = "Safety Club (5-Iron/Hybrid)"
        strategy = "The engine has detected high stress or extreme wind. Do not be a hero. Keep it in play."
        risk = "🚩 HIGH RISK - EGO DETECTED"
    elif eff_dist > 400 and pressure <= 6:
        club = "Driver"
        strategy = "Aggressive play. Pick a specific target in the fairway. Smooth tempo."
        risk = "🔥 VALUE PLAY (Aggressive)"
    elif eff_dist > 200:
        club = "Mid-Iron / Hybrid"
        strategy = "Aim for the center of the green. Take the safe miss."
        risk = "🟢 STANDARD PLAY"
    else:
        club = "Scoring Wedge"
        strategy = "Attack the pin. Be precise."
        risk = "🟢 SCORING OPPORTUNITY"

    if miss == "Slice":
        strategy += " (Alignment: Aim left, hold off the release)."
    elif miss == "Hook":
        strategy += " (Alignment: Aim right, feel the clubface stay open)."

    return club, strategy, risk

def mental_reset(pressure):
    if pressure >= 8:
        return "🚨 **SYSTEM OVERRIDE:** Your brain is over-aroused. Take 3 deep breaths. Step back. Do not swing until your heart rate drops."
    elif pressure >= 5:
        return "🟡 **MODERATE PRESSURE:** Stick to your routine. Count to 3. Smooth tempo."
    else:
        return "🟢 **CALM STATE:** Trust your swing. Execute the plan."

# --- MAIN UI ---
st.header(f"Waratah GC (Simulated) | Hole {hole} | Par {par}")

col_dist1, col_dist2 = st.columns(2)
with col_dist1: st.metric("Actual Distance", f"{distance}m")
with col_dist2: st.metric("Effective Distance (Wind)", f"{int(eff_distance)}m")

club, strategy, risk = get_club_and_strategy(eff_distance, pressure, miss_tendency, wind)
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
st.write("☐ One practice swing focusing *only* on smooth tempo.")
st.write("☐ Step in, align the clubface, and breathe out.")
st.write("☐ Swing. Do not try to 'hit' the ball; let the club swing.")
