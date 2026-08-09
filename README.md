# Ops Status Board

Ops Status Board is an operator-first DevOps and CloudOps portfolio project. A small FastAPI/PostgreSQL incident dashboard provides a realistic workload for learning how to build, deliver, configure, observe, secure, back up, recover, and remove a service.

> **Current status:** Milestones 0 and 1 are complete. In Milestone 2, the Python foundation, reproducible dependencies, validated startup, request IDs, safe errors, and structured/redacted logs are complete. PostgreSQL-backed behavior has not started, and no deployment or cloud environment exists.

## Portfolio focus

The learner owns the work most representative of a Junior DevOps/CloudOps role:

- Linux and server operations;
- Git, Docker, Compose, CI/CD, and immutable images;
- Nginx, systemd, SSH, permissions, and firewall behavior;
- Ansible and Terraform configuration;
- metrics, logs, alerts, backup, restore, incident response, and AWS operations; and
- security and cost controls across those layers.

Codex may scaffold repetitive FastAPI, SQLAlchemy, Jinja, and application-test plumbing. Public evidence describes that assistance honestly. For example, the M02-T04 observability module was Codex-scaffolded while the learner operated it, tested it, reviewed it, detected a query-string leak in the runtime path, changed the startup behavior, and verified the correction.

## Core delivery path

1. Build an operable FastAPI/PostgreSQL workload.
2. Containerize it and run the local stack with Docker Compose.
3. Test and publish immutable images with GitHub Actions and GHCR.
4. Operate it manually on a separate Ubuntu 24.04 practice server.
5. Reproduce server configuration with Ansible.
6. Monitor, investigate, back up, fail, and restore the local service.
7. Repeat the relevant infrastructure and delivery path in AWS with Terraform, Systems Manager, CloudWatch, OIDC, encrypted S3 backups, and strict cost gates.
8. Preserve evidence, tear down cloud resources, and defend the project.

The approved blueprint has 69 tasks across M00–M12 and targets approximately 12–16 weeks at 75–90 focused minutes on most study days.

## Environments

| Environment | Purpose |
|---|---|
| Windows | Host platform, browser, and terminal access |
| Ubuntu 24.04 under WSL2 | Development and automation workstation |
| Separate VirtualBox VM | Ubuntu 24.04 server deployment and operations practice beginning in M05 |
| AWS | Later cost-controlled CloudOps adaptation after the local system is proven |

## Documentation

- [`docs/architecture.md`](docs/architecture.md) describes current and planned system boundaries.
- [`docs/roadmap.md`](docs/roadmap.md) summarizes the operator-first delivery sequence.
- [`docs/backlog.md`](docs/backlog.md) contains optional extensions that do not block the portfolio.
- [`docs/blueprint-changelog.md`](docs/blueprint-changelog.md) records approved planning changes.
- [`docs/glossary.md`](docs/glossary.md) defines project terms.
- [`docs/lessons-learned.md`](docs/lessons-learned.md) records selected technical lessons.

The detailed master blueprint, raw project state, learning log, environment snapshots, and sensitive evidence remain in a private control bundle outside Git.

## Local application startup

Create a local `.env` from the safe example and replace every placeholder. The real `.env` remains ignored and must never be committed.

```bash
cp .env.example .env
python -m uvicorn ops_status_board.app:create_app \
  --factory --app-dir src --no-access-log
```

Startup validates configuration before FastAPI serves requests. Every response receives an `X-Request-ID`. Production logs are structured JSON, omit query strings, redact configured secrets, and return generic traceable errors to clients. The application currently exposes FastAPI's generated `/docs`; the database-backed workflow arrives in the remaining Milestone 2 tasks.

## Workflow and safety

- One task is In Progress at a time in the private project state.
- Related tasks may share a branch and pull request, with one local commit per coherent task.
- A task requires meaningful learner operation, inspection, troubleshooting, or configuration/automation modification; copying commands alone is not completion.
- No chargeable AWS change occurs without current cost review and explicit approval.
- The out-of-pocket cloud ceiling is USD $5 per month.
- Secrets, private keys, credentials, personal identifiers, real `.env` files, Terraform state, backups, and raw private-control records never enter Git.

## Current next step

Review the M02-T05 PostgreSQL operator-lab and Incident-model plan before starting PostgreSQL or changing application code.
