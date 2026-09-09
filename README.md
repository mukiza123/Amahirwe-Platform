# Amahirwe

**Discover • Connect • Grow**

Amahirwe is a digital platform that helps students in rural public schools in Rwanda discover their talents and connect with mentors, teachers and opportunities.

This is a university final software prototype built from scratch with:

- **Frontend:** HTML5, CSS3, vanilla JavaScript (no frameworks)
- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy, Alembic
- **Database:** PostgreSQL

> Project status: **Phase 1 — Foundation** (folder structure, FastAPI app, database wiring, design system, base pages). Authentication, dashboards, the talent assessment, mentor matching, opportunities and admin tools are built out in the phases that follow — see [Development Plan](#development-plan) below.

## Live demo

- App URL: _to be added once deployed to Vercel_
- SRS document: `Lisette_Mukiza_Assignment2_07302026.pdf` (in this repo)

## Demo accounts

_Not yet available — seed data is added in a later phase. This section will list a demo student, teacher, mentor, opportunity provider and administrator account once `database/seed.py` is implemented._

## Project structure

```
Amahirwe-Platform/
├── backend/                 FastAPI application
│   ├── app/
│   │   ├── main.py          App entry point, CORS, health check
│   │   ├── core/            Settings, DB session/engine
│   │   ├── models/          SQLAlchemy models (added per phase)
│   │   ├── schemas/         Pydantic request/response schemas
│   │   ├── api/             API routers
│   │   └── services/        Business logic (e.g. matching algorithm)
│   ├── alembic/              Database migrations
│   ├── requirements.txt
│   └── .env.example
├── frontend/                 Static HTML/CSS/JS site
│   ├── index.html, login.html, register.html
│   ├── student/ teacher/ mentor/ provider/ admin/   Role dashboards
│   ├── css/                  style.css, components.css, responsive.css
│   ├── js/                   api.js, auth.js, main.js, ...
│   ├── locales/               en.json, rw.json, fr.json
│   └── assets/                illustrations, icons, images
├── database/seed.py          Demo data seed script
├── tests/                    Backend tests (pytest)
├── api/index.py              Vercel entry point (re-exports the FastAPI app)
└── vercel.json                Deployment configuration
```

## Prerequisites

- Python 3.9 or newer
- A PostgreSQL database. This project uses a free hosted instance from [Neon](https://neon.tech) — no local PostgreSQL install required.
- A modern web browser
- A simple static file server for the frontend (instructions below use Python's built-in one, so nothing extra to install)

## Setup — running the project locally

Follow these steps in order.

### 1. Clone the repository

```bash
git clone <this-repo-url>
cd Amahirwe-Platform
```

### 2. Create a free PostgreSQL database (Neon)

1. Go to [neon.tech](https://neon.tech) and sign up for a free account.
2. Create a new project (any name, e.g. `amahirwe`).
3. On the project dashboard, copy the **connection string** shown (it looks like `postgresql://user:password@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require`).
4. Keep this connection string — you'll paste it into `.env` in the next step.

### 3. Configure backend environment variables

```bash
cd backend
cp .env.example .env
```

Open `backend/.env` and set:

- `DATABASE_URL` — paste the Neon connection string from step 2.
- `JWT_SECRET_KEY` — generate one with:
  ```bash
  python3 -c "import secrets; print(secrets.token_hex(32))"
  ```

Never commit `backend/.env` — it's already in `.gitignore`.

### 4. Create a virtual environment and install backend dependencies

```bash
# from backend/
python3 -m venv venv
source venv/bin/activate          # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Run database migrations

```bash
# from backend/, with venv activated
alembic upgrade head
```

### 6. Start the backend API

```bash
# from backend/, with venv activated
uvicorn app.main:app --reload --port 8000
```

The API is now running at `http://127.0.0.1:8000`. Confirm it works by opening:

- `http://127.0.0.1:8000/api/health` → should return `{"status":"ok","service":"Amahirwe API"}`
- `http://127.0.0.1:8000/docs` → interactive API documentation

### 7. Start the frontend (in a second terminal)

The frontend is plain HTML/CSS/JS, so it just needs to be served as static files (opening the HTML files directly with `file://` will break the API calls and JS modules).

```bash
# from the project root, in a new terminal
python3 -m http.server 5500
```

Then open:

```
http://127.0.0.1:5500/frontend/index.html
```

The frontend automatically talks to the backend at `http://127.0.0.1:8000/api` when running locally like this.

### 8. Run backend tests (optional)

```bash
cd backend
source venv/bin/activate
cd ..
pytest tests/ -v
```

## Development plan

Built in phases, per the project's development rule of not building everything at once:

1. **Foundation** — folder structure, FastAPI, PostgreSQL/SQLAlchemy/Alembic wiring, design system, base pages, Vercel config *(current)*
2. **Authentication** — registration, login, JWT, role-based access, protected pages
3. **Student** — dashboard, profile, talent assessment, results
4. **Offline assessment** — service worker, IndexedDB sync queue
5. **Teacher** — dashboard, students, mentor match approvals
6. **Mentor matching** — rule-based matching algorithm, approval workflow, audit log, notifications
7. **Opportunities** — provider dashboard, opportunity creation, listing, filtering
8. **Admin** — user management, verification, audit logs
9. **Multilingual** — Kinyarwanda, English, French across all screens
10. **Polish** — mobile QA, accessibility, loading/empty/error states, illustrations

## Design system

Amahirwe uses a **controlled neumorphism** design language: soft shadows and raised/pressed states on cards, buttons and inputs, kept subtle and used only where it aids usability — not on every element. Brand colours (primary dark green `#0F6B52`, teal `#1A9B8A`, mint, warm yellow/orange accents), typography (Plus Jakarta Sans for headings, Inter for body) and spacing/radius scales are defined as CSS custom properties in `frontend/css/style.css`.

## Security notes

- Passwords are hashed (never stored in plaintext).
- Authentication uses JWT; the backend enforces role-based authorization — the frontend never decides access on its own.
- Because Amahirwe's primary users are minors, there is no direct/unsupervised messaging between students and mentors. A teacher or administrator must approve a mentor match before any contact information is shared.
- Mentors and opportunity providers must be verified by an administrator before they can appear in matches or publish opportunities.

## License

Educational prototype built for a university capstone project. Not for production use.
