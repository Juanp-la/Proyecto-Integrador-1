# CampusReserve

Sports court reservation platform for Universidad EAFIT — search, reserve, cancel, and join a waiting list for soccer, basketball, and volleyball courts, with automatic waiting-list notifications when a reservation is cancelled.

**Course:** Proyecto Integrador 1 — Universidad EAFIT, Ingeniería de Sistemas
**Team:** Samuel Ramírez, Samuel Rendón, Juan Pablo Lopera, Juan Diego Albanez, Daniel Muñetón, Tomás Vera

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 18 (Vite), React Router, Axios, Tailwind CSS |
| Backend | Django 5.x + Django REST Framework |
| Authentication | JWT (`djangorestframework-simplejwt`) |
| Database | PostgreSQL 15+ |
| Async tasks | Celery + Redis (waiting-list expiration and notifications) |

---

## Prerequisites

Make sure you have the following installed before setting up the project:

- **Python** 3.11 or higher
- **Node.js** 18 or higher (includes `npm`)
- **PostgreSQL** 15 or higher, running locally or accessible remotely
- **Redis** 7 or higher, running locally or accessible remotely
- **git**

---

## Project structure

```
campusreserve/
├── backend/            # Django project (API)
│   ├── accounts/       # User registration, login, JWT
│   ├── courts/         # Court catalog, search, status
│   ├── reservations/   # Reservation creation/cancellation
│   ├── waitlist/       # Waiting list logic (Celery tasks)
│   ├── manage.py
│   └── requirements.txt
└── frontend/            # React application
    ├── src/
    ├── package.json
    └── vite.config.js
```

---

## Backend setup (Django + DRF)

1. Clone the repository and move into the backend folder:

   ```bash
   git clone https://github.com/<org>/campusreserve.git
   cd campusreserve/backend
   ```

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate        # macOS / Linux
   venv\Scripts\activate           # Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the `backend/` folder with the following variables:

   ```env
   DEBUG=True
   SECRET_KEY=<your-django-secret-key>
   DATABASE_URL=postgres://<user>:<password>@localhost:5432/campusreserve_db
   REDIS_URL=redis://localhost:6379/0
   ALLOWED_HOSTS=localhost,127.0.0.1
   CORS_ALLOWED_ORIGINS=http://localhost:5173
   ```

5. Create the PostgreSQL database (if it doesn't exist yet):

   ```bash
   createdb campusreserve_db
   ```

6. Apply migrations:

   ```bash
   python manage.py migrate
   ```

7. Create an admin user (optional, for Django Admin access):

   ```bash
   python manage.py createsuperuser
   ```

8. Run the development server:

   ```bash
   python manage.py runserver
   ```

   The API will be available at `http://localhost:8000/api/`.

9. In a **separate terminal** (same virtual environment activated), start the Celery worker, required for the waiting-list notifications and expiration logic:

   ```bash
   celery -A campusreserve worker --loglevel=info
   ```

   Make sure Redis is running before starting Celery (`redis-server`, or your platform's Redis service).

---

## Frontend setup (React)

1. In a new terminal, move into the frontend folder:

   ```bash
   cd campusreserve/frontend
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Create a `.env` file in the `frontend/` folder with the following variable:

   ```env
   VITE_API_BASE_URL=http://localhost:8000/api
   ```

4. Run the development server:

   ```bash
   npm run dev
   ```

   The application will be available at `http://localhost:5173`.

---

## Running tests

Backend tests (from the `backend/` folder, with the virtual environment activated):

```bash
python manage.py test
```

---

## Documentation

- Full Software Requirements Specification, sprint backlog, and project management records: see the project **Wiki** on GitHub.
- Deployment, Component, and Data Model diagrams: see `/docs/diagrams` in this repository (`.drawio` files, open with [app.diagrams.net](https://app.diagrams.net)).
