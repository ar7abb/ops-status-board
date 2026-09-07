# Portfolio evidence index

This index maps public claims to reviewable repository evidence. It intentionally
excludes credentials, private addresses, account/resource identifiers, raw
Terraform state, database dumps, and private coaching records.

## Evidence model

The FastAPI/PostgreSQL application provides a realistic workload. The main
portfolio focus is the operational system around it: Linux environments, Git,
containers, CI/CD, VM administration, Ansible, Terraform, AWS security and cost
controls, observability, incident response, backup/restore, and teardown.

A document explains a design or procedure. Tests and CI show repeatable checks.
A postmortem proves investigation and recovery. A release identifies an immutable
checkpoint. None of these alone proves that a cloud service is still running;
the current architecture and teardown record explicitly state that it is not.

## Application and database lifecycle

| Claim | Evidence |
|---|---|
| Configuration fails closed and secrets stay out of responses/logs | [`src/ops_status_board/config.py`](../../src/ops_status_board/config.py), [`src/ops_status_board/observability.py`](../../src/ops_status_board/observability.py), [`tests/`](../../tests/) |
| Migrations create and evolve PostgreSQL schema | [`migrations/`](../../migrations/), [`compose.yaml`](../../compose.yaml), [`README.md`](../../README.md#quick-local-demonstration) |
| Liveness and readiness represent different failure boundaries | [`src/ops_status_board/routes.py`](../../src/ops_status_board/routes.py), [`README.md`](../../README.md#api-and-operational-contracts) |
| Incident API validates authenticated writes | [`tests/test_incident_routes.py`](../../tests/test_incident_routes.py), [`README.md`](../../README.md#api-and-operational-contracts) |

## Containers and continuous delivery

| Claim | Evidence |
|---|---|
| Compose keeps PostgreSQL private and uses health-gated services | [`compose.yaml`](../../compose.yaml), [`README.md`](../../README.md#quick-local-demonstration) |
| Application image is non-root, health checked, and reproducible | [`Dockerfile`](../../Dockerfile), [release `v0.2`](https://github.com/ar7abb/ops-status-board/releases/tag/v0.2) |
| Pull requests run quality, Terraform, security, and container checks | [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml), [PR #65](https://github.com/ar7abb/ops-status-board/pull/65) |
| Cloud releases use immutable digests and explicit rollback | [`docs/cloud-release-runbook.md`](../cloud-release-runbook.md), [release `v0.5`](https://github.com/ar7abb/ops-status-board/releases/tag/v0.5) |

## Linux, Ansible, and local operations

| Claim | Evidence |
|---|---|
| Reusable roles configure base, security, application, monitoring, backup, and runtime secrets | [`ansible/roles/`](../../ansible/roles/), [`ansible/playbooks/`](../../ansible/playbooks/) |
| Configuration converges and can correct drift | [`ansible/README.md`](../../ansible/README.md), [release `v0.3.0`](https://github.com/ar7abb/ops-status-board/releases/tag/v0.3.0) |
| Monitoring and scheduled restore were operated on a separate server | [`docs/observability.md`](../observability.md), [`docs/postmortems/m07-scheduled-backup-restore.md`](../postmortems/m07-scheduled-backup-restore.md) |

## Terraform and AWS

| Claim | Evidence |
|---|---|
| Bootstrap and workload are separate Terraform roots | [`infra/bootstrap/`](../../infra/bootstrap/), [`infra/aws/`](../../infra/aws/), [`docs/terraform-remote-state.md`](../terraform-remote-state.md) |
| EC2 used no inbound SSH and registered through Systems Manager | [`docs/terraform-network-iam-ssm.md`](../terraform-network-iam-ssm.md), [PR #51](https://github.com/ar7abb/ops-status-board/pull/51) |
| Workload used encrypted EBS and private versioned KMS-encrypted S3 backups | [`docs/terraform-compute-storage.md`](../terraform-compute-storage.md), [PR #52](https://github.com/ar7abb/ops-status-board/pull/52) |
| Terraform detected drift and reproduced the workload after destroy | [`docs/terraform-drift-recreation.md`](../terraform-drift-recreation.md), [release `v0.4`](https://github.com/ar7abb/ops-status-board/releases/tag/v0.4) |
| GitHub used protected OIDC temporary credentials rather than stored AWS keys | [`docs/github-oidc-delivery.md`](../github-oidc-delivery.md), [PR #59](https://github.com/ar7abb/ops-status-board/pull/59) |

## Observability, recovery, and incident response

| Claim | Evidence |
|---|---|
| CloudWatch collected retained logs, disk/memory metrics, and four alarms | [`docs/cloudwatch-observability.md`](../cloudwatch-observability.md), [PR #55](https://github.com/ar7abb/ops-status-board/pull/55) |
| Encrypted backup restored into a clean isolated target in 15 seconds | [`docs/recovery-runbook.md`](../recovery-runbook.md), [PR #62](https://github.com/ar7abb/ops-status-board/pull/62) |
| A controlled database outage correlated readiness, 5xx, request logs, application errors, and alarm recovery | [`docs/postmortems/m11-database-dependency-incident.md`](../postmortems/m11-database-dependency-incident.md), [PR #63](https://github.com/ar7abb/ops-status-board/pull/63) |
| Integrated controls and accepted limitations were reviewed before teardown | [`docs/integrated-cloud-audit.md`](../integrated-cloud-audit.md), [release `v0.9`](https://github.com/ar7abb/ops-status-board/releases/tag/v0.9) |

## Cleanup and current state

| Claim | Evidence |
|---|---|
| Workload was destroyed before its state backend | [`docs/cloud-teardown.md`](../cloud-teardown.md), [PR #65](https://github.com/ar7abb/ops-status-board/pull/65) |
| Independent inventories found no active project cloud resources | [`docs/cloud-teardown.md`](../cloud-teardown.md#final-inventory-evidence) |
| Delayed Cost Explorer remained effectively zero but estimated | [`docs/cloud-teardown.md`](../cloud-teardown.md#billing-boundary) |
| The current cloud design is reproducible but intentionally offline | [`docs/architecture.md`](../architecture.md), [`infra/`](../../infra/) |

## Portfolio demonstration

| Claim | Evidence |
|---|---|
| A local end-to-end demonstration covers startup, an authenticated incident, dependency failure, recovery, and cleanup | [`docs/demo-runbook.md`](../demo-runbook.md), [`m12-local-demo.txt`](m12-local-demo.txt) |
| The live process stayed healthy while database-dependent readiness failed safely | [`m12-local-demo.txt`](m12-local-demo.txt) |
| A disposable fresh clone passed dependencies, tests, lint, containers, migrations, health, and Terraform validation | [`fresh-clone-acceptance.md`](fresh-clone-acceptance.md) |

## Release checkpoints

| Release | Verified scope |
|---|---|
| [`v0.1`](https://github.com/ar7abb/ops-status-board/releases/tag/v0.1) | Workstation, repository, application, database, API, health, and logging foundations |
| [`v0.2`](https://github.com/ar7abb/ops-status-board/releases/tag/v0.2) | Containers, Compose, CI, scanning, and immutable image delivery |
| [`v0.3.0`](https://github.com/ar7abb/ops-status-board/releases/tag/v0.3.0) | Manual VM operations, Ansible, local observability, backup, and recovery |
| [`v0.4`](https://github.com/ar7abb/ops-status-board/releases/tag/v0.4) | Terraform/AWS creation, SSM deployment, drift, destroy, and recreation |
| [`v0.5`](https://github.com/ar7abb/ops-status-board/releases/tag/v0.5) | CloudWatch, protected OIDC delivery, immutable deployment, failure, and rollback |
| [`v0.9`](https://github.com/ar7abb/ops-status-board/releases/tag/v0.9) | Encrypted restore, database incident response, integrated audit, and pre-teardown checkpoint |
| [`v1.0.0`](https://github.com/ar7abb/ops-status-board/releases/tag/v1.0.0) | Sanitized demo, clean-clone acceptance, teardown reconciliation, and final portfolio acceptance |

Final `v1.0.0` records the completed local demonstration, clean-clone
acceptance, final secret/link checks, and teardown/billing reconciliation.
