# Ops Status Board

Ops Status Board is an operator-first DevOps and CloudOps portfolio project. It uses a small FastAPI and PostgreSQL incident dashboard as a realistic workload for learning how to build, configure, test, deliver, secure, observe, back up, recover, and remove a service.

> **Current status:** Milestones 0 and 1 are complete. In Milestone 2, the Python foundation, reproducible dependencies, validated startup, request observability, PostgreSQL foundation, versioned migration, protected incident API, server-rendered dashboard, and operational endpoints are complete. Unit and integration failure tests, the local demonstration, and release `v0.1` remain.

## Portfolio focus

The project focuses on practical Junior DevOps and CloudOps responsibilities:

- Linux and server operations
- Git and pull-request workflows
- Docker and Docker Compose
- Continuous integration and delivery
- Immutable container images
- Nginx, systemd, SSH, permissions, and firewall behavior
- Ansible configuration management
- Terraform infrastructure management
- Metrics, logs, alerts, backup, restore, and incident response
- AWS operations, security controls, and cost management

## Current architecture

The current local application flow is:

```text
Browser or API client
    → FastAPI route
    → Pydantic validation
    → SQLAlchemy session
    → PostgreSQL
    → JSON response or Jinja-rendered HTML
    → structured logs with request IDs
```

FastAPI provides the HTTP interface and interactive API documentation. Pydantic validates incoming data. SQLAlchemy manages database operations. Alembic versions the PostgreSQL schema. Jinja renders incident data into completed HTML for the browser.

## Core delivery path

1. Build an operable FastAPI and PostgreSQL workload.
2. Containerize it and run the local stack with Docker Compose.
3. Test and publish immutable images with GitHub Actions and GHCR.
4. Operate it manually on a separate Ubuntu practice server.
5. Reproduce the server configuration with Ansible.
6. Monitor, investigate, back up, fail, and restore the local service.
7. Reproduce the relevant infrastructure and delivery workflow in AWS.
8. Preserve evidence, remove cloud resources, and complete the portfolio.

The approved roadmap contains 69 tasks across milestones M00–M12 and targets approximately 12–16 weeks of focused work.

## Environments

| Environment | Purpose |
|---|---|
| Windows | Host platform, browser, and terminal access |
| Ubuntu 24.04 under WSL2 | Linux development and automation workstation |
| Separate VirtualBox VM | Server deployment and operations practice beginning in M05 |
| AWS | Later cost-controlled CloudOps implementation after the local system is proven |

The application and project repository live inside the WSL Linux filesystem. The VirtualBox VM remains a separate server environment.

## Documentation

- [`docs/architecture.md`](docs/architecture.md) describes current and planned system boundaries.
- [`docs/roadmap.md`](docs/roadmap.md) summarizes the operator-first delivery sequence.
- [`docs/backlog.md`](docs/backlog.md) contains optional extensions.
- [`docs/blueprint-changelog.md`](docs/blueprint-changelog.md) records approved planning changes.
- [`docs/glossary.md`](docs/glossary.md) defines project terminology.
- [`docs/lessons-learned.md`](docs/lessons-learned.md) records selected technical lessons.

Private project state, learning notes, environment snapshots, credentials, and sensitive evidence remain outside the public repository.

## Local development setup

Create and activate a project-specific Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the hash-locked development dependencies:

```bash
python -m pip install --require-hashes -r requirements-dev.txt
python -m pip install --no-deps --editable .
python -m pip check
```

Create a private local configuration file:

```bash
cp .env.example .env
```

Replace every placeholder in `.env` with a local value. The real `.env` is ignored by Git and must never be committed.

The application expects a PostgreSQL instance matching the private `DATABASE_URL`. Docker Compose management of the complete local stack is introduced in Milestone 3.

## Database migrations

Database schema changes are versioned with Alembic.

Apply all migrations:

```bash
python -m alembic upgrade head
```

Inspect the current database revision:

```bash
python -m alembic current
```

Confirm that the SQLAlchemy models and database schema remain aligned:

```bash
python -m alembic check
```

Use migration downgrades only after reviewing their data-loss risk. The initial `downgrade base` exercise is intended only for an empty disposable development database.

## Start the application

Start the local FastAPI application from the repository root:

```bash
python -m uvicorn ops_status_board.app:create_app \
  --factory \
  --app-dir src \
  --host 127.0.0.1 \
  --port 8765 \
  --no-access-log
```

Available local interfaces:

| Interface | URL |
|---|---|
| Dashboard | `http://127.0.0.1:8765/` |
| Interactive API documentation | `http://127.0.0.1:8765/docs` |
| OpenAPI document | `http://127.0.0.1:8765/openapi.json` |

## Incident workflow

| Method | Path | Purpose | Authentication |
|---|---|---|---|
| `GET` | `/` | Render the incident dashboard as completed HTML | Public |
| `GET` | `/api/incidents` | List incidents as JSON | Public |
| `GET` | `/api/incidents/{incident_id}` | Return one incident or `404` | Public |
| `POST` | `/api/incidents` | Validate and create an incident | Bearer token |
| `PUT` | `/api/incidents/{incident_id}` | Validate and replace an incident or return `404` | Bearer token |

Supported severity values:

- `low`
- `medium`
- `high`
- `critical`

Supported status values:

- `investigating`
- `identified`
- `monitoring`
- `resolved`

A resolved incident must include `resolved_at`. An active incident must not include a resolved timestamp.

Invalid input is rejected before it reaches PostgreSQL. An unknown incident returns `404`, invalid data returns `422`, and an unauthenticated write returns `401`.
`PUT` is a full replacement: send the same complete payload used for `POST`.

## Operational endpoints

| Method | Path | Purpose | Authentication |
|---|---|---|---|
| `GET` | `/health/live` | Confirm the HTTP application process is running; it never queries PostgreSQL | Public |
| `GET` | `/health/ready` | Confirm a minimal PostgreSQL query succeeds | Public |
| `GET` | `/version` | Return the configured application version | Public |
| `GET` | `/metrics` | Return minimal Prometheus-compatible process metrics | Bearer token |

Liveness and readiness answer different operator questions: liveness detects whether the application process can respond, while readiness detects whether it can currently use its database. A database failure therefore leaves liveness at `200` but makes readiness return `503` with a safe `Not ready` response.

Metrics remain protected because they are intended for a trusted monitoring client, not public discovery.

## Configuration and security

Startup validates required configuration before the application serves requests.

Required settings include:

- `DATABASE_URL`
- `ADMIN_API_TOKEN`
- `APP_VERSION`
- `APP_ENVIRONMENT`

The application follows these security rules:

- Real `.env` files never enter Git.
- Database passwords and bearer tokens never appear in client errors.
- Request logs omit query strings.
- Authentication headers and submitted tokens are not logged.
- Every response receives an `X-Request-ID`.
- Unexpected failures return a generic response with a traceable request ID.
- Database sessions roll back uncommitted work after failures.
- Protected writes use constant-time token comparison.
- PostgreSQL is bound to the local workstation during development.

## Logging behavior

Development logs are human-readable. Production logs use structured JSON.

Routine request logs include:

- timestamp
- log level
- request ID
- HTTP method
- URL path
- response status
- request duration

Logs do not include the complete URL, query parameters, request body, database password, or admin token.

## Verification

Run the complete local verification suite before committing or opening a pull request:

```bash
python -m alembic check
python -m pytest -q
ruff check .
ruff format --check .
python -m pip check
git diff --check
```

### Opt-in PostgreSQL integration tests

`tests/test_postgres_integration.py` uses only the disposable local
`ops_status_board_test` database. It is skipped unless explicitly enabled.

Create that database locally and run migrations first. Then run:

```bash
RUN_POSTGRES_INTEGRATION=1 python -m pytest -q tests/test_postgres_integration.py
```

The tests verify the database name before modifying data and clean up test
incidents afterward.

A release candidate must also prove that:

- dependencies install in a clean environment;
- migrations build an empty database;
- expected API and dashboard workflows succeed;
- authentication and validation failures are safe;
- no secret or private state is tracked by Git; and
- the working tree contains only reviewed project changes.

## Workflow and safety

- Work on one task at a time.
- Use focused feature branches.
- Related tasks may share a branch and pull request.
- Review staged changes before creating a commit.
- Do not commit secrets, private keys, credentials, real `.env` files, Terraform state, backups, or private-control records.
- Do not create chargeable AWS resources without a current cost review and explicit approval.
- Keep out-of-pocket cloud spending at or below USD $5 per month.

## Current next step

Review the M02-T10 unit-test plan, followed by integration failure tests, the local demo, and release `v0.1`.
