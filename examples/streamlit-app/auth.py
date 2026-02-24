"""
Authy AuthManager and login-gate helpers for Streamlit.

The AuthManager is cached with @st.cache_resource so it's built once and
shared across all sessions. Auth state (token, user) lives in st.session_state
which persists across re-runs for the same browser session.
"""
import asyncio
import os

import streamlit as st

from authy import AuthManager, LocalProvider, LocalProviderConfig, hash_password

# ---------------------------------------------------------------------------
# In-memory user store  (replace with DB in production)
# ---------------------------------------------------------------------------
_PASSWORD_HASH = hash_password("password123")
_BOB_HASH      = hash_password("letmein")

USERS = {
    "alice": {"id": "1", "email": "alice@example.com", "name": "Alice", "password_hash": _PASSWORD_HASH},
    "bob":   {"id": "2", "email": "bob@example.com",   "name": "Bob",   "password_hash": _BOB_HASH},
}


async def _find_user(username: str):
    return USERS.get(username)


def run_async(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# AuthManager singleton — cached across Streamlit re-runs
# ---------------------------------------------------------------------------
@st.cache_resource
def get_auth_manager() -> AuthManager:
    secret = os.environ.get("JWT_SECRET", "change-me")
    manager = AuthManager(jwt_secret=secret)
    manager.register(LocalProvider(
        LocalProviderConfig(jwt_secret=secret, token_ttl=3600 * 8),
        _find_user,
    ))
    return manager


# ---------------------------------------------------------------------------
# require_login()
#
# Call at the top of any page. Renders a login form and halts the script
# (st.stop()) until the user authenticates. On success it stores the token
# and decoded payload in st.session_state and calls st.rerun().
# ---------------------------------------------------------------------------
def require_login():
    manager = get_auth_manager()

    # If a token exists, verify it's still valid
    if "auth_token" in st.session_state:
        try:
            st.session_state.user = manager.verify_token(st.session_state.auth_token)
            return  # Authenticated — let the page continue
        except Exception:
            # Token expired or invalid — force re-login
            st.session_state.pop("auth_token", None)
            st.session_state.pop("user", None)

    # --- Login form ---
    st.title("Sign in")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="alice", autocomplete="username")
        password = st.text_input("Password", placeholder="password123",
                                 type="password", autocomplete="current-password")
        submitted = st.form_submit_button("Sign in", use_container_width=True)

    if submitted:
        if not username or not password:
            st.error("Username and password are required.")
        else:
            result = run_async(manager.authenticate("local", {
                "username": username,
                "password": password,
            }))
            if result.success:
                st.session_state.auth_token = result.token
                st.session_state.user = manager.verify_token(result.token)
                st.rerun()
            else:
                st.error(result.error)

    st.caption("Test accounts: **alice / password123** or **bob / letmein**")
    st.stop()


# ---------------------------------------------------------------------------
# logout()  — clear session state and rerun
# ---------------------------------------------------------------------------
def logout():
    st.session_state.pop("auth_token", None)
    st.session_state.pop("user", None)
    st.rerun()
