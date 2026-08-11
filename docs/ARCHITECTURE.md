# 5edma.tn — Architecture

5edma.tn is a Tunisian gig/services marketplace with three roles: **worker**, **client**,
and **admin**. The original UML (`UML/`) documents identity, verification, messaging,
reviews, wallet and subscriptions. The platform supports **two independent ways for a
client and worker to end up working together** — both are intentional, current features,
not duplicates to be merged.

## Flow 1 — Jobs & Applications (`backend/app/jobs.py`)

The client describes a one-off need; workers apply; the client picks one.

```
Client → POST /jobs                       create a job offer (open)
Worker → POST /jobs/{id}/apply             submit an application
Client → GET  /jobs/{id}/applications      review applicants
Client → POST /jobs/{id}/applications/{app_id}/accept
Client → POST /jobs/{id}/complete          close the job out
```

Tables: `job_offers`, `job_applications`. This is the flow the original ERD/class
diagram describes (`Job` + `Application`), with two renames: `Job` → `job_offers`,
`Application` → `job_applications` (SQLAlchemy reserves cleaner names for the ORM
classes: `JobOffer`, `JobApplication`).

Boosting a job (`POST /subscriptions/boost-job`) extends `job_offers.boost_until`,
which `GET /jobs` uses to rank boosted listings first.

## Flow 2 — Services & Bookings (`backend/app/service.py`, `backend/app/bookings.py`)

The worker publishes a standing, fixed-price service; a client books a specific slot
directly, no application/acceptance step.

```
Worker → POST /services                   publish a bookable service
Client → GET  /services                   browse the catalog
Client → POST /bookings                   book a service (status=pending)
Worker → POST /bookings/{id}/confirm       accept the booking
Worker → POST /bookings/{id}/complete      mark it done
```

Tables: `services`, `bookings`. This flow is **not** in the original ERD — it was
added after the initial design to cover workers who sell a repeatable, fixed-price
service (e.g. "AC cleaning — 60 TND") rather than bidding on client-posted jobs.

## Reviews span both flows

`reviews.py` has two independent pairs of endpoints — `/reviews/bookings/{id}/review-as-*`
and `/reviews/jobs/{job_id}/applications/{id}/review-as-*` — because a completed
interaction can come from either flow. `reviews.booking_id` and
`reviews.job_application_id` are both nullable FKs; exactly one is set per review.

## Shared systems

- **Wallet & transactions** (`wallet.py`): a single wallet per user regardless of role.
  Top-ups are self-reported by the user and require admin approval
  (`POST /wallet/admin/transactions/{id}/approve`) — there's no live payment gateway
  integration yet (D17/Flouci in the use-case diagram are aspirational; wiring one in
  requires merchant credentials from that provider).
- **Verification** (`admin.py`, `auth.py`): `worker_profiles.status` /
  `client_profiles.status` (`pending` / `approved` / `rejected`) gate the
  `get_verified_worker` / `get_verified_client` dependencies that most write endpoints
  require. ID photos are stored as files under `uploads/user_<id>/` (git-ignored —
  never commit real ID photos) rather than in their own DB table; there's no separate
  `id_documents` table tracking review history the way the ERD sketches one, so if you
  need an audit trail of resubmissions that's a real gap to fill later, not something
  half-wired today.
- **Chat** (`chat.py`): REST history (`GET /chat/history/{job_id}`) + a WebSocket
  (`/chat/ws?token=<jwt>`) for live push. The socket authenticates via the same JWT as
  the REST API — identity is derived from the token, never from a client-supplied id.
- **AI generation** (`ai.py`): bio/job-description text via Groq
  (`llama-3.3-70b-versatile`). Falls back to a mock string if `GROQ_API_KEY` is unset
  or the call fails, so the rest of the app keeps working without it.

## Database

MySQL (`aiomysql` driver at runtime, `PyMySQL` for synchronous Alembic migrations).
`backend/database/schema.sql` is the canonical schema for a direct `mysql < schema.sql`
import; `backend/migrations/versions/0001_initial_schema.py` is the equivalent Alembic
baseline for `alembic upgrade head`. Both are hand-kept in sync with the SQLAlchemy
models in `backend/app/*.py` — the models are the source of truth.

## Frontend

`frontend/` (Next.js, App Router) is the one true frontend. It's a client-heavy app —
almost every page is a client component driven by `AuthContext` (`contexts/AuthContext.tsx`)
plus a thin fetch wrapper (`lib/api.ts`) that attaches the JWT and normalizes error
shapes. `lib/hooks.ts`'s `useRequireAuth()` is the role-gate used on authenticated-only
pages; the job/service listing and detail pages deliberately *don't* use it — the
backend allows anonymous access to open jobs/active services (see below), so those
pages render for guests too, with a login prompt gating only the actual apply/book
action. An earlier Vite/React prototype (`5edma-frontend/`) explored the same screens
and is kept on disk for reference but is not tracked in git.

**Tailwind is v4** — `app/globals.css` must start with `@import "tailwindcss";`, not
the v3 `@tailwind base/components/utilities` directives. Using the v3 syntax compiles
without error but silently drops every utility class site-wide; this actually happened
during development and was only caught by rendering the app in a browser, not by
`next build` or `tsc`. If a future refactor of `globals.css` results in an unstyled
app that still builds cleanly, check this first.

## Security & ops hardening

- **Rate limiting**: `/auth/login`, `/auth/register`, `/auth/register/simple` are
  limited to 10 requests/minute/IP via `slowapi` (`app/rate_limit.py`). The limiter
  state is in-process — fine for one instance, not shared across replicas without
  pointing it at Redis.
- **Security headers & logging**: a single middleware in `app/main.py` adds baseline
  headers (`X-Frame-Options`, `nosniff`, HSTS in production), tags every request with
  a correlation id, and logs method/path/status/duration. A global exception handler
  guarantees clients never see a raw stack trace; full details still go to the server
  log.
- **CORS** is driven by `ALLOWED_ORIGINS` (comma-separated) instead of a hardcoded
  list; interactive docs (`/docs`, `/redoc`) are disabled when `ENVIRONMENT=production`.
- **DB connections** use `pool_pre_ping` + `pool_recycle=1800` so an idle MySQL
  connection reconnects transparently instead of surfacing as a 500 on the next
  request. SQL echo logging is tied to `DEBUG`, off by default in production.
- Two real bugs were caught specifically by testing against the live database rather
  than relying on code review: `admin.verify_worker` updated `WorkerProfile.verified`
  but not `.status`, and every worker-gated endpoint actually checks `.status` — so
  approving a worker silently did nothing. And the multipart `/auth/register` endpoint
  accepted `role=admin` directly, letting anyone self-register an administrator
  account. Both are fixed and covered by regression tests.

## Testing

`backend/tests/` has two tiers:
- Automated pytest suite (`test_auth.py`, `test_admin.py`, `test_jobs.py`,
  `test_wallet.py`) — runs against an in-memory SQLite database via a `get_db`
  dependency override (see `conftest.py`), no external services required. On Windows,
  `conftest.py` forces the Selector event loop policy because `aiosqlite` deadlocks
  on connection teardown under the default Proactor loop — a test-only quirk, since
  production uses a single long-lived event loop against MySQL.
- `backend/tests/manual/` — standalone scripts that need a running server and a real
  database (chat WebSocket, wallet flows). Not pytest-shaped on purpose, so `pytest`
  doesn't try to collect them.

## Deployment

`docker-compose.yml` at the repo root runs MySQL + backend + frontend together;
`backend/Dockerfile` and `frontend/Dockerfile` are both multi-stage (the frontend
builds Next.js's `output: 'standalone'` bundle to avoid shipping `node_modules` in
the image). Copy `.env.example` to `.env` at the repo root before `docker compose up`.
