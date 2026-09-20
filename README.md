# Janatha Library Website

Janatha Reading Room & Library is a FastAPI application backed by PostgreSQL.
The active application is under `app/`; `server.js` is legacy reference code
and must not be used to run this version.

## Requirements

- Windows 10 or newer
- Python 3.11 or newer
- PostgreSQL 14 or newer
- Git

## Clone

```powershell
git clone https://github.com/aadhiarun2019/Janatha.git
cd Janatha
git switch rebuild-fastapi
```

## Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation for the current terminal, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

## Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Configure the environment

Copy the template and edit the new file:

```powershell
Copy-Item .env.example .env
```

Set your own values in `.env`:

```dotenv
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/janatha_library
SESSION_SECRET=replace-with-a-long-random-secret
```

Never commit `.env`. It is ignored by Git. Use URL encoding for special
characters in the PostgreSQL username or password.

## Create and migrate the database

Create an empty PostgreSQL database named `janatha_library` using pgAdmin or
the PostgreSQL command line tools, then run:

```powershell
alembic upgrade head
```

The migration files in `alembic/versions/` create the schema. The database is
not stored in this repository.

## Create the initial admin

After the database is migrated, run the existing provisioning script:

```powershell
python -m app.services.admin
```

Enter an admin username and password when prompted. This creates an admin in
the unified `users` table used by the FastAPI login flow.

## Run the application

```powershell
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000> in a browser. The admin dashboard is available at
`/admin` after admin login. Uploaded images are stored locally in `uploads/`;
production deployments need persistent storage for that directory or an
external storage service.

## Verification

```powershell
python -m compileall -q app
python test_endpoints.py
pip check
```

The endpoint smoke test checks unauthenticated access. For a full local check,
log in through the website and verify public content, admin content management,
image uploads, and the rental issue/return flow.

## Repository notes

- `app/`, `templates/`, `static/`, `alembic/`, `alembic.ini`, and
  `requirements.txt` are required application source/configuration.
- `.env`, virtual environments, caches, logs, local databases, and uploaded
  files are intentionally excluded from Git.
- `uploads/.gitkeep` is tracked so the upload directory exists after cloning.
