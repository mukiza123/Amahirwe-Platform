# Amahirwe

**Discover • Connect • Grow**

Amahirwe is a digital platform that helps students in rural public schools in Rwanda discover their talents and connect with mentors, teachers and opportunities.

This is a university final software prototype built from scratch with:

- **Frontend:** HTML5, CSS3, vanilla JavaScript (no frameworks)
- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy, Alembic
- **Database:** PostgreSQL

> Project status: **All 10 phases complete.** Registration/login, student profile and talent assessment (with offline support), teacher tools, mentor matching (with a no-contact-before-approval safeguard), opportunities, admin user management, multilingual support (Kinyarwanda/English/French), and a mobile/accessibility/illustration polish pass are all working end to end, backend and frontend. See [Development Plan](#development-plan) below for the remaining known gap (JS-rendered dynamic dashboard content is not yet translated).

## Live demo

- App URL: _to be added once deployed to Vercel_
- SRS document: `Lisette_Mukiza_Assignment2_07302026.pdf` (in this repo)

## Demo accounts

Run `database/seed.py` (see setup steps below) to create these. Password for all of them: `password123`.

| Role | Email | What's seeded for them |
|---|---|---|
| Student | `student@amahirwe.demo` | Profile at Nyagatare Secondary School, a completed talent assessment, and a pending mentor match awaiting the teacher's review |
| Teacher | `teacher@amahirwe.demo` | Profile at the same school, so they see the student above and can approve/reject their pending match |
| Mentor | `mentor@amahirwe.demo` | Verified profile with technology/leadership expertise, matched to the student above |
| Opportunity provider | `provider@amahirwe.demo` | Verified account with one posted opportunity |
| Administrator | `admin@amahirwe.demo` | Can list/verify/deactivate users and view the audit log |
| Parent / guardian | `parent@amahirwe.demo` | Account only; parent dashboard is not yet built |

All five built-out roles (student, teacher, mentor, provider, admin) have working dashboards wired to the real API.

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
- A PostgreSQL database. This project uses a free hosted instance from [Neon](https://neon.tech), so no local PostgreSQL install is required.
- A modern web browser
- A simple static file server for the frontend (instructions below use Python's built-in one, so nothing extra to install)

## Setup: Running the Project Locally

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
4. Keep this connection string; you'll paste it into `.env` in the next step.

### 3. Configure backend environment variables

```bash
cd backend
cp .env.example .env
```

Open `backend/.env` and set:

- `DATABASE_URL`: paste the Neon connection string from step 2.
- `JWT_SECRET_KEY`: generate one with:
  ```bash
  python3 -c "import secrets; print(secrets.token_hex(32))"
  ```

Never commit `backend/.env`; it's already in `.gitignore`.

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

### 6. Load demo data (optional)

```bash
# from backend/, with venv activated
python ../database/seed.py
```

Creates the [demo accounts](#demo-accounts) above, plus one completed talent assessment for the demo student. Safe to re-run; it skips anything that already exists.

### 7. Start the backend API

```bash
# from backend/, with venv activated
uvicorn app.main:app --reload --port 8000
```

The API is now running at `http://127.0.0.1:8000`. Confirm it works by opening:

- `http://127.0.0.1:8000/api/health` → should return `{"status":"ok","service":"Amahirwe API"}`
- `http://127.0.0.1:8000/docs` → interactive API documentation

### 8. Start the frontend (in a second terminal)

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

### 9. Run backend tests (optional)

```bash
cd backend
source venv/bin/activate
cd ..
pytest tests/ -v
```

## Development plan

Built in phases, per the project's development rule of not building everything at once:

1. **Foundation**: folder structure, FastAPI, PostgreSQL/SQLAlchemy/Alembic wiring, design system, base pages, Vercel config ✅
2. **Authentication**: registration, login, JWT, role-based access, protected pages ✅
3. **Student**: profile and talent assessment (`/api/students`, `/api/assessments`), with a dashboard UI to complete a profile, take the assessment, and see ranked results ✅
4. **Offline assessment**: service worker precaching the app shell, IndexedDB queue for assessment answers taken with no connection, auto-sync (with a manual "Sync now" fallback) once back online ✅
5. **Teacher**: dashboard to add/view students at their school and review mentor match requests ✅
6. **Mentor matching**: rule-based matching (top talent area → verified mentor with matching expertise), teacher/admin approval workflow, audit log, in-app notifications. Mentor and student contact details are only exposed after approval, with no unsupervised contact before that ✅
7. **Opportunities**: provider dashboard to post/edit/deactivate/delete opportunities; public listing endpoint ✅
8. **Admin**: list/filter users, verify mentors and providers, activate/deactivate accounts, audit log viewer ✅
9. **Multilingual**: Kinyarwanda, English, French. Done for the marketing site, login/register, and the static chrome (headings, labels, buttons, forms) of every dashboard. JS-rendered dynamic content on dashboards (match cards, notifications, admin table rows, form validation messages) is still English-only; translating those would mean threading the translation dictionary through every render function, which is a larger follow-up, not a quick addition ✅ (dashboard chrome) / ⏳ (dynamic content)
10. **Polish**: mobile QA (390/768/1024px sweep across every dashboard, no overflow, verified visually), accessibility (skip-to-content link and `role="status"` loading state on every dashboard, matching the marketing site's existing focus-visible and semantic-landmark conventions), loading/empty/error states (every dashboard shows a loading spinner, a real error message on failure, and an illustrated empty state rather than nothing), and illustrations (the provided character/object/system artwork is now used in the student assessment intro, the offline sync banner, and the teacher/mentor/provider empty states, instead of generic icons) ✅

## Design system

Amahirwe uses a **controlled neumorphism** design language: soft shadows and raised/pressed states on cards, buttons and inputs, kept subtle and used only where it aids usability, not on every element. Brand colours (primary dark green `#0F6B52`, teal `#1A9B8A`, mint, warm yellow/orange accents), typography (Manrope throughout) and spacing/radius scales are defined as CSS custom properties in `frontend/css/style.css`.

## Security notes

- Passwords are hashed (never stored in plaintext).
- Authentication uses JWT; the backend enforces role-based authorization, and the frontend never decides access on its own.
- Because Amahirwe's primary users are minors, there is no direct/unsupervised messaging between students and mentors. A teacher or administrator must approve a mentor match before any contact information is shared.
- Mentors and opportunity providers must be verified by an administrator before they can appear in matches or publish opportunities.

## License

Educational prototype built for a university capstone project. Not for production use.
