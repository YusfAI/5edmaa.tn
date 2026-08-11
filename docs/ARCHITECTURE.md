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

## Frontends

`frontend/` (Next.js) is the one being built out. An earlier Vite/React prototype
(`5edma-frontend/`) explored the same screens and is kept on disk for reference but is
not tracked in git and not being developed further.
