# =====================================================================
# APEX FILE UTILITY & BROWSER DOWNLOAD MODULE (apex_file_utility.py)
# Save inside your repository folder
# =====================================================================

import os
import re
import shutil
from datetime import datetime
import streamlit as st

def render_apex_file_utility():
    """Renders the Apex File Utility & Browser Download interface."""
    st.header("📂 Secure File Generator & Local Download Utility")
    st.markdown("Create, edit, and download files directly to your Windows PC (`Downloads` or your workspace folder).")

    col1, col2 = st.columns([3, 1])
    with col1:
        f_name = st.text_input("File Name", "Kaggle_Submission", key="apex_util_name")
    with col2:
        f_ext = st.selectbox("Extension", [".py", ".txt", ".md", ".csv", ".json"], key="apex_util_ext")

    f_content = st.text_area(
        "File Content Editor",
        height=280,
        placeholder="Type or paste your code, patent spec, or racing telemetry data here...",
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
```[cite: 3]

You can commit this directly to your [nfl-unicorn](https://github.com/g3ffr0-netizen/nfl-unicorn) GitHub repository via your [new file page](https://github.com/) or your local git terminal[cite: 3]. Let me know if you need any of the other protocol scripts, legend! ☕️💻🪿🔥
