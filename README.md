# 5edma.tn

A Tunisian gig/services marketplace connecting **clients** who need work done with
**workers** who offer skills or services, with an **admin** role for ID verification
and dispute handling.

- **[`backend/`](backend/)** — FastAPI + MySQL API. See [`backend/README.md`](backend/README.md) for setup.
- **[`frontend/`](frontend/)** — Next.js web app.
- **[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)** — data model, the two hiring flows
  (Jobs/Applications and Services/Bookings), and how the pieces fit together.
- **[`docs/uml/`](docs/uml/)** — use-case, class, and ERD diagrams matching the current
  system (Mermaid sources in `docs/uml/src/`, rendered SVG/PNG alongside them).
- **[`docs/RAPPORT_5edma.tn.docx`](docs/RAPPORT_5edma.tn.docx)** — rapport de projet (FR).
- **[`docs/GUIDE_TECHNIQUE_5edma.tn.docx`](docs/GUIDE_TECHNIQUE_5edma.tn.docx)** — guide
  technique d'installation et d'exploitation (FR).

## Quick start

```bash
# Backend
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # fill in DATABASE_URL / SECRET_KEY / GROQ_API_KEY
mysql -u <user> -p <database> < database/schema.sql   # or: alembic upgrade head
uvicorn main:app --reload

# Frontend
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

Or with Docker (MySQL + backend + frontend together):

```bash
copy .env.example .env   # repo root — fill in MYSQL_ROOT_PASSWORD / SECRET_KEY / GROQ_API_KEY
docker compose up --build
```
