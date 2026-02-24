# Authy — FastAPI Example

## Quick start

```bash
pip install -e ../../python       # install Authy from repo
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000

**Test accounts:**

| Username | Password |
|---|---|
| alice | password123 |
| bob | letmein |

## Project structure

```
fastapi-app/
├── main.py          ← FastAPI app: all routes
├── auth.py          ← AuthManager singleton + get_current_user dependency
├── static/
│   └── index.html   ← demo UI
├── requirements.txt
└── .env.example
```

## Routes

| Method | Path | Auth required | Description |
|---|---|---|---|
| `GET` | `/` | No | Demo UI |
| `POST` | `/auth/login` | No | Local login |
| `GET` | `/auth/google` | No | Start Google OAuth |
| `GET` | `/auth/google/callback` | No | Google callback |
| `GET` | `/auth/m365` | No | Start M365 OAuth |
| `GET` | `/auth/m365/callback` | No | M365 callback |
| `POST` | `/auth/logout` | No | Clear cookie |
| `GET` | `/api/me` | Yes (`CurrentUser`) | Return JWT payload |
| `GET` | `/api/providers` | No | List active providers |

## Protecting your own endpoints

```python
from auth import CurrentUser

@app.get("/api/secret")
async def secret(user: CurrentUser):
    return {"message": f"Hello, {user['name']}!"}
```

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
- `http://localhost:8000/auth/google/callback`
- `http://localhost:8000/auth/m365/callback`
