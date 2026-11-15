# =====================================================================
# APEX UNIVERSAL SAVE & DOWNLOAD MODULE (apex_save_utility.py)
# =====================================================================

import re
import streamlit as st

def render_save_widget(default_filename: str, data_content: str, file_extension: str = ".csv"):
    """
    Renders a universal save/download widget for any Streamlit app module.
    Supports .csv, .txt, .json, .py, and .md formats.
    """
    st.markdown("---")
    st.subheader("💾 Export & Save Data")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        f_name = st.text_input("Export File Name", default_filename, key=f"save_name_{default_filename}")
    with col2:
        f_ext = st.selectbox("Format", [".csv", ".txt", ".json", ".md", ".py"], index=0, key=f"save_ext_{default_filename}")

    if f_name.strip() and data_content.strip():
        ext = f_ext if f_ext.startswith(".") else f".{f_ext}"
        clean_name = re.sub(r'[<>:"/\\|?*]', '_', f_name).strip() or "export_data"
        filename = f"{clean_name}{ext}"

        mime_map = {
            ".csv": "text/csv",
            ".txt": "text/plain",
            ".json": "application/json",
            ".md": "text/markdown",
            ".py": "text/x-python"
        }
        mimetype = mime_map.get(ext, "text/plain")

        st.download_button(
            label=f"📥 Download {filename} to PC",
            data=data_content,
            file_name=filename,
            mime=mimetype,
            use_container_width=True,
            key=f"download_btn_{default_filename}"
        )
    else:
        st.info("💡 Data content required to activate download.")
