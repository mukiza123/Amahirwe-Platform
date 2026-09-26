<div align="center">

<img src="frontend/assets/icons/logo-full.png" alt="Amahirwe logo" width="220">

# Amahirwe Platform

**Discover. Connect. Grow.**

A web platform that helps students in rural public schools in Rwanda discover their talents and connect with mentors, teachers and real opportunities, even with weak or no internet.

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-4169E1?logo=postgresql&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-frontend-E34F26?logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-styling-1572B6?logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-vanilla-F7DF1E?logo=javascript&logoColor=black)
![Vercel](https://img.shields.io/badge/Vercel-deployment-000000?logo=vercel&logoColor=white)
![License](https://img.shields.io/badge/license-Educational-0F6B52)

[Live Demo](#live-demo) · [SRS Document](Lisette_Mukiza_Assignment2_07302026.pdf) · [Demo Accounts](#demo-accounts) · [Setup Guide](#getting-started)

</div>

---

## Overview

**The problem:** talented students in rural Rwandan schools go unnoticed. Mentors and opportunities are concentrated in Kigali, internet is weak and data is expensive, and most platforms are English-first.

**The solution:** Amahirwe gives students an offline talent assessment, matches them with verified mentors, and shows them scholarships and competitions, with a teacher approving every match. The platform works in Kinyarwanda, English and French.

One codebase, six user roles:

| Role | Route | What they can do |
|---|---|---|
| Student | `/student/` | Build a profile, take the talent assessment (works offline), see mentor matches and opportunities |
| Teacher | `/teacher/` | Add and track students, approve or decline mentor matches |
| Parent | `/parent/` | Follow their child's progress (once linked by a teacher) |
| Mentor | `/mentor/` | View approved mentees and their talent areas |
| Opportunity provider | `/provider/` | Post scholarships, competitions and internships |
| Administrator | `/admin/` | Verify mentors and providers, manage users, view the audit log |

## Key Features

| Feature | SRS reference |
|---|---|
| Offline talent assessment with automatic sync | FR-1.1 to FR-1.3, FR-5.1, FR-5.2 |
| Mentor matching by talent area and language | FR-2.1 |
| Teacher approval before any mentor contact | FR-2.2, FR-3.2 |
| Match notifications and audit log | FR-2.3, NFR-5 |
| Teacher dashboard with student progress | FR-3.1 |
| Opportunities feed filtered by talent area | FR-4.1, FR-4.2 |
| Kinyarwanda, English and French | FR-6.1 |

## Live Demo

- **App:** _add the Vercel URL here_
- **SRS:** [Lisette_Mukiza_Assignment2_07302026.pdf](Lisette_Mukiza_Assignment2_07302026.pdf)

## Demo Accounts

Created by the seed script (step 5 below). Password for all accounts: `password123`

| Role | Email |
|---|---|
| Student | `student@amahirwe.demo` |
| Teacher | `teacher@amahirwe.demo` |
| Parent | `parent@amahirwe.demo` |
| Mentor | `mentor@amahirwe.demo` |
| Provider | `provider@amahirwe.demo` |
| Admin | `admin@amahirwe.demo` |

The student already has a completed assessment and a pending mentor match, so you can log in as the teacher and approve it straight away.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, vanilla JavaScript, service worker + IndexedDB for offline use |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, Alembic |
| Database | PostgreSQL (free hosted instance on Neon) |
| Auth | JWT with role-based access, email verification codes |
| Deployment | Vercel |

## Getting Started

### Prerequisites

- Python 3.9 or newer
- A free [Neon](https://neon.tech) PostgreSQL database (no local install needed)
- A modern web browser

### 1. Clone the repository

```bash
git clone https://github.com/lisette-lachiever/Amahirwe-Platform.git
cd Amahirwe-Platform
```

### 2. Set up environment variables

Create a project on [neon.tech](https://neon.tech) and copy its connection string. Then:

```bash
cd backend
cp .env.example .env
```

Open `backend/.env` and fill in these two values:

| Variable | Value |
|---|---|
| `DATABASE_URL` | Your Neon connection string |
| `JWT_SECRET_KEY` | Any random string, e.g. from `python3 -c "import secrets; print(secrets.token_hex(32))"` |

Everything else can stay as it is. Leave the Google and email settings blank: verification codes will simply be shown on screen.

### 3. Install dependencies

```bash
# inside backend/
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Create the database tables

```bash
alembic upgrade head
```

### 5. Load the demo accounts

```bash
python ../database/seed.py
```

### 6. Start the backend

```bash
uvicorn app.main:app --reload --port 8000
```

Check it works: open http://127.0.0.1:8000/api/health (API docs at http://127.0.0.1:8000/docs).

### 7. Start the frontend (new terminal)

```bash
# from the project root
python3 dev-server.py 5500
```

Open **http://127.0.0.1:5500** and log in with a [demo account](#demo-accounts).

### Run the tests (optional)

```bash
# from the project root, with the venv activated
pytest tests/ -v
```

## Project Structure

```
Amahirwe-Platform/
├── backend/app/        FastAPI app: api/ routes, models/, schemas/, services/ (matching logic)
├── backend/alembic/    Database migrations
├── frontend/           HTML/CSS/JS site, one folder per role (student/, teacher/, ...)
├── frontend/locales/   Translations: en.json, rw.json, fr.json
├── database/seed.py    Demo data
├── tests/              Backend tests (pytest)
├── api/index.py        Vercel entry point
└── vercel.json         Deployment config
```

## Safety and Security

- Passwords are hashed; access is controlled by JWT and user role on the backend.
- Students are minors, so mentors never get contact details until a teacher or admin approves the match.
- Mentors and providers must be verified by an admin before they appear anywhere.
- Every match decision is recorded in the audit log.

## Known Limitations

- Text generated by JavaScript on dashboards (for example chart labels and notification messages) is still English only. Page headings, menus, buttons and forms are fully translated.

## Author

**Lisette Mukiza** · African Leadership College (ALCHE) · Introduction to Software Engineering, Final Project, 2026

Educational prototype, not intended for production use.
