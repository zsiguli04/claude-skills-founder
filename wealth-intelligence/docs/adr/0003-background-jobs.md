# ADR 0003: background jobs

Status: accepted.

## Decision

Celery workers with Redis as the broker. Job outcomes that matter (ingestion runs, batch valuations, report generation, regulatory fetches) are recorded in PostgreSQL tables, not only in the Celery result backend, so they are auditable and survive Redis restarts.

## Why

Mature, widely operated, supports chunked batch work, retries with backoff, scheduled tasks (Celery beat) for regulatory monitoring. Redis 7 is already available in the environment.

## Rules

- Tasks are idempotent: keyed by `(task kind, subject id, data version, parameter set)`.
- Tasks call domain services, never engines directly with raw database rows.
- No secrets in task arguments.
