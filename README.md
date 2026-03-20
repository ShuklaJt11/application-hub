# application-hub

Application Hub is a job application tracking platform.

This repository currently contains the backend service and local infrastructure setup.

## What is included

- FastAPI backend for auth, applications, and reminders
- PostgreSQL for persistent storage
- Redis for rate limiting, caching, and reminder queueing
- Docker Compose for local orchestration

## Quick start

1. Create a root-level `.env` file with your Postgres and JWT variables.
2. Start services:

```bash
docker compose up --build
```

3. Run database migrations:

```bash
docker compose exec backend alembic upgrade head
```

4. Open API docs at `http://localhost:8000/docs`.

## Backend docs

For detailed backend setup, configuration, and API information, see [backend/README.md](backend/README.md).
