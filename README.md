# AI Code Review Assistant

## Local development

Install Python dependencies from `backend/requirements.txt` and frontend dependencies from `frontend/package.json`, then run `python run.py` from the repository root. The launcher serves the built frontend and starts the API in local development mode. In this mode, API identity headers and the local developer sign-in are enabled for local use only.

On Windows, run `setup.bat` once to create `.venv` and install Python and npm dependencies. Then run `run.bat` to start the app at `http://localhost:8000`. Setup requires Python 3.10 or newer (3.11 recommended), Node.js 18 or newer, npm, and an internet connection to download dependencies.

Set `REACT_APP_CLERK_PUBLISHABLE_KEY` in `frontend/.env` to use Clerk sign-in. Without a Clerk key, the app offers a local development sign-in; it does not verify passwords and must not be exposed to a network.

Uploaded projects, files, and vector indexes are stored in separate workspaces for each account. Existing data from older shared-index installs remains in the legacy folders and is not automatically assigned to an account.

## Production and Docker

Production requires a Clerk session token verifier. Set these values in `backend/.env`:

```dotenv
APP_ENV=production
CLERK_ISSUER=https://your-instance.clerk.accounts.dev
CLERK_JWKS_URL=https://your-instance.clerk.accounts.dev/.well-known/jwks.json
CORS_ALLOWED_ORIGINS=https://your-app.example.com
GROQ_API_KEY=your-groq-api-key
```

Use the issuer and JWKS URL shown for your Clerk instance, and set `CORS_ALLOWED_ORIGINS` to the exact HTTPS origin serving the frontend. Set the Clerk publishable key in `frontend/.env` before building so the browser can sign in and send its session token. Do not commit secret environment files. Docker Compose passes `APP_ENV=production` and reads `backend/.env` when present; use Docker Compose v2.24 or newer for the optional env-file setting.
