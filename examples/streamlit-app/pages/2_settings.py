"""
Settings page — another example of a protected page.
"""
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from auth import require_login

st.set_page_config(page_title="Settings — Authy Demo", page_icon="⚙️")
require_login()

user = st.session_state.user

st.title("Settings")
st.write(f"Logged in as **{user['name']}** — only authenticated users can see this page.")

st.subheader("Notification preferences")
st.checkbox("Email notifications", value=True)
st.checkbox("Weekly digest", value=False)
st.button("Save (demo — no-op)", disabled=True)
