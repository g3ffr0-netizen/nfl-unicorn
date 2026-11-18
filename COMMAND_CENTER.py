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

    # Fixed 1-to-18 hole selection slider
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
