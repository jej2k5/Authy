# Streamlit Integration Guide

**Python:** 3.11+  **Streamlit:** 1.32+

Streamlit re-runs the entire script on every user interaction. Auth state lives in
`st.session_state` which persists across re-runs for the same browser session.

## Install

```bash
pip install streamlit pyjwt python-dotenv
pip install -e ../python    # install Authy
```

## 1. AuthManager

```python
# auth.py
import asyncio, os
from authy import AuthManager, LocalProvider, LocalProviderConfig, hash_password

_password_hash = hash_password("password123")
USERS = {
    "alice": {"id": "1", "email": "alice@example.com",
              "name": "Alice", "password_hash": _password_hash},
}

async def _find_user(username: str):
    return USERS.get(username)

def get_auth_manager() -> AuthManager:
    secret = os.environ.get("JWT_SECRET", "change-me")
    manager = AuthManager(jwt_secret=secret)
    manager.register(LocalProvider(
        LocalProviderConfig(jwt_secret=secret, token_ttl=3600 * 8),  # 8-hour session
        _find_user,
    ))
    return manager

# Single instance — st.cache_resource persists across re-runs
import streamlit as st

@st.cache_resource
def auth_manager():
    return get_auth_manager()

def run_async(coro):
    return asyncio.run(coro)
```

## 2. Login gate

Call this at the top of every page. It halts rendering until the user is authenticated:

```python
# auth.py (continued)
def require_login():
    manager = auth_manager()

    if "auth_token" in st.session_state:
        # Verify token is still valid on each page load
        try:
            st.session_state.user = manager.verify_token(st.session_state.auth_token)
            return   # user is authenticated — let the page render
        except Exception:
            del st.session_state["auth_token"]   # token expired

    # --- Show login form ---
    st.title("Sign in")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")

    if submitted:
        result = run_async(manager.authenticate("local", {
            "username": username, "password": password,
        }))
        if result.success:
            st.session_state.auth_token = result.token
            st.session_state.user = manager.verify_token(result.token)
            st.rerun()
        else:
            st.error(result.error)

    st.stop()   # halt rendering until logged in
```

## 3. Main app

```python
# app.py
import streamlit as st
from auth import require_login

require_login()   # ← gate: nothing below runs until authenticated

user = st.session_state.user

st.title("My App")
st.write(f"Welcome, **{user['name']}** ({user['email']})")

if st.button("Sign out"):
    del st.session_state["auth_token"]
    del st.session_state["user"]
    st.rerun()

# --- Rest of your application ---
st.header("Dashboard")
st.write("You are now seeing authenticated content.")
```

## 4. Multi-page apps

For Streamlit multi-page apps (files in `pages/`), put the gate in each page, or
create a shared `pages/_common.py` and import it:

```
my_app/
├── app.py              # home / login
├── auth.py
└── pages/
    ├── 1_dashboard.py
    └── 2_settings.py
```

```python
# pages/1_dashboard.py
import streamlit as st
from auth import require_login     # same gate

require_login()

st.title("Dashboard")
st.write(f"Logged in as: {st.session_state.user['email']}")
```

## 5. OAuth in Streamlit

Streamlit can't directly host OAuth callback routes. The recommended pattern is to
run a small FastAPI sidecar on a separate port that handles the redirect, sets a
shared cookie or session token, and redirects back to Streamlit:

```python
# oauth_sidecar.py — run alongside Streamlit on port 8001
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
import jwt as pyjwt
from auth import auth_manager, run_async

sidecar = FastAPI()

@sidecar.get("/auth/google")
async def google_start():
    result = await auth_manager().authenticate("google", {"action": "get_auth_url"})
    meta = pyjwt.decode(result.token, options={"verify_signature": False})
    # Store verifier in a short-lived cookie
    from fastapi import Response
    resp = RedirectResponse(meta["auth_url"])
    resp.set_cookie("pkce_verifier", meta["code_verifier"], httponly=True)
    return resp

@sidecar.get("/auth/google/callback")
async def google_callback(code: str, state: str, request):
    code_verifier = request.cookies.get("pkce_verifier", "")
    result = await auth_manager().authenticate("google", {
        "action": "callback", "code": code,
        "state": state, "code_verifier": code_verifier,
    })
    # Pass the JWT to Streamlit via query param (Streamlit reads st.query_params)
    return RedirectResponse(f"http://localhost:8501/?token={result.token}")
```

```python
# app.py — pick up the token from the sidecar redirect
params = st.query_params
if "token" in params and "auth_token" not in st.session_state:
    st.session_state.auth_token = params["token"]
    st.query_params.clear()
    st.rerun()
```

## Run it

```bash
streamlit run app.py
# Open http://localhost:8501
# Username: alice   Password: password123
```

See the runnable example: [`examples/streamlit-app/`](../examples/streamlit-app/)
