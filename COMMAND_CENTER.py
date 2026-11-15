# =====================================================================
# INTEGRATING EXPORT & SAVE INTO RACING / NFL COMMAND MODULE
# =====================================================================

import streamlit as st
import pandas as pd
from apex_save_utility import render_save_widget

def render_racing_and_nfl_hub():
    st.header("🏁 Racing Telemetry & NFL ELO Hub")
    st.markdown("Analyze Flemington form odds, telemetry data, and NFL fixtures with instant PC export.")

    # Example Datasets (Replace with your actual pandas DataFrames or analysis strings)
    racing_data = pd.DataFrame({
        "Horse_Name": ["Apex Runner", "Thunder Bolt", "Sovereign Flame"],
        "Flemington_Odds": [4.20, 6.50, 2.10],
        "Form_Rating": [92, 88, 95]
    })

    st.subheader("🐴 Flemington Form Analysis Grid")
    st.dataframe(racing_data, use_container_width=True)

    # --- ADD THE SAVE & EXPORT WIDGET HERE ---
    # Converts your DataFrame to CSV and triggers the download button
    racing_csv = racing_data.to_csv(index=False)
    render_save_widget(
        default_filename="Flemington_Racing_Form_Export",
        data_content=racing_csv,
        file_extension=".csv"
    )
