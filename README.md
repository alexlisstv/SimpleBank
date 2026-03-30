# SimpleBank

REST API (Django 4 + DRF + PostgreSQL). See `PLAN.md` for scope and implementation checklist.

## Apps

- `users` — registration and authentication (upcoming)
- `accounts` — balances, transactions, transfers (upcoming)

## Local development (virtualenv)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pre-commit
pre-commit install
```

Start PostgreSQL (e.g. `docker compose up -d db`), then copy env and run migrations:

```bash
cp .env.example .env
export DJANGO_SETTINGS_MODULE=config.settings.dev
python manage.py migrate
python manage.py runserver
```

Create an admin user:

```bash
python manage.py createsuperuser
```

## Pre-commit

Hooks run Ruff (lint + format) and basic file checks:

```bash
pre-commit install
pre-commit run --all-files
```

## Docker

Build and run API + database:

```bash
docker compose up --build
```

With Docker Compose v1:

```bash
docker-compose up --build
```

The web container waits for PostgreSQL, runs `migrate`, then starts Gunicorn on port **8000**.

Override the secret in production:

```bash
SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())") docker compose up --build
```

## Settings modules

| Module                 | Use case                          |
|------------------------|-----------------------------------|
| `config.settings.dev`  | Default in `manage.py`, local dev |
| `config.settings.prod` | Gunicorn / Docker (`Dockerfile`)  |
