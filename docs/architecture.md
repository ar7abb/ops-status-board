# Ops Status Board Architecture

> **Current status:** The FastAPI and PostgreSQL workload runs as pinned containers on both the separate Ubuntu 24.04 practice VM and a Terraform-managed AWS instance in Europe (Stockholm). Ansible deploys the cloud workload through Systems Manager without inbound SSH. The cloud instance keeps the API loopback-only behind Nginx, uses encrypted Parameter Store runtime values, and omits the heavier local Prometheus/Grafana stack.

## Architecture purpose

The application is intentionally small. It creates an operable workload through which the learner can practise delivery, configuration, security, observation, failure, backup, recovery, and cost control.

The learner operates and verifies the Linux, container, pipeline, server, automation, observability, recovery, and cloud boundaries around the workload.

## Local request and operations path

```text
Windows browser or API client
        |
        v
Nginx on separate Ubuntu 24.04 VM
        |
        v
FastAPI container <-> PostgreSQL container
        |
        +--> structured logs and request IDs
        +--> Prometheus metrics -> Grafana dashboards/alerts
        +--> scheduled backup -> clean restore drill
```

The Ubuntu 24.04 WSL2 distribution is the workstation for code, Git, Docker, CI configuration, Ansible, and Terraform. The VirtualBox VM was rebuilt to supported Ubuntu 24.04 during M05 and remains a separate server for SSH, firewall, permissions, Nginx, deployment, monitoring, failure, and recovery practice.

## Delivery path

```text
source -> pull request checks -> protected main -> GHCR digest
                                                |
                                                +-> local VM deployment
                                                +-> AWS deployment through Ansible and SSM
```

Deployments consume immutable image digests. The server does not rebuild application source.

## Core AWS path

```text
Terraform -> AWS APIs -> network/IAM/SSM/EC2/EBS/private S3
Ansible -> SSM + temporary private S3 transfer -> EC2 configuration
GitHub Actions -> restricted OIDC role -> SSM digest deployment
EC2 workload -> CloudWatch logs, metrics, and alarms
PostgreSQL backup -> encrypted private S3 -> timed clean restore
```

The cloud core demonstrates infrastructure, identity, secure delivery, monitoring, recovery, drift, destroy, recreate, and billing verification without requiring an always-running public website. Systems Manager replaces inbound SSH. CloudWatch replaces duplicating the full local monitoring stack on a small EC2 instance.

## Security boundaries

- FastAPI, PostgreSQL, metrics, dashboards, and Docker APIs are not unintentionally public.
- Local VM exposure is explicitly inspected because Docker-published ports can interact with firewall filtering.
- Cloud administration uses Systems Manager and has no inbound SSH.
- GitHub uses short-lived, repository/environment-restricted OIDC credentials.
- Terraform state and database backups are private and encrypted.
- Application secrets, database credentials, private keys, account identifiers, and sensitive evidence never enter Git or logs.
- MFA, least privilege, non-root containers, dependency/container/IaC scanning, safe logs, recovery proof, and threat review are integrated across the core.

## Optional public architecture

A paid domain, public DNS, trusted HTTPS, and a permanently reachable dashboard require a separate cost/security decision. Loki, Alloy, external email notification, automatic rollback, Kubernetes, managed databases, and load balancers are also optional extensions, not core completion requirements.
