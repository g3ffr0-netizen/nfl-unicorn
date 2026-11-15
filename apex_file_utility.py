# =====================================================================
# APEX FILE UTILITY & BROWSER DOWNLOAD MODULE (apex_file_utility.py)
# =====================================================================

import os
import re
import streamlit as st

def render_apex_file_utility():
    """Renders the Apex File Utility & Browser Download interface."""
    st.header("📂 Secure File Generator & Local Download Utility")
    st.markdown("Create, edit, and download files directly to your Windows PC.")

    col1, col2 = st.columns([3, 1])
    with col1:
        f_name = st.text_input("File Name", "Kaggle_Submission", key="apex_util_name")
    with col2:
        f_ext = st.selectbox("Extension", [".py", ".txt", ".md", ".csv", ".json"], key="apex_util_ext")

    f_content = st.text_area(
        "File Content Editor",
        height=280,
        placeholder="Type or paste your code or data here...",
        key="apex_util_content"
    )

    if f_name.strip() and f_content.strip():
        ext = f_ext.strip()
        if not ext.startswith("."):
            ext = "." + ext

        clean_name = re.sub(r'[<>:"/\\|?*]', '_', f_name).strip() or "untitled_file"
        filename = f"{clean_name}{ext}"

        mime_map = {
            ".py": "text/x-python",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".csv": "text/csv",
            ".json": "application/json"
        }
        mimetype = mime_map.get(ext, "text/plain")

        chars = len(f_content)
        lines = f_content.count("\n") + 1
        st.caption(f"📊 Ready: `{filename}` | {chars:,} characters | {lines:,} lines")

        st.download_button(
            label=f"📥 Download {filename} to My PC",
            data=f_content,
            file_name=filename,
            mime=mimetype,
            use_container_width=True,
            key="apex_util_download_btn"
        )
    else:
        st.info("💡 Enter a file name and content above to activate the direct PC download button.")

if __name__ == "__main__":
    st.set_page_config(page_title="Apex File Utility", page_icon="📂", layout="wide")
    render_apex_file_utility()
