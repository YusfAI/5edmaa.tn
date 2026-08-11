# 5edma.tn — Backend

FastAPI + MySQL backend for 5edma.tn, a Tunisian gig/services marketplace connecting
**clients** (who need work done) with **workers** (who offer skills/services), with an
**admin** role for ID verification and dispute handling. See [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md)
for the data model and the two hiring flows the platform supports.

## Stack

- FastAPI (async), SQLAlchemy 2.0 (async), Alembic migrations
- MySQL (`aiomysql` driver at runtime, `PyMySQL` for synchronous Alembic migrations)
- JWT auth (`python-jose`), password hashing via `passlib` (pbkdf2_sha256)
- Groq (Llama models) for AI-assisted bio / job-description generation

## Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

copy .env.example .env       # then fill in DATABASE_URL / SECRET_KEY / GROQ_API_KEY

# Load the schema — either one:
mysql -u <user> -p <database> < database/schema.sql
alembic upgrade head

uvicorn main:app --reload
```

The API is served at `http://localhost:8000`, interactive docs at `/docs`.

## Environment variables

See [`.env.example`](.env.example). `SECRET_KEY` should be a long random value
(`python -c "import secrets; print(secrets.token_urlsafe(48))"`), never reused across
environments. `.env` is git-ignored — never commit it.

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | *(required)* | SQLAlchemy connection string |
| `SECRET_KEY` | *(required)* | JWT signing key |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Token lifetime |
| `GROQ_API_KEY` | *(unset)* | AI bio/description generation; falls back to a mock string if unset |
| `ENVIRONMENT` | `development` | `production` disables `/docs`, `/redoc`, tightens defaults |
| `DEBUG` | tied to `ENVIRONMENT` | Toggles SQL echo logging and verbose validation error bodies |
| `ALLOWED_ORIGINS` | localhost dev ports | Comma-separated CORS allow-list |
| `RATE_LIMIT_ENABLED` | `true` | Disable only for local load-testing |

## Project layout

```
backend/
  app/
    main.py             FastAPI app, middleware, exception handlers, router registration
    config.py           Settings loaded from .env
    database.py         Async SQLAlchemy engine/session
    rate_limit.py        Shared slowapi Limiter instance
    user.py              User, WorkerProfile, ClientProfile models
    auth.py              Registration, login, JWT, role dependencies
    jobs.py              Job postings + applications (client posts, worker applies)
    service.py           Worker services catalog (fixed-price listings)
    bookings.py          Bookings against services (client books directly)
    reviews.py           Reviews for both jobs and bookings
    wallet.py            Wallet balance + transactions (manual top-up/withdrawal, admin-approved)
    subscriptions.py     Premium plans, job boosts
    chat.py              Messaging + WebSocket push
    admin.py             Worker/client verification queue
    ai.py                Groq-backed bio / job description generation
  database/
    schema.sql           Canonical MySQL schema, safe to import directly
  migrations/            Alembic migrations
  tests/                 Automated pytest suite (in-memory SQLite)
  tests/manual/           Standalone scripts needing a live server/DB — not pytest-shaped
  uploads/                Local file storage for ID photos (git-ignored, PII)
```

## Tests

```bash
pytest
```

Runs against an in-memory SQLite database (see `tests/conftest.py`) — no MySQL or
`.env` required. `tests/manual/` scripts are separate (need a running server + real DB).

## Docker

```bash
docker compose up --build   # from the repo root; copy .env.example to .env first
```

Runs MySQL + backend + frontend together. `backend/Dockerfile` and
`docker-compose.yml` are also usable independently of the frontend if you only need
the API.
