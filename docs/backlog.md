# Ops Status Board Backlog

This backlog parks possible extensions outside the approved 69-task core. An item here is neither promised nor scheduled and cannot block `v1.0.0`.

## Optional extensions

### Expanded observability

- Loki and Alloy for centralized log aggregation
- advanced Grafana provisioning
- external email notifications

The core already teaches structured logs, request-ID investigation, Prometheus/Grafana locally, and CloudWatch in AWS. Add these only if they answer a new operational question within the available VM capacity.

### Public website path

- paid domain and DNS
- trusted public HTTPS
- permanently reachable dashboard

This requires a separate cost, exposure, certificate-renewal, privacy, and teardown decision. A live public URL is not required for the reproducible portfolio.

### Delivery and failure depth

- automatic deployment rollback with migration compatibility
- repeated disk-pressure and bad-configuration drills
- a larger multi-part security audit

The core includes one deliberate CI failure, one deployment failure with manual rollback, one alert/outage drill, integrated security review, backup/restore, and postmortems. Repeat only when a new learning objective justifies it.

### Platform expansion

- short-lived multi-instance scaling lab using a launch template, health checks, and load testing
- optional JavaScript frontend
- Kubernetes
- microservices
- managed database
- load balancer

These substantially change architecture, cost, and ownership. Multiple independent instances alone do not prove scalability; a promoted scaling lab must address traffic distribution, shared state, health, and cleanup. Kubernetes should be a separate follow-on project that solves a stated scaling, reliability, or team-workflow need.

## Promotion rule

Before an extension becomes approved work, record its user/portfolio benefit, dependencies, estimated sessions, cloud cost, security and operational risk, effect on completed work, recovery path, and explicit blueprint decision. Until then it remains parked.
