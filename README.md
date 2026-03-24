# Bank Statement Portal

This project now includes a full web application around the existing PDF transaction parser.

What is included:
- FastAPI backend with login and session-based authentication
- Mobile-friendly frontend for login, PDF upload, and transaction review
- Database-backed storage for users, uploads, and parsed transactions
- Default local setup with SQLite
- Optional Docker + Postgres setup for deployment
- Legacy ETL mode still available for the original batch workflow

## Stack

- Backend: FastAPI, SQLAlchemy, Jinja2
- Frontend: server-rendered HTML with vanilla JavaScript and CSS
- Parser: existing `pdfplumber` ETL logic from `src/etl`
- Database: SQLite by default, PostgreSQL supported via `DATABASE_URL`

## Project Modes

### Web app

Runs the authenticated upload dashboard.

```bash
python main.py --mode web --reload
```

Open:

```text
http://localhost:8000
```

To access it from your phone on the same Wi-Fi network, run the app on your computer and open:

```text
http://<your-computer-local-ip>:8000
```

Example local IP discovery:

```bash
ipconfig
```

### Legacy ETL mode

Runs the original folder-based batch parser.

```bash
python main.py --mode etl
```

Test mode:

```bash
python main.py --mode etl --test
```

## Local Setup

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Git Bash:

```bash
python -m venv .venv
source .venv/Scripts/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create environment file

Copy `.env.example` to `.env` and adjust values if needed.

Minimal `.env` for local development:

```env
APP_NAME=Bank Statement Portal
HOST=0.0.0.0
PORT=8000
SECRET_KEY=replace-this-in-production
SESSION_COOKIE_NAME=bank_portal_session
SESSION_TTL_HOURS=24
SESSION_SECURE_COOKIE=false
```

If `DATABASE_URL` is not set, the app uses SQLite automatically at `db/app.db`.

### 4. Start the web app

```bash
python main.py --mode web --reload
```

## Docker Setup

This repository includes:
- `Dockerfile` for the web app
- `docker-compose.yml` for the web app plus PostgreSQL

Start everything:

```bash
docker compose up --build
```

The app will be available at:

```text
http://localhost:8000
```

Postgres will be exposed at:

```text
localhost:5432
```

The default compose setup injects a PostgreSQL `DATABASE_URL` into the web container.

## Web App Features

- Register and login with email + password
- Secure session cookie authentication
- Drag-and-drop or tap-to-upload PDF statements
- Upload history with processing status
- Dashboard summary for credits, debits, total transactions, and latest balance
- Transaction table sorted by latest statement activity

## Database Notes

Recommended default:
- SQLite for local development because it needs no extra setup

Recommended for deployment:
- PostgreSQL through `DATABASE_URL`

Tables created automatically on startup:
- `users`
- `auth_sessions`
- `statement_uploads`
- `transactions`

## Important Files

- `main.py`: entrypoint for web mode and legacy ETL mode
- `app/main.py`: FastAPI app and API routes
- `app/models.py`: SQLAlchemy models
- `app/auth.py`: password hashing and session handling
- `app/services.py`: upload processing and dashboard queries
- `app/templates/index.html`: frontend shell
- `app/static/app.css`: frontend styles
- `app/static/app.js`: frontend logic
- `src/etl/readPdf.py`: existing PDF parsing logic

## Current API Endpoints

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `GET /api/dashboard`
- `GET /api/transactions`
- `POST /api/uploads`

## Notes

- Uploaded files are stored under `storage/uploads`
- Local SQLite data is stored at `db/app.db`
- The frontend and backend are served from the same app, so no separate frontend build is required
- For production, change `SECRET_KEY` and set `SESSION_SECURE_COOKIE=true` behind HTTPS