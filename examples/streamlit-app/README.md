# Authy — Streamlit Example

A Streamlit app with a login gate and three protected pages.

## Quick start

```bash
pip install -e ../../python       # install Authy from repo
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

Open http://localhost:8501

**Test accounts:**

| Username | Password |
|---|---|
| alice | password123 |
| bob | letmein |

## Project structure

```
streamlit-app/
├── app.py               ← Dashboard (home page) — protected
├── auth.py              ← AuthManager + require_login() + logout()
├── pages/
│   ├── 1_profile.py     ← Profile page — protected
│   └── 2_settings.py    ← Settings page — protected
├── requirements.txt
└── .env.example
```

## How it works

### `auth.py`

| Symbol | Purpose |
|---|---|
| `get_auth_manager()` | `@st.cache_resource` singleton — built once, shared across all sessions |
| `require_login()` | Call at top of every page; shows login form and `st.stop()` until authenticated |
| `logout()` | Clears `st.session_state` and calls `st.rerun()` |

### Session state keys

| Key | Value |
|---|---|
| `st.session_state.auth_token` | Raw JWT string |
| `st.session_state.user` | Decoded JWT payload dict |

### Auth flow

```
Page loads
  └─ require_login()
       ├─ auth_token in session_state?
       │    ├─ Yes → verify_token() → still valid? → return (page renders)
       │    │                      → expired?      → clear + show form
       │    └─ No  → show login form → st.stop()
       │                ↓ user submits
       │           authenticate('local', creds)
       │                ↓ success
       │           store token + user → st.rerun()
```

## Multi-page pattern

Every page in `pages/` calls `require_login()` at the top. This is the
recommended approach — it's two lines and handles token expiry automatically:

```python
from auth import require_login
require_login()
# rest of page...
```

## Adding OAuth to Streamlit

Streamlit can't serve OAuth callback routes directly. Run a small FastAPI sidecar
on port 8001 (see `docs/streamlit.md` for a full example) that handles the OAuth
redirect and passes the resulting JWT to Streamlit via `st.query_params`.
