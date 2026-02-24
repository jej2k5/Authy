"""
Authy Streamlit example — single-page app.

Run:
    pip install -r requirements.txt
    pip install -e ../../python
    cp .env.example .env
    streamlit run app.py

Then open http://localhost:8501
"""
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from auth import logout, require_login

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Authy Streamlit Example", page_icon="🔐")

# ---------------------------------------------------------------------------
# Auth gate — nothing below this line runs until the user is signed in
# ---------------------------------------------------------------------------
require_login()

# ---------------------------------------------------------------------------
# Authenticated content
# ---------------------------------------------------------------------------
user = st.session_state.user

# Sidebar
with st.sidebar:
    st.header("Session")
    st.write(f"**{user['name']}**")
    st.write(user["email"])
    st.caption(f"Provider: `{user['provider']}`")
    st.divider()
    if st.button("Sign out", use_container_width=True):
        logout()

# Main content
st.title("Dashboard")
st.success(f"Welcome back, **{user['name']}**!")

col1, col2, col3 = st.columns(3)
col1.metric("User ID", user["sub"])
col2.metric("Provider", user["provider"].upper())
col3.metric("Email", user["email"])

st.divider()

with st.expander("JWT payload (decoded)"):
    st.json(user)

st.subheader("What's happening")
st.markdown("""
1. `require_login()` in `auth.py` checked `st.session_state` for a valid token.
2. The JWT was verified with `AuthManager.verify_token()` — if expired, the login
   form is shown again automatically.
3. Your app code only runs after the user has authenticated.
4. The token survives page re-runs and navigation within the same browser session.
""")
