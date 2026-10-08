# Phase 0: environment

Inspected 2026-10-08 in the Claude Code cloud container. Rerun any time with `python3 scripts/check_env.py --phase N`; it exits 1 when a tool needed by phase N is missing.

## Machine

Ubuntu 24.04.5 LTS, 4 CPUs, 15 GiB RAM, about 30 GiB free disk.

## Tools

| Tool | Version | Status | Needed from |
|:-----|:--------|:-------|:------------|
| Python | 3.13.16 | installed | phase 0 |
| uv | 0.11.32 | installed | phase 2 |
| Git | 2.43.0 | installed | phase 0 |
| GitHub CLI | 2.89.0 | installed (GitHub access goes through the session's GitHub tools) | optional |
| Node.js | 22.22.0 (LTS line) | installed | phase 12 |
| pnpm | 10.28.0 | installed | phase 12 |
| PostgreSQL | 16.15 | client on PATH; server binaries in `/usr/lib/postgresql/16/bin`. Verified: `initdb`, start, `select version()`, stop | phase 4 |
| Redis | 7.0.15 | installed. Verified: start, `PING`, shutdown | phase 11 |
| Docker | 29.8.2, Compose v5.6.0, buildx 0.37.1 | installed. The daemon was not running; `dockerd` starts manually. Verified pulling `postgres:16-alpine` and `redis:7-alpine` | phase 19 |
| Chromium for Playwright | in `/opt/pw-browsers` | installed | phase 12 |
| Tesseract OCR | none | **missing** | phase 14 |

### Missing: Tesseract

Needed for OCR of scanned annual reports and property documents (phase 14). Not installed now because nothing needs it yet. When phase 14 starts:

```bash
apt-get install -y tesseract-ocr tesseract-ocr-hun
tesseract --version && tesseract --list-langs | grep hun
```

Alternative to evaluate in phase 14: a hosted document AI. That needs a data-processing review first, because the documents are restricted data.

### Starting services locally

```bash
# PostgreSQL (data owned by the postgres user)
runuser -u postgres -- /usr/lib/postgresql/16/bin/initdb -D /var/lib/postgresql/wi-dev -A scram-sha-256 -U postgres --pwfile=<(echo "$PGPASSWORD") -E UTF8 --locale=C.UTF-8
runuser -u postgres -- /usr/lib/postgresql/16/bin/pg_ctl -D /var/lib/postgresql/wi-dev -l /var/lib/postgresql/wi-dev.log -o "-p 5432" -w start

# Redis
redis-server --port 6379 --save "" --daemonize yes

# Docker daemon (in this container it is not started automatically)
dockerd > /var/log/dockerd.log 2>&1 &
```

From phase 4, `infra/docker-compose.dev.yml` will start PostgreSQL and Redis instead.

## Network

| Host | Reachable | Purpose |
|:-----|:----------|:--------|
| pypi.org, registry.npmjs.org, Docker Hub | yes | packages and images |
| api.anthropic.com | yes | AI layer |
| njt.hu, kormany.hu, nav.gov.hu, www.mnb.hu | **no** | official law, draft bills, tax authority, central bank |
| e-beszamolo.im.gov.hu, www.e-cegjegyzek.hu | **no** | company financial statements, company registry |

The environment's network policy blocks the Hungarian official hosts. This matters for phases 8 (regulatory engine), 14, and 18. They must be added under Allowed domains in the environment settings (see https://code.claude.com/docs/en/cloud-environments#network-access). Until then, regulatory facts come from web search summaries and are recorded with lower confidence.

## Environment variables

None of the project's variables are set yet: `ANTHROPIC_API_KEY` (phase 13), `DATABASE_URL` (phase 4), `REDIS_URL` (phase 11), `AUTH_JWT_SECRET` (phase 16), `APP_ENV`. Names and meanings are in `.env.example`. The container has unrelated cloud credentials in its environment; the project must not read or use them.
