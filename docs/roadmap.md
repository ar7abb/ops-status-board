# Ops Status Board Roadmap

This roadmap is a public summary of the approved project sequence. The planning baseline is version 2.1.0; it changes documentation privacy, not the technical architecture.

## Delivery sequence

1. **Workstation and repository** — Prepare Ubuntu 24.04 under WSL2, install trusted development tools and Docker, configure privacy-aware GitHub access, and establish the public repository.
2. **Application literacy** — Build a tested FastAPI service with a PostgreSQL data model, migrations, health endpoints, and clear failure behavior.
3. **Containers and CI** — Package the service, run the local stack with Docker Compose, test it in GitHub Actions, and publish versioned images to GitHub Container Registry.
4. **Local server operations** — Deploy manually to a separate Ubuntu server, add Nginx, then automate repeatable configuration with Ansible.
5. **Observability and reliability** — Add metrics, dashboards, centralized logs, alerts, backups, restore verification, and failure-recovery exercises on the local server.
6. **Cost-controlled AWS adaptation** — Apply explicit cost gates, practise a small manual cloud lab, create infrastructure with Terraform, configure the server, and add DNS and HTTPS.
7. **Secure delivery and recovery** — Use GitHub OIDC and AWS Systems Manager for deployment, prove rollback and cloud recovery, audit security, and tear down chargeable resources.
8. **Portfolio completion** — Publish sanitized evidence, runbooks, architecture decisions, demonstrations, and a final project defence.

## Fixed technical direction

- Python 3.12 and FastAPI
- PostgreSQL and database migrations
- Docker Engine and Docker Compose
- GitHub Actions and GitHub Container Registry
- Ubuntu server, Nginx, and Certbot
- Ansible for configuration management
- Prometheus, Grafana, Loki, Alloy, and Alertmanager
- Terraform, Amazon EC2, GitHub OIDC, and AWS Systems Manager
- Encrypted backups with verified restore procedures

Kubernetes, microservices, managed databases, load balancers, NAT Gateway, and frontend expansion are deliberately outside the core project.

## Safety boundaries

- Local implementation, deployment, observation, backup, and recovery come before AWS.
- No chargeable cloud change happens without a current cost review and explicit approval.
- The target out-of-pocket AWS limit is USD $5 per month.
- Secrets and raw private-control records never enter the public repository.
