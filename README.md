# Ops Status Board

Ops Status Board is a hands-on DevOps portfolio project showing how a small operations and incident dashboard is developed, tested, deployed, observed, backed up, and recovered.

> **Current status:** The workstation and public repository are ready, and the learning workflow is being established. The application, deployment environments, and public URL do not exist yet.

## Project goals

This project will demonstrate:

- a Python 3.12 FastAPI application backed by PostgreSQL;
- repeatable local development with Docker Engine and Docker Compose;
- continuous integration and container publishing with GitHub Actions and GitHub Container Registry;
- deployment and operations practice on a separate Ubuntu server;
- configuration management with Ansible;
- metrics, dashboards, logs, and alerts with Prometheus, Grafana, Loki, Alloy, and Alertmanager;
- backup and verified recovery procedures; and
- a later, cost-controlled adaptation to AWS using Terraform and Systems Manager.

The core project uses one application, one PostgreSQL database, and Docker Compose. Kubernetes, microservices, managed databases, and a JavaScript frontend are intentionally outside the core scope.

## Learning environments

| Environment | Purpose |
|---|---|
| Windows | Host platform, browser, and terminal access |
| Ubuntu 24.04 under WSL2 | Development and automation workstation |
| Separate Ubuntu VM | Local server deployment, operations, failure, and recovery practice |
| AWS | Later cloud adaptation after the local system is proven and cost gates pass |

## Project documentation

- [`docs/architecture.md`](docs/architecture.md) describes the planned system, environment, and delivery paths.
- [`docs/roadmap.md`](docs/roadmap.md) summarizes the approved delivery sequence and technical boundaries.
- [`docs/backlog.md`](docs/backlog.md) parks unapproved future ideas outside the current scope.
- [`docs/blueprint-changelog.md`](docs/blueprint-changelog.md) summarizes approved changes to the plan.
- [`docs/glossary.md`](docs/glossary.md) defines project terms.
- [`docs/lessons-learned.md`](docs/lessons-learned.md) records selected technical lessons in a portfolio-friendly form.
- Git history, tests, runbooks, architecture records, and sanitized evidence will show what has actually been implemented and verified.

Detailed coaching records, environment snapshots, and the master learning blueprint are private control documents kept outside Git. They are not required to understand, build, or evaluate the public project.

## Learning workflow

Planned tasks move through:

```text
Backlog -> Ready -> In Progress -> Verification -> Done
                              \
                               -> Blocked
```

Only one task may be **In Progress** at a time. GitHub may warn when a column limit is exceeded, but the learner and reviewer must enforce this WIP-one rule. Work enters **Done** only after verification and evidence review pass.

GitHub task and pull-request templates keep scope, risks, verification, evidence, and review visible throughout the workflow. The public backlog document contains optional ideas; the GitHub Project's **Backlog** status contains planned tasks that are not ready to start.

## Security and cost boundaries

- Secrets, private keys, credentials, personal email addresses, real `.env` files, account identifiers, and sensitive evidence must never enter Git.
- Only harmless placeholders belong in a future `.env.example` file.
- AWS work begins only after the local system is proven and documented approval and cost checks pass.
- The project targets no more than USD $5 per month in out-of-pocket cloud spending; an alert is a warning, not an automatic shutdown.

## Current next step

Finish and verify the Milestone 1 learning workflow before adding application code or infrastructure.
