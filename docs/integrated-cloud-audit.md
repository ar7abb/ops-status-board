# M11 Integrated Cloud Security and Operations Audit

## Purpose

This audit follows the complete path from a reviewed source change to a running
and recoverable cloud service. It checks whether controls at one layer are
supported by evidence at the next layer instead of treating IAM, networking,
containers, delivery, monitoring, and recovery as separate checklists.

The review was performed against the Terraform-managed lab workload in Europe
(Stockholm). Private identifiers, credentials, addresses, backup contents, and
raw error traces are intentionally excluded.

## Audit result

The core controls passed. Two container-deployment findings were remediated and
verified. Several deliberate lab limitations remain accepted and documented.

| Layer | Evidence checked | Result |
| --- | --- | --- |
| Identity and IAM | EC2 assumes its instance role; SSM, backup, Parameter Store, KMS, and CloudWatch permissions are scoped to their required paths/resources; GitHub uses environment-restricted OIDC and one-hour credentials | Pass |
| Network | Security group has zero inbound rules; the only egress rule is TCP/443; administration uses outbound SSM; PostgreSQL has no published host port | Pass |
| Compute and host | EC2 is running, uses required IMDSv2 with hop limit one, and has an encrypted root EBS volume; SSM is Online; root-only runtime files are mode `0600` | Pass |
| Containers | Application and PostgreSQL are healthy; images are digest-pinned; the application runs as `appuser`; application traffic binds to loopback; PostgreSQL data uses a named volume | Pass after remediation |
| Delivery pipeline | Pull-request CI, protected production review, immutable digest validation, short-lived OIDC identity, instance-scoped SSM, serialized release, source/version/readiness gates, visible failure, and separate rollback are documented and previously exercised | Pass |
| Data and recovery | S3 backup versioning, KMS encryption, all four public-access blocks, TLS-only policy, restricted prefix access, current recovery objects, portable checksums, and a clean timed restore were verified | Pass |
| Observability | CloudWatch Agent and backup timer are active; four alarms are `OK`; structured access logs, request IDs, host metrics, dependency-failure detection, and alarm recovery were exercised | Pass |
| Infrastructure reconciliation | Terraform returned detailed exit code `0`; immediate repeat Ansible deployment returned `changed=0`, `failed=0` | Pass |

## Remediated findings

### 1. Unnecessary application-container write and privilege surface

The application already ran as a dedicated non-root user, but its container
root filesystem remained writable and Docker had not explicitly removed its
capabilities or blocked privilege escalation.

The application and one-shot migration services now use:

- a read-only root filesystem;
- a small temporary `/tmp` filesystem for legitimate temporary writes;
- `no-new-privileges`; and
- all Linux capabilities dropped.

An isolated Compose smoke test successfully built the image, migrated a clean
database, started the service, returned healthy readiness and API responses,
and inspected all four runtime controls. The live application was then
recreated through the managed Compose definition and passed the same checks.
PostgreSQL was not given a read-only root filesystem because its managed data
path must remain writable.

### 2. Deferred handler could leave file/runtime drift after a later failure

During deployment, Ansible rendered the hardened Compose file before the backup
role rejected a missing controller-supplied bucket value. Because application
handlers ran only at the end of the play, the file changed but the running
container did not. A correct retry saw no file change and therefore had no
handler to run.

The application role now flushes its notified deployment handler immediately
after rendering a changed Compose definition. This keeps the running workload
aligned even if a later independent role fails. The one existing mismatch was
reconciled once, and the complete immediate repeat run reported zero changes
and zero failures.

## Accepted limitations

- Broad outbound TCP/443 is retained because SSM, signed packages, and approved
  image downloads do not share one stable destination range. Private endpoints
  or a managed egress design would improve isolation but add cost and scope.
- The EC2 instance has a public IPv4 address to reach those services, but zero
  inbound security-group rules make it unavailable for direct inbound access.
- The SSM deployment role is instance-scoped, but the approved shell document
  runs with root-level host authority. Protected repository/environment access
  remains a critical boundary.
- CloudWatch alarms have no external notification destination in the core lab;
  operators inspect their state directly.
- The backup timer runs only while the instance is online, so the scheduled RPO
  upper bound is approximately 24 hours while online, not a calendar guarantee.
- PostgreSQL remains a single-container database on one EC2 host. Managed
  database high availability is outside this cost-controlled learning scope.
- The service is not a public production website and has no trusted public TLS,
  domain, load balancer, or multi-instance failover.

## Verification summary

- SSM reported Online on Ubuntu.
- The security group had zero inbound rules and one TCP/443 egress rule.
- IMDSv2 was required with hop limit one; the root EBS volume was encrypted.
- All four CloudWatch alarms were `OK`.
- Backup storage had versioning, KMS encryption, and all public-access blocks
  enabled, with current encrypted recovery evidence retained.
- The protected GitHub environment had a required reviewer and protected-branch
  deployment policy.
- Live readiness returned HTTP 200; both containers were healthy; PostgreSQL
  had no host-published port; runtime secret files were `600:root:root`.
- The hardened application ran as `appuser` with a read-only root filesystem,
  temporary `/tmp`, no privilege escalation, and zero retained capabilities.
- Terraform reported no changes and the repeat Ansible run reported zero
  changes and zero failures.

## Release meaning

The `v0.9` tag records a verified cloud recovery and integrated-audit
checkpoint. It does not claim production-grade high availability, public
hosting, automatic rollback, or zero residual risk. Cloud teardown and delayed
billing verification remain a separate final Milestone 11 task.
