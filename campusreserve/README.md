# CampusReserve

Sports court reservation platform for Universidad EAFIT — search, reserve, cancel, and join a waiting list for soccer, basketball, and volleyball courts, with automatic waiting-list notifications when a reservation is cancelled.

**Course:** Proyecto Integrador 1 — Universidad EAFIT, Ingeniería de Sistemas
**Team:** Samuel Ramírez, Samuel Rendón, Juan Pablo Lopera, Juan Diego Albanez, Daniel Muñetón, Tomás Vera

This repository implements Sprint 1 + Sprint 2 user stories (HU1–HU8):

| ID | Story | Sprint |
|---|---|---|
| HU1 | Search available courts | 1 |
| HU2 | Reserve a court | 1 |
| HU3 | View court status clearly | 1 |
| HU5 | Shared court constraint (basketball/volleyball) | 1 |
| HU4 | Cancel a court reservation | 2 |
| HU6 | Join a waiting list for a court | 2 |
| HU7 | Automatic notification on cancellation | 2 |
| HU8 | Auto-advance the queue | 2 |

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19 (Vite), Tailwind CSS |
| Backend | Django 5.x + Django REST Framework |
| Authentication | JWT (`djangorestframework-simplejwt`) |
| Database | PostgreSQL 15+ (SQLite automatically used in local dev if `DATABASE_URL` is unset) |
| Async tasks | Celery + Redis (waiting-list expiration and notifications) |

---

## Prerequisites

- **Python** 3.11 or higher
- **Node.js** 18 or higher (includes `npm`)
- **Redis** 7 or higher, running locally or accessible remotely
- **PostgreSQL** 15+ — optional for local dev (SQLite is used automatically if you skip it)
- **git**

---

## Project structure

```
campusreserve/
├── backend/             # Django project (API)
│   ├── accounts/        # Registration, login (FR20)
│   ├── courts/          # Court catalog, search, status (HU1, HU3, HU5)
│   ├── reservations/    # Reserve / cancel (HU2, HU4)
│   ├── waitlist/        # Waiting list + Celery tasks (HU6, HU7, HU8)
│   ├── manage.py
│   └── requirements.txt
└── frontend/             # React application (Vite)
    ├── src/
    │   ├── App.tsx       # Screens (login, home, book, my-reservations, waitlist)
    │   └── api.ts         # API client
    └── package.json
```

---

## Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate          # Windows

pip install -r requirements.txt
cp .env.example .env             # edit if you want PostgreSQL instead of SQLite

python manage.py migrate
python manage.py seed_courts     # loads the soccer / basketball-volleyball / volleyball courts
python manage.py createsuperuser # optional, for /admin/

python manage.py runserver       # http://localhost:8000
```

In a **separate terminal** (same virtual environment), start the Celery worker — required for HU7/HU8 (automatic waiting-list notification and expiration):

```bash
redis-server                                      # if not already running
celery -A campusreserve worker --loglevel=info
```

---

## Frontend setup

```bash
cd frontend
npm install
cp .env.example .env             # points to the backend API, defaults to localhost:8000
npm run dev                      # http://localhost:5173
```

Create an account from the login screen using an `@eafit.edu.co` email (enforced by the backend), or register one directly:

```bash
curl -X POST http://localhost:8000/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"ana.gomez@eafit.edu.co","first_name":"Ana","last_name":"Gomez","password":"CampusReserve123!"}'
```

---

## Running tests

```bash
cd backend
python manage.py test
```

---

## Documentation

- Full Software Requirements Specification, sprint backlog, and Deliverable 1/2 records: see the project **Wiki** on GitHub.
- Deployment, Component, and Data Model diagrams: `.drawio` files, open with [app.diagrams.net](https://app.diagrams.net).
