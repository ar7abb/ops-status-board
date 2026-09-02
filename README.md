# Ops Status Board

Ops Status Board is an operator-first DevOps and CloudOps portfolio project. It uses a small FastAPI and PostgreSQL incident dashboard as a realistic workload for learning how to build, configure, test, deliver, secure, observe, back up, recover, and remove a service.

> **Current status:** Milestones 0–9 and M10-T01 are complete. The reproducible AWS workload now sends retained Nginx logs plus minimal host metrics to CloudWatch and evaluates four actionable alarms. Terraform remains converged, Ansible remains idempotent over Systems Manager without inbound SSH, and the monitoring design stays within an explicit free-allowance and promotional-credit boundary. Release `v0.4` records the reproducible cloud foundation; M10 continues with secure delivery.

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
| AWS | Cost-controlled Terraform, SSM, Ansible, EC2, IAM, networking, and private encrypted storage implementation |

The application and project repository live inside the WSL Linux filesystem. The VirtualBox VM remains a separate server environment.

## Documentation

- [`docs/architecture.md`](docs/architecture.md) describes current and planned system boundaries.
- [`docs/roadmap.md`](docs/roadmap.md) summarizes the operator-first delivery sequence.
- [`docs/backlog.md`](docs/backlog.md) contains optional extensions.
- [`docs/blueprint-changelog.md`](docs/blueprint-changelog.md) records approved planning changes.
- [`docs/glossary.md`](docs/glossary.md) defines project terminology.
- [`docs/lessons-learned.md`](docs/lessons-learned.md) records selected technical lessons.
- [`docs/recovery-runbook.md`](docs/recovery-runbook.md) documents PostgreSQL backup and clean restore verification.
- [`docs/observability.md`](docs/observability.md) records the local monitoring architecture, capacity budget, image-security decision, and verification evidence.
- [`docs/cloudwatch-observability.md`](docs/cloudwatch-observability.md) records the AWS signal flow, alarm policy, cost boundary, verification, and recovery path.
- [`docs/terraform-drift-recreation.md`](docs/terraform-drift-recreation.md) records the reviewed M09 drift, destruction, cleanup, and equivalent recreation exercise.

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

The application expects a PostgreSQL instance matching the private `DATABASE_URL`.

## Local Docker Compose

Use Docker Compose to run the application and PostgreSQL together on a local machine. Docker and the Docker Compose plugin must be installed first.

Create private configuration files from the safe templates:

```bash
cp .env.example .env
cp postgres.env.example postgres.env
```

Replace every placeholder. Keep `.env` for application settings and `postgres.env` for PostgreSQL initialization settings. For Compose, the hostname in `DATABASE_URL` is `db`, because `db` is the private database service name. The PostgreSQL database name, user, and password must match across the two files.

Validate configuration and start PostgreSQL:

```bash
docker compose config --quiet
docker compose up --detach db
```

Apply outstanding database migrations, then start the application:

```bash
docker compose run --rm migrate
docker compose up --detach app
```

Verify readiness and container health:

```bash
curl -i http://127.0.0.1:8000/health/ready
docker compose ps
```

The application is intentionally bound to `127.0.0.1:8000`. PostgreSQL has no host-published port and is reachable only by services on the Compose network.

Stop the stack with:

```bash
docker compose down
```

This removes containers and the network but keeps the named database volume. Use `docker compose down -v` only when you intentionally want to delete local database data.

## Database migrations

Database schema changes are versioned with Alembic.

The commands in this section assume PostgreSQL is reachable directly from WSL. When using Docker Compose, run schema commands through the temporary `migrate` service shown above.

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

## Run without Docker

Start FastAPI directly from WSL, rather than through Docker Compose:

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
- PostgreSQL is not host-published by Docker Compose; only Compose services can reach it.

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

Run the following application-quality checks before committing or opening a pull request:

```bash
python -m pytest -q
ruff check .
ruff format --check .
python -m pip check
git diff --check
```

Use the schema verification command that matches the database location:

- **Host Python workflow:** use this when `DATABASE_URL` points to PostgreSQL reachable directly from WSL.

  ```bash
  python -m alembic check
  ```

- **Docker Compose workflow:** use this when `DATABASE_URL` uses the private Compose hostname `db`.

  ```bash
  docker compose run --rm migrate alembic check
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

Begin M10-T02: define a restricted GitHub Actions OIDC role and protected deployment workflow without storing long-lived AWS credentials.
