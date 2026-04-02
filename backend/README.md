# Application Hub Backend

Backend service for Application Hub, built with FastAPI, async SQLAlchemy, PostgreSQL, and Redis.

## What This Service Provides

- Authentication with JWT access/refresh tokens.
- Multi-tenant data access using the `X-Tenant-ID` request header.
- Application tracking APIs (create, list, update, soft-delete, dashboard summary).
- Reminder APIs plus a scheduler that enqueues/processes due reminders.
- Rate limiting via Redis (`fastapi-limiter`).

## Tech Stack

- Python 3.12
- FastAPI + Uvicorn
- SQLAlchemy (async) + asyncpg
- Alembic migrations
- Redis
- APScheduler
- Pytest

## Project Layout

```
backend/
	app/
		api/            # FastAPI routers, dependencies
		core/           # Security and logging setup
		db/             # Engine and session setup
		middleware/     # Request ID and error handling middleware
		models/         # SQLAlchemy models
		repositories/   # DB access layer
		schemas/        # Pydantic request/response schemas
		services/       # Business logic
	alembic/          # Database migration scripts
	tests/            # Unit/integration tests
```

## Prerequisites

- Python 3.12+
- PostgreSQL 15+
- Redis 7+
- Poetry (recommended)

## Environment Variables

Create a `.env` file in the repository root (used by Docker Compose) or export variables in your shell.

Required:

- `JWT_ACCESS_SECRET`
- `JWT_REFRESH_SECRET`
- `JWT_ALGORITHM` (example: `HS256`)

Optional (with defaults):

- `DATABASE_URL` (default: `postgresql+asyncpg://postgres:postgres@localhost:5432/app_db`)
- `REDIS_URL` (default: `redis://localhost:6379/0`)
- `CORS_ALLOW_ORIGINS` (default: `http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000`)
- `CORS_ALLOW_ORIGIN_REGEX` (default: `^https?://(localhost|127\\.0\\.0\\.1)(:\\d+)?$`)
- `JWT_ACCESS_EXPIRE_MINUTES` (default: `15`)
- `JWT_REFRESH_EXPIRE_MINUTES` (default: `1440`)
- `REMINDER_CHECK_INTERVAL_SECONDS` (default: `60`)
- `DASHBOARD_CACHE_TTL_SECONDS` (default: `60`)
- `TEST_DATABASE_URL` (required for tests; must be different from `DATABASE_URL`)

`CORS_ALLOW_ORIGINS` accepts a comma-separated list of frontend origins. Set it explicitly in non-local environments.
`CORS_ALLOW_ORIGIN_REGEX` allows pattern-based origin matching (used by default for localhost dev ports).

For local Docker Compose usage, you will also need:

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`

## Local Development (Without Docker)

From the `backend/` directory:

```bash
python -m venv .venv
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# or Git Bash
source .venv/Scripts/activate

pip install poetry
poetry install --no-root
```

Run migrations:

```bash
alembic upgrade head
```

Start the API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open docs at:

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

## Run with Docker Compose

From repository root:

```bash
docker compose up --build
```

The backend will be available at `http://localhost:8000`.

Run migrations in the backend container:

```bash
docker compose exec backend alembic upgrade head
```

## Testing

From `backend/`:

```bash
pytest
```

Set `TEST_DATABASE_URL` to a dedicated test database before running tests. The
test fixture creates and drops tables and will refuse to run if
`TEST_DATABASE_URL` is missing or matches `DATABASE_URL`.

With Docker Compose defaults, `TEST_DATABASE_URL` points to the `db_test`
service (`postgres_test` container, port `5433` on host).

## API Overview

Base API prefix: `/api`

- Auth: `/api/auth`
	- `POST /signup`
	- `POST /login`
	- `POST /refresh`
	- `POST /logout`
	- `GET /sessions`
	- `DELETE /sessions/{token_id}`
- Applications: `/api/applications`
	- `POST /`
	- `GET /`
	- `GET /dashboard`
	- `GET /{application_id}`
	- `PATCH /{application_id}`
	- `DELETE /{application_id}`
- Reminders: `/api/reminders`
	- `POST /`
	- `POST /process-due`

Health endpoint:

- `GET /` returns `{"message": "Backend is running"}`

## Auth and Tenant Notes

- Protected endpoints require `Authorization: Bearer <access_token>`.
- Tenant-scoped endpoints require `X-Tenant-ID: <uuid>`.
- `signup` creates a default workspace/tenant and membership for the new user.

## Operational Notes

- If Redis is unavailable at startup, the app continues running but rate limiting is skipped.
- Reminder scheduling starts on app startup and runs at `REMINDER_CHECK_INTERVAL_SECONDS`.
- Slow query logs are emitted when DB query duration exceeds 200 ms.
