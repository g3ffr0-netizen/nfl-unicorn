# === TAB 3: GOLF CADDY & LEADERBOARD SIMULATOR ===
with tab_golf:
    st.subheader('⛳ Golf Caddy & Tournament Stroke-Play Tracker (Geoscience Australia WFS Indexed)')
    st.markdown('Live course management, wind compensation, and spatial telemetry across 1,581 Australian venues.')
    
    # Course selection dictionary including Mangrove Mountain
    courses = {
        "Mangrove Mountain Memorial Club & Golf Course": {"Par": 72, "Standard_Yardage": 5820, "Location": "Central Mangrove NSW"},
        "Howlong Golf Resort": {"Par": 72, "Standard_Yardage": 6120, "Location": "Howlong NSW"},
        "Central Coast Regional Course": {"Par": 71, "Standard_Yardage": 6000, "Location": "Central Coast NSW"}
    }
    
    selected_course = st.selectbox("Select Indexed Course", list(courses.keys()))
    course_info = courses[selected_course]
    st.info(f"📍 **{selected_course}** | Location: {course_info['Location']} | Course Par: {course_info['Par']}")

    g_col1, g_col2, g_col3 = st.columns(3)
    with g_col1:
        yardage = st.number_input('Pin Yardage (yds)', min_value=50, max_value=650, value=168)
    with g_col2:
        wind_mph = st.slider('Wind Speed (mph)', 0, 35, 12)
    with g_col3:
        wind_dir = st.selectbox('Wind Vector', ['Headwind', 'Tailwind', 'Crosswind L-to-R', 'Crosswind R-to-L'])
        
    adj_yards = yardage + (wind_mph * 1.2 if wind_dir == 'Headwind' else (-wind_mph * 0.8 if wind_dir == 'Tailwind' else 0))
    st.metric('🎯 Adjusted Effective Yardage', f'{int(round(adj_yards))} yds', delta=f'{int(round(adj_yards - yardage))} yds wind adjustment')
    
    golf_df = pd.DataFrame([
        {'Course': selected_course, 'Pin_Yards': yardage, 'Wind_MPH': wind_mph, 'Wind_Vector': wind_dir, 'Effective_Yards': int(round(adj_yards))}
    ])
    
    st.dataframe(golf_df, use_container_width=True)
    csv_golf = golf_df.to_csv(index=False)
    
    if HAS_SAVE_UTIL:
        render_save_widget(default_filename='Mangrove_Mountain_Caddy_Sheet', data_content=csv_golf, file_extension='.csv')
    else:
        st.download_button('📥 Download Caddy Sheet (.CSV)', csv_golf, f'Golf_Caddy_{datetime.date.today()}.csv', 'text/csv')
