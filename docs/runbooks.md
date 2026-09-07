# Operator runbook index

Use this page to choose the procedure that matches the environment and incident.
Never paste real secrets, Terraform state, private addresses, or account-specific
identifiers into an issue, pull request, terminal transcript, or screenshot.

## Local workstation and Compose

The root [`README.md`](../README.md#quick-local-demonstration) contains the supported
local lifecycle: create private environment files, validate Compose, start the
database, run migrations, start the application, verify readiness, and stop the
stack without deleting its named volume.

Use [`docs/recovery-runbook.md`](recovery-runbook.md) for logical PostgreSQL
backup, checksum verification, an isolated restore target, record comparison,
and safe cleanup.

## Separate Ubuntu practice server

- [`docs/ansible-ssm-deployment.md`](ansible-ssm-deployment.md) explains the
  reusable Ansible roles and inventory boundary. Its SSM sections describe the
  retired AWS path; use the standard inventory for the separate VM.
- [`docs/observability.md`](observability.md) documents the local
  Prometheus/Grafana stack, capacity budget, dashboards, and alert drill.
- [`docs/postmortems/m07-scheduled-backup-restore.md`](postmortems/m07-scheduled-backup-restore.md)
  records scheduled backup and clean restore evidence.

## AWS infrastructure and operations

The cloud workload is intentionally destroyed. These documents are reproduction
and evidence guides, not instructions to apply infrastructure without a fresh
cost/security review and explicit approval.

- [`docs/terraform-remote-state.md`](terraform-remote-state.md): bootstrap/state
  ordering, locking, recovery, and teardown boundaries.
- [`docs/terraform-network-iam-ssm.md`](terraform-network-iam-ssm.md): VPC,
  no-inbound security group, IAM role/profile, and Systems Manager path.
- [`docs/terraform-compute-storage.md`](terraform-compute-storage.md): EC2, EBS,
  S3 backup storage, KMS, retention, and least privilege.
- [`docs/terraform-drift-recreation.md`](terraform-drift-recreation.md): drift,
  reviewed plan/apply, destroy/recreate, and equivalence checks.
- [`docs/cloudwatch-observability.md`](cloudwatch-observability.md): agent,
  log/metric/alarm flow, investigation, and alarm recovery.
- [`docs/github-oidc-delivery.md`](github-oidc-delivery.md): protected GitHub
  environment, temporary identity, trust scope, and SSM target verification.
- [`docs/cloud-release-runbook.md`](cloud-release-runbook.md): immutable digest
  deployment, health gates, failure visibility, and explicit rollback.

## Incidents, audit, and teardown

- [`docs/postmortems/m11-database-dependency-incident.md`](postmortems/m11-database-dependency-incident.md):
  correlate client symptoms, request IDs, application errors, and alarms before
  recovering PostgreSQL.
- [`docs/integrated-cloud-audit.md`](integrated-cloud-audit.md): review IAM,
  network, host, container, delivery, data, observability, and limitations as one
  system.
- [`docs/cloud-teardown.md`](cloud-teardown.md): preserve evidence, destroy the
  workload before its backend, reconcile partial failures, inventory leftovers,
  and separate immediate cleanup from delayed billing.

## Universal verification pattern

For every operational change:

1. Establish a healthy baseline and a recovery point.
2. Identify the exact environment and target.
3. Preview the change and its data/cost/security impact.
4. Apply only the reviewed change.
5. Verify the intended behavior and a useful failure path.
6. Re-run the automation to check convergence or idempotence.
7. Inspect independent runtime/provider evidence.
8. Clean up temporary resources and record honest limitations.
