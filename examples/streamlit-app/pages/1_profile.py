"""
Profile page — demonstrates the login gate in a multi-page Streamlit app.

Every page in pages/ calls require_login() at the top.
The gate is instant if the user is already authenticated.
"""
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from auth import logout, require_login

st.set_page_config(page_title="Profile — Authy Demo", page_icon="👤")
require_login()

user = st.session_state.user

st.title("Profile")

with st.form("profile_form"):
    st.text_input("Name",  value=user.get("name", ""),  disabled=True)
    st.text_input("Email", value=user.get("email", ""), disabled=True)
    st.text_input("Provider", value=user.get("provider", ""), disabled=True)
    st.form_submit_button("Edit profile (demo — no-op)", disabled=True)

st.divider()
if st.button("Sign out"):
    logout()
