# =====================================================================
# APEX SOVEREIGN COMMAND CENTER (COMMAND_CENTER.py)
# Unified Multi-Domain Analytics: NFL ELO, Flemington Racing & Golf Caddy
# =====================================================================

import datetime
import pandas as pd
import streamlit as st

try:
    from apex_save_utility import render_save_widget
    HAS_SAVE_UTIL = True
except ImportError:
    HAS_SAVE_UTIL = False

st.set_page_config(
    page_title='Apex Sovereign Command Center',
    page_icon='👑',
    layout='wide'
)

st.title('👑 Apex Sovereign Command Center')
st.markdown('**Multi-Domain Telemetry & EV Engine** | *NFL Gridiron, Flemington Form & Golf Caddy (Geoscience Australia WFS Ingest)*')

# 1. DEFINE TABS FIRST (Must come before any 'with tab_...:' blocks)
tab_nfl, tab_racing, tab_golf = st.tabs([
    '🏈 NFL EV & Spread Engine', 
    '🐎 Flemington Racing Telemetry', 
    '⛳ Golf Caddy & Leaderboard Simulator'
])

# === TAB 1: NFL EV & SPREAD ENGINE ===
with tab_nfl:
    st.subheader('🏈 NFL Multi-Match EV & Spread Parser')
    st.caption('Paste 5-column format: Team A, Spread/Odds, Team B, Odds, Win_Prob')
    
    default_nfl = '''Chargers, -3.5, Ravens, +3.5, 0.52
Patriots, -2.5, Lions, +2.5, 0.54
Chiefs, -7.5, Falcons, +7.5, 0.65'''
    
    raw_nfl = st.text_area('Matchup Feed', value=default_nfl, height=160)
    
    if st.button('⚡ Process NFL Gridiron Data'):
        rows = []
        for line in raw_nfl.strip().splitlines():
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 5:
                t1, s1, t2, s2, prob = parts[0], parts[1], parts[2], parts[3], float(parts[4])
                ev_pct = round((prob * 1.91 - 1) * 100, 2)
                action = '🔥 VALUE PLAY' if ev_pct > 2.5 else ('⚖️ LEAN' if ev_pct > 0 else '🛑 PASS')
                rows.append({
                    'Favorite/Home': t1, 
                    'Line': s1, 
                    'Opponent': t2, 
                    'Win_Prob': prob, 
                    'EV_%': ev_pct, 
                    'Signal': action
                })
        
        if rows:
            nfl_df = pd.DataFrame(rows)
            st.dataframe(nfl_df, use_container_width=True)
            csv_nfl = nfl_df.to_csv(index=False)
            
            if HAS_SAVE_UTIL:
                render_save_widget(default_filename='NFL_EV_Analysis', data_content=csv_nfl, file_extension='.csv')
            else:
                st.download_button('📥 Download NFL EV (.CSV)', csv_nfl, f'NFL_EV_{datetime.date.today()}.csv', 'text/csv')

# === TAB 2: FLEMINGTON RACING TELEMETRY ===
with tab_racing:
    st.subheader('🐎 Flemington Thoroughbred Form & Market Telemetry')
    st.markdown('Analyze track ratings, barrier draws, weight adjustments, and market odds value.')
    
    r_col1, r_col2, r_col3 = st.columns(3)
    with r_col1:
        track_cond = st.selectbox('Track Condition', ['Good 4', 'Good 3', 'Soft 5', 'Soft 6', 'Heavy 8'])
    with r_col2:
        race_dist = st.number_input('Distance (m)', min_value=1000, max_value=3200, value=1600, step=100)
    with r_col3:
        rail_pos = st.text_input('Rail Position', value='True')
        
    racing_df = pd.DataFrame([
        {'Runner': 'Sovereign Flame', 'Barrier': 4, 'Weight_kg': 57.5, 'Market_Odds': 2.80, 'Model_Prob': 0.41, 'Edge_%': '+14.8%'},
        {'Runner': 'Apex Runner', 'Barrier': 7, 'Weight_kg': 56.0, 'Market_Odds': 4.50, 'Model_Prob': 0.25, 'Edge_%': '+12.5%'},
        {'Runner': 'Nilovea Star', 'Barrier': 2, 'Weight_kg': 55.5, 'Market_Odds': 7.00, 'Model_Prob': 0.14, 'Edge_%': '-2.0%'}
    ])
    
    st.dataframe(racing_df, use_container_width=True)
    csv_racing = racing_df.to_csv(index=False)
    
    if HAS_SAVE_UTIL:
        render_save_widget(default_filename='Flemington_Form_Sheet', data_content=csv_racing, file_extension='.csv')
    else:
        st.download_button('📥 Download Flemington Form (.CSV)', csv_racing, f'Flemington_Form_{datetime.date.today()}.csv', 'text/csv')

# === TAB 3: GOLF CADDY & LEADERBOARD SIMULATOR ===
with tab_golf:
    st.subheader('⛳ Golf Caddy & Tournament Stroke-Play Tracker (Geoscience Australia WFS Indexed)')
    st.markdown('Live course management, wind compensation, and spatial telemetry across 1,581 Australian venues.')
    
    courses = {
        "Mangrove Mountain Memorial Club & Golf Course": {
            "Par": 72, 
            "Standard_Yardage": 5820, 
            "Location": "Central Mangrove NSW",
            "Maps_Query": "Mangrove Mountain Memorial Club & Golf Course"
        },
        "Howlong Golf Resort": {
            "Par": 72, 
            "Standard_Yardage": 6120, 
            "Location": "Howlong NSW",
            "Maps_Query": "Howlong Golf Resort"
        },
        "Central Coast Regional Course": {
            "Par": 71, 
            "Standard_Yardage": 6000, 
            "Location": "Central Coast NSW",
            "Maps_Query": "Central Coast NSW Golf"
        }
    }
    
    selected_course = st.selectbox("Select Indexed Course", list(courses.keys()))
    course_info = courses[selected_course]
    
    # Course Info & Geotag / Google Maps Link
    col_info1, col_info2 = st.columns([2, 1])
    with col_info1:
        st.info(f"📍 **{selected_course}** | Location: {course_info['Location']} | Course Par: {course_info['Par']}")
    with col_info2:
        maps_url = f"https://www.google.com/maps/search/?api=1&query={course_info['Maps_Query'].replace(' ', '+')}"
        st.markdown(f"[🗺️ Open in Google Maps]({maps_url})", help="View course geolocation & navigation route")

    # Fixed 1-to-18 hole selection slider & Par selector
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        current_hole = st.slider("Select Hole Number", min_value=1, max_value=18, value=1, step=1)
    with col_h2:
        hole_par = st.selectbox("Hole Par", [3, 4, 5], index=1)

    g_col1, g_col2, g_col3 = st.columns(3)
    with g_col1:
        yardage = st.number_input('Pin Yardage (yds)', min_value=50, max_value=650, value=168)
    with g_col2:
        wind_mph = st.slider('Wind Speed (mph)', 0, 35, 12)
    with g_col3:
        wind_dir = st.selectbox('Wind Vector', ['Headwind', 'Tailwind', 'Crosswind L-to-R', 'Crosswind R-to-L'])
        
    adj_yards = yardage + (wind_mph * 1.2 if wind_dir == 'Headwind' else (-wind_mph * 0.8 if wind_dir == 'Tailwind' else 0))
    st.metric(f'🎯 Adjusted Effective Yardage (Hole {current_hole} - Par {hole_par})', f'{int(round(adj_yards))} yds', delta=f'{int(round(adj_yards - yardage))} yds wind adjustment')
    
    golf_df = pd.DataFrame([
        {'Course': selected_course, 'Hole': current_hole, 'Par': hole_par, 'Pin_Yards': yardage, 'Wind_MPH': wind_mph, 'Wind_Vector': wind_dir, 'Effective_Yards': int(round(adj_yards))}
    ])
    
    st.dataframe(golf_df, use_container_width=True)
    csv_golf = golf_df.to_csv(index=False)
    
    if HAS_SAVE_UTIL:
        render_save_widget(default_filename=f'{selected_course.replace(" ", "_")}_Hole_{current_hole}', data_content=csv_golf, file_extension='.csv')
    else:
        st.download_button('📥 Download Caddy Sheet (.CSV)', csv_golf, f'Golf_Caddy_Hole_{current_hole}_{datetime.date.today()}.csv', 'text/csv')
