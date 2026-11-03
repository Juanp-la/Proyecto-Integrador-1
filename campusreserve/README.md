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

### New features (Sprint 3)

| Feature | Where |
|---|---|
| Logout button | Navbar → **Salir** |
| One active reservation at a time (also blocks joining a waiting list) | `reservations/services.py` |
| Leave a waiting list (also used to decline an offer — the spot goes to the next student right away) | `POST /api/waitlist/<id>/leave/` |
| AI: most popular courts | `GET /api/ai/recommendations/popular/` |
| AI: little-used courts & time slots (free, next 6 days, skips rainy outdoor slots) | `GET /api/ai/recommendations/quiet/` |
| AI: daily weather report (Open-Meteo forecast + AI summary) | `GET /api/ai/weather/today/` |
| Bad-weather alerts for outdoor reservations, with option to cancel | `GET /api/notifications/`, `POST /api/notifications/<id>/cancel-reservation/`, `POST /api/notifications/<id>/dismiss/` |

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
│   ├── ai/              # AI client, weather (Open-Meteo), recommendations
│   ├── notifications/   # Bad-weather alerts for reservations
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

python manage.py seed_demo_usage # optional: past demo reservations so recommendations have data
python manage.py runserver       # http://localhost:8000
```

### AI configuration

The AI features use any **OpenAI-compatible** chat API. By default they use **Google Gemini**, which has a free tier:

1. Create a free key at <https://aistudio.google.com/apikey>.
2. Put it in `backend/.env`: `AI_API_KEY=your-key` (see `.env.example` to use OpenAI or Groq instead).

If `AI_API_KEY` is empty (or the AI call fails) everything still works: recommendations and the weather report are calculated with rules, and the UI shows *"Calculado con datos de uso"* instead of *"Generado con IA"*.

Weather data comes from [Open-Meteo](https://open-meteo.com) (free, no key) for the EAFIT coordinates. Only courts marked **outdoor** (`is_outdoor`, editable in `/admin/`) get rain alerts; the parquet courts are indoor. Alerts are created when a student opens the app/notifications; to also check every hour in the background run `celery -A campusreserve beat` (or `python manage.py check_weather` from a cron job).

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
