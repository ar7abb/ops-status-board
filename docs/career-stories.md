# Career evidence and interview stories

These statements are supported by repository code, tests, runbooks, reviewed
pull requests, and sanitized evidence. They describe completed lab work, not a
claim that a production service is currently hosted.

## Résumé bullets

- Built and tested a containerized FastAPI/PostgreSQL service behind Nginx,
  including migrations, health checks, persistent storage, least-exposed ports,
  and repeatable Docker Compose operations.
- Provisioned a temporary AWS environment with Terraform, including networking,
  EC2, encrypted S3 backups, IAM least privilege, SSM access without inbound SSH,
  remote state, drift detection, and reviewed destroy/recreate workflows.
- Automated server configuration and application deployment with Ansible over
  AWS Systems Manager, including runtime-secret retrieval, pinned container
  images, idempotence checks, and health verification.
- Implemented CloudWatch logs, custom memory/disk metrics, HTTP 5xx monitoring,
  and alarms; ran controlled failure and recovery drills to correlate service
  symptoms with infrastructure telemetry.
- Implemented protected GitHub Actions cloud delivery using OIDC short-lived AWS
  credentials, environment approval, immutable image digests, post-deployment
  verification, and rollback controls.
- Tested PostgreSQL backup and restore procedures, measured recovery objectives,
  documented an incident postmortem, and verified workload-first, backend-last
  AWS teardown with effectively zero estimated residual cost.

## STAR story: database failure and recovery

**Situation:** A database dependency was deliberately stopped during a controlled
exercise while the application process remained available.

**Task:** Identify the customer-facing symptom, distinguish process health from
dependency health, restore service, and prove that data remained intact.

**Action:** I compared liveness and readiness responses, reviewed application and
platform evidence, restarted the database through the defined operational path,
and re-ran health and data checks. I documented the timeline and prevention
actions in the incident postmortem.

**Result:** Liveness correctly remained `200` while readiness changed to `503`;
after recovery, readiness returned to `200` and the recorded incident was still
present. The drill demonstrated why load balancers and operators need readiness,
not only process liveness.

## STAR story: reproducible cloud recovery

**Situation:** A temporary AWS workload needed to be proven reproducible rather
than treated as a manually maintained server.

**Task:** Remove and recreate the workload safely while protecting state and
recovery evidence.

**Action:** I reviewed saved Terraform plans, applied an ordered destroy and
recreation, redeployed configuration with Ansible over SSM, and verified the
application, monitoring, and drift-free Terraform result.

**Result:** The environment was recreated from versioned configuration and passed
the same health checks. This showed the difference between backing up data and
reproducing infrastructure.

## Honest boundaries

- The AWS environment was a temporary laboratory environment and has been
  intentionally destroyed.
- This design uses one EC2 instance and one local PostgreSQL container; it is not
  a highly available production architecture.
- A higher-traffic system would need managed database services, multiple
  instances across availability zones, load balancing, autoscaling, centralized
  secret rotation, and tested cross-region recovery.
- The strongest evidence is operational: reviewed plans, automated checks,
  failure/recovery drills, idempotence, drift correction, and teardown—not a
  claim of long-running production traffic.
