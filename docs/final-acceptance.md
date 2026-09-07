# Final acceptance

Release: `v1.0.0`
Acceptance date: 2026-09-07

## Gate results

| Acceptance gate | Result | Evidence |
|---|---|---|
| Public setup is reproducible | Pass | [Fresh-clone acceptance](evidence/fresh-clone-acceptance.md) |
| Local system can be demonstrated without secrets | Pass | [Demo runbook](demo-runbook.md) |
| Failure and recovery behavior is verified | Pass | [Local demo evidence](evidence/m12-local-demo.txt) and [database postmortem](postmortems/m11-database-dependency-incident.md) |
| Architecture and operations are documented | Pass | [Architecture](architecture.md), [runbooks](runbooks.md), and [integrated audit](integrated-cloud-audit.md) |
| Public claims map to evidence | Pass | [Evidence index](evidence/README.md) |
| Limitations are explicit | Pass | [Architecture](architecture.md) and [integrated audit](integrated-cloud-audit.md) |
| Cloud resources were removed | Pass | [Cloud teardown](cloud-teardown.md) |
| Delayed billing was reconciled honestly | Pass with timing boundary | Cost Explorer remained effectively USD 0.00 but estimated, not a finalized invoice |
| Local documentation links | Pass | 22 Markdown files checked with no missing local target after public-documentation curation |
| Sensitive-value pattern scan | Pass | No AWS access key, private key, account identifier, or secret assignment found in tracked files |
| Required continuous-integration checks | Pass | Python quality, container smoke test, Terraform validation, security, and CI trust checks |

## Accepted limitations

- The verified AWS environment was temporary and is intentionally offline.
- Customer-managed KMS key deletion uses an AWS waiting period; the scheduled
  deletion was recorded during teardown rather than misreported as immediate.
- The Cost Explorer value was estimated and may change when billing finalizes.
- The single-instance architecture is a learning lab, not a highly available
  production topology.
- The clean-clone test validates Terraform syntax without recreating chargeable
  cloud resources.

## Release meaning

`v1.0.0` means the approved portfolio scope is implemented, tested, documented,
demonstrable, reproducible locally, supported by sanitized evidence, and closed
with an explicit cloud-cost boundary. It does not mean the service is currently
publicly hosted or that the laboratory design meets production scale or
availability requirements.
