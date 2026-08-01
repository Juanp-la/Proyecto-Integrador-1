# R2 Cinema — Movie Catalog

A Django-based movie catalog site. Browse movies, search by title, and manage entries through Django's admin panel.

## Built With

- **Python 3.14**
- **Django 6.0** — web framework
- **Pillow** — image upload handling for movie posters
- **Bootstrap 5.3.3** (via CDN) — front-end styling
- **SQLite** — database (Django's default, `db.sqlite3`)

## Features

- Movie catalog with poster images, title, description, and details (genre/year/runtime)
- Search bar — filter movies by title (case-insensitive)
- Custom display order for movies, set from the admin panel
- Django admin panel for adding/editing/deleting movies
- Responsive layout (mobile, tablet, desktop)

## Project Structure

```
R2-Project/
├── R2/               # Django project config (settings, urls, wsgi)
├── movie/            # Main app — models, views, admin, templates
│   └── templates/    # home.html, about.html
├── media/             # Uploaded movie posters (gitignored — not shared between machines)
├── venv/              # Virtual environment (gitignored — recreate per machine)
├── db.sqlite3         # SQLite database
└── manage.py
```

## Requirements

- Python 3.14+ (installed with "Add python.exe to PATH" checked)
- pip (bundled with Python)
- Git

## First-Time Setup (new machine)

**1. Clone the repo and switch to the working branch:**
```powershell
git clone https://github.com/Juanp-la/Proyecto-Integrador-1.git R2-Project
cd R2-Project
git checkout Juan-pablo-lopera-Arrazola
```

**2. Create and activate a virtual environment:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
If PowerShell blocks the script with an execution policy error:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

**3. Install dependencies** (venv must be active — check for `(venv)` in the prompt):
```powershell
pip install django pillow
```

**4. Apply database migrations:**
```powershell
py manage.py makemigrations movie
py manage.py migrate
```

**5. (Optional) Create an admin login:**
```powershell
py manage.py createsuperuser
```

**6. Run the development server:**
```powershell
py manage.py runserver
```
- Site: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## Daily Workflow (already set up)

```powershell
cd path\to\R2-Project
.\venv\Scripts\Activate.ps1
py manage.py runserver
```
Stop the server with `Ctrl+C`, then `deactivate` to exit the virtual environment.

## Git Workflow

Working branch (case-sensitive): `Juan-pablo-lopera-Arrazola`

```powershell
git status
git add -A
git commit -m "describe your change"
git push
git pull
```

## After Changing `models.py`

Any time a model field is added, removed, or changed:
```powershell
py manage.py makemigrations movie
py manage.py migrate
```

## Author

Juan Pablo Lopera Arrazola
