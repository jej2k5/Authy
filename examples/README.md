# Authy — Working Examples

Each directory is a self-contained, runnable application.

| Example | Stack | Run command |
|---|---|---|
| [`express-app/`](express-app/) | Node.js + TypeScript + Express | `npm install && npm run dev` |
| [`nextjs-app/`](nextjs-app/) | Next.js 14 (App Router) | `npm install && npm run dev` |
| [`fastapi-app/`](fastapi-app/) | Python + FastAPI + Uvicorn | `pip install -r requirements.txt && uvicorn main:app --reload` |
| [`flask-app/`](flask-app/) | Python + Flask 3 | `pip install -r requirements.txt && flask run` |
| [`streamlit-app/`](streamlit-app/) | Python + Streamlit | `pip install -r requirements.txt && streamlit run app.py` |

## First steps (all examples)

1. Install Authy from this repo:
   ```bash
   # TypeScript examples
   npm install     # package.json references ../../typescript via file:

   # Python examples
   pip install -e ../../python
   ```

2. Copy `.env.example` to `.env` and set `JWT_SECRET`.

3. Start the app — see the table above.

4. Log in with a test account:
   - Username: `alice`  Password: `password123`
   - Username: `bob`    Password: `letmein`

## Enabling OAuth providers

All examples check for OAuth credentials at startup and silently skip providers
whose env vars are missing. To enable Google or M365:

```ini
# Google
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx

# Microsoft 365
M365_CLIENT_ID=xxx
M365_CLIENT_SECRET=xxx
M365_TENANT_ID=xxx
```

Callback URLs to register (replace `localhost:PORT` with your domain in production):

| Provider | Express | Next.js | FastAPI | Flask |
|---|---|---|---|---|
| Google | `:3000/auth/google/callback` | `:3000/api/auth/google/callback` | `:8000/auth/google/callback` | `:5000/auth/google/callback` |
| M365 | `:3000/auth/m365/callback` | `:3000/api/auth/m365/callback` | `:8000/auth/m365/callback` | `:5000/auth/m365/callback` |
