import streamlit as st

st.set_page_config(
    page_title="Mangrove Mountain Caddy · KISS",
    page_icon="⛳",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2rem;
            max-width: 680px;
        }
        .cue-banner {
            background: #111827;
            color: #F9FAFB;
            border-left: 8px solid #10B981;
            border-radius: 12px;
            padding: 1.15rem 1.25rem;
            margin: 0.75rem 0 1.1rem 0;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.14);
        }
        .cue-label {
            font-size: 0.78rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #6EE7B7;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }
        .cue-text {
            font-size: 1.55rem;
            font-weight: 800;
            line-height: 1.25;
            letter-spacing: 0.01em;
        }
        .aim-box {
            background: #F3F4F6;
            color: #111827;
            border-radius: 10px;
            padding: 0.9rem 1.1rem;
            margin-top: 0.6rem;
            font-size: 1.05rem;
            font-weight: 600;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

MANGROVE_HOLES = [
    {"hole": 1, "par": 4, "hcp": 5,  "white": 340, "red": 319},
    {"hole": 2, "par": 4, "hcp": 1,  "white": 386, "red": 370},
    {"hole": 3, "par": 4, "hcp": 9,  "white": 301, "red": 286},
    {"hole": 4, "par": 5, "hcp": 4,  "white": 410, "red": 410},
    {"hole": 5, "par": 3, "hcp": 15, "white": 121, "red": 121},
    {"hole": 6, "par": 3, "hcp": 14, "white": 125, "red": 120},
    {"hole": 7, "par": 4, "hcp": 3,  "white": 340, "red": 330},
    {"hole": 8, "par": 3, "hcp": 11, "white": 157, "red": 157},
    {"hole": 9, "par": 4, "hcp": 18, "white": 238, "red": 224},
]

DEFAULT_BAG = [
    ("Driver", 215),
    ("3 Wood", 195),
    ("Hybrid", 175),
    ("5 Iron", 160),
    ("6 Iron", 150),
    ("7 Iron", 140),
    ("8 Iron", 130),
    ("9 Iron", 120),
    ("PW", 108),
    ("GW", 95),
    ("SW", 80),
]

st.title("⛳ Mangrove Mountain Caddy")

c_tee, c_hole = st.columns([1, 2])
with c_tee:
    tee = st.radio("Tees", ["White", "Red"], horizontal=True)
with c_hole:
    hole_num = st.selectbox(
        "Hole",
        options=[h["hole"] for h in MANGROVE_HOLES],
        format_func=lambda n: (
            f"Hole {n} · Par {MANGROVE_HOLES[n-1]['par']} · "
            f"{MANGROVE_HOLES[n-1]['white' if tee == 'White' else 'red']}m (HCP {MANGROVE_HOLES[n-1]['hcp']})"
        ),
    )

hole = MANGROVE_HOLES[hole_num - 1]
stock_m = hole["white"] if tee == "White" else hole["red"]

st.markdown(
    """
    <div class="cue-banner">
        <div class="cue-label">Pre-Shot Routine · Stay In The Barrel</div>
        <div class="cue-text">HIPS, HIPS — STAY WITH THE BALL</div>
    </div>
    """,
    unsafe_allow_html=True,
)

m1, m2, m3 = st.columns(3)
m1.metric("Hole", f"#{hole['hole']}")
m2.metric("Par / HCP", f"Par {hole['par']} · HCP {hole['hcp']}")
m3.metric(f"{tee} Tee", f"{stock_m} m")

st.divider()

st.subheader("🔭 Rangefinder")
r1, r2, r3 = st.columns(3)
with r1:
    laser_m = st.number_input(
        "Laser (m)",
        min_value=10,
        max_value=600,
        value=int(stock_m),
        step=1,
        key=f"laser_{hole_num}_{tee}",
    )
with r2:
    slope_m = st.number_input(
        "Slope (+/- m)",
        min_value=-40,
        max_value=40,
        value=0,
        step=1,
        help="+ uphill (plays longer), - downhill (plays shorter)",
    )
with r3:
    wind = st.selectbox(
        "Wind",
        ["Calm (0)", "Light Head (+5m)", "Strong Head (+12m)", "Light Tail (-5m)", "Strong Tail (-10m)"],
    )

wind_adj = {
    "Calm (0)": 0,
    "Light Head (+5m)": 5,
    "Strong Head (+12m)": 12,
    "Light Tail (-5m)": -5,
    "Strong Tail (-10m)": -10,
}[wind]

plays_like = max(10, int(round(laser_m + slope_m + wind_adj)))

with st.expander("🎒 My Club Distances (edit anytime)", expanded=False):
    bag = []
    cols = st.columns(3)
    for idx, (club_name, default_dist) in enumerate(DEFAULT_BAG):
        with cols[idx % 3]:
            d = st.number_input(
                f"{club_name} (m)",
                min_value=30,
                max_value=320,
                value=default_dist,
                step=1,
                key=f"bag_{club_name}",
            )
            bag.append((club_name, d))

best_club, best_dist = min(bag, key=lambda item: abs(item[1] - plays_like))

res1, res2 = st.columns(2)
res1.metric("Plays-Like Distance", f"{plays_like} m", f"{plays_like - laser_m:+d} m adj")
res2.metric("Suggested Club", best_club, f"Stock {best_dist} m")

st.markdown(
    """
    <div class="aim-box">
        🎯 <strong>Target Line:</strong> Aim <strong>left-centre</strong> to allow for your small miss right.
        Lift arms &amp; cock wrists as one — watch the ball leave before looking up.
    </div>
    """,
    unsafe_allow_html=True,
)
