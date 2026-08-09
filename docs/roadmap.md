# Ops Status Board Roadmap

This is the public summary of blueprint `3.0.0`, state schema 2. It preserves completed work and reframes the remaining project as a 12–16 week operator-first Junior DevOps/CloudOps path.

## Core catalog

The core contains 69 sequential tasks across 13 milestones, M00–M12.

| Milestone | Operator outcome | Release |
|---|---|---|
| M00 — Baseline and safety | Verify environments, boundaries, privacy, and cost concepts | v0.1 |
| M01 — Workstation and repository | Prepare WSL2, Linux tools, Docker, Git, GitHub, and resumable project control | v0.1 |
| M02 — Application as an operable workload | Operate PostgreSQL, migrations, API/dashboard behavior, health, logs, metrics, and failures | v0.1 |
| M03 — Containers and local stack | Build, inspect, secure, and troubleshoot the Docker/Compose workload | v0.2 |
| M04 — CI and immutable images | Run quality/security pipelines and publish protected GHCR digests | v0.2 |
| M05 — Manual VM operations | Rebuild Ubuntu 24.04, harden access, deploy manually, reboot, back up, and restore | v0.3 |
| M06 — Ansible configuration | Reproduce the server, prove idempotence, and correct drift | v0.3 |
| M07 — Local observability and recovery | Use Prometheus/Grafana, logs, request IDs, alerts, backups, restores, and postmortems | v0.3 |
| M08 — AWS safety and manual lab | Establish account/cost controls, use SSM, compare EC2 with the local VM, and clean up | v0.4 |
| M09 — Terraform and cloud deployment | Build protected state, least-privileged infrastructure, SSM deployment, drift, destroy, and recreate | v0.4 |
| M10 — Secure cloud delivery | Use CloudWatch, OIDC, protected digest deployment, failure, and manual rollback | v0.5 |
| M11 — Cloud recovery, audit, and teardown | Restore from S3, investigate failure, audit the system, and verify cleanup/billing | v0.9 |
| M12 — Portfolio completion | Publish reproducible evidence, demo/career materials, clean-clone acceptance, and project defense | v1.0.0 |

## Ownership model

The learner personally operates Linux, Git, containers, pipelines, Nginx, systemd, SSH/firewall controls, Ansible, Terraform, monitoring, recovery, and AWS. Each task includes at least one meaningful operation, investigation, troubleshooting step, or configuration/automation modification.

Codex may scaffold repetitive FastAPI business logic, SQLAlchemy/Jinja plumbing, application-test fixtures, and private-control boilerplate. Evidence distinguishes authored/configured work from operated/reviewed/troubleshot work. Memorizing syntax is not required; understanding purpose, risk, verification, and recovery is required.

## Fixed core direction

- Python 3.12, FastAPI, PostgreSQL, and Alembic
- Docker Engine, Docker Compose, GitHub Actions, and GHCR
- Ubuntu 24.04 WSL2 workstation and separate Ubuntu 24.04 VirtualBox server
- Nginx, systemd, SSH, firewall, permissions, backup, and restore
- Ansible and Terraform introduced just in time
- AWS EC2, Systems Manager, CloudWatch, restricted OIDC, and encrypted S3/state
- Prometheus and Grafana for the local observability lab
- USD $5/month out-of-pocket ceiling and explicit approval for chargeable actions

## Optional extensions

The following do not block the portfolio: Loki/Alloy and advanced Grafana provisioning; external email notifications; paid domain/DNS/trusted HTTPS and permanent public hosting; automatic rollback; repeated pressure/configuration drills; a larger security audit; Kubernetes; microservices; managed databases; and load balancers.

Local implementation and recovery come before AWS. The cloud core uses Systems Manager and CloudWatch rather than duplicating the complete self-hosted observability stack on a small EC2 instance.
