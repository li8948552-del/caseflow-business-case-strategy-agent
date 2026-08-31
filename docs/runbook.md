# Operations Runbook

## Local development

1. Copy `.env.example` to `.env`.
2. Set `OPENAI_API_KEY`.
3. Run `make install`, then `make run` and `make worker` in separate terminals.

## Production-like Docker

```bash
export OPENAI_API_KEY="..."
docker compose up --build
```

Before any real deployment, replace the compose API key and database password with
secret-manager values.

## Database

Production uses Alembic:

```bash
alembic upgrade head
```

Never enable `CASEFLOW_AUTO_CREATE_SCHEMA` in production.

## Incident checks

1. Check `/health/live`.
2. Inspect the job endpoint and case audit trail.
3. A `failed` case preserves the exception category but should not store credentials.
4. Confirm the official competition AI policy before creating a case.
5. Do not upload active competition material to the public template repository.
