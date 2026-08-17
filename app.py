"""
app.py

Main entry point for the Laboratory Information Management System (LIMS).
"""

import streamlit as st

st.set_page_config(
    page_title="LIMS",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🧪 Laboratory Information Management System")

# See pages/storage.py for why this marker exists -- it lets that
# page detect whether the user just navigated in from elsewhere.
st.session_state["_active_page_marker"] = "home"

st.markdown(
    """
Welcome to the new **LIMS**.

This system will let you manage:

- 📦 Sample storage
- 🧬 DNA
- 🧫 Proteins
- 🧪 Reagents
- 📋 Orders
- 👥 Users

Select a module from the sidebar menu to get started.
"""
)

st.divider()

st.subheader("Project status")

st.success("✔ SQLite database created")
st.success("✔ Project architecture created")
st.success("✔ Storage Engine implemented")

st.info("Next goal: Storage box registration and management.")