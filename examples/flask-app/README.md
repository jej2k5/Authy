# Authy — Flask Example

## Quick start

```bash
pip install -e ../../python       # install Authy from repo
pip install -r requirements.txt
cp .env.example .env
flask run --port 5000
```

Open http://localhost:5000

**Test accounts:**

| Username | Password |
|---|---|
| alice | password123 |
| bob | letmein |

## Project structure

```
flask-app/
├── app.py           ← Flask app: all routes
├── auth.py          ← AuthManager singleton + require_auth decorator
├── static/
│   └── index.html   ← demo UI
├── requirements.txt
└── .env.example
```

## Routes

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/` | No | Demo UI |
| `POST` | `/auth/login` | No | Local login |
| `GET` | `/auth/google` | No | Start Google OAuth |
| `GET` | `/auth/google/callback` | No | Google callback |
| `GET` | `/auth/m365` | No | Start M365 OAuth |
| `GET` | `/auth/m365/callback` | No | M365 callback |
| `POST` | `/auth/logout` | No | Clear cookie |
| `GET` | `/api/me` | Yes | Return JWT payload |
| `GET` | `/api/providers` | No | List active providers |

## Protecting your own routes

```python
from auth import require_auth
from flask import g

@app.get("/dashboard")
@require_auth
def dashboard():
    return f"Hello, {g.user['name']}!"
```

## Note on async

Flask's standard WSGI mode is synchronous. The `run_async()` helper in
`auth.py` calls `asyncio.run()` for each Authy call. This is fine for
typical web apps. For high-concurrency workloads consider using `flask[async]`
(which requires `asgiref`) or switching to FastAPI.

## Enable OAuth

```ini
# .env
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx

M365_CLIENT_ID=xxx
M365_CLIENT_SECRET=xxx
M365_TENANT_ID=xxx
```

Callback URLs:
- `http://localhost:5000/auth/google/callback`
- `http://localhost:5000/auth/m365/callback`
