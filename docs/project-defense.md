# Project defense guide

This guide connects common interview questions to evidence in the repository.
Answers should be explained in plain language and supported with a command,
test, runbook, pull request, postmortem, or release—not memorized as slogans.

## Architecture

**How does one browser request travel through the system?**

Nginx receives traffic on the loopback-published port and proxies it to FastAPI.
FastAPI validates the request, uses SQLAlchemy to read or change PostgreSQL, and
returns JSON or rendered HTML. PostgreSQL is reachable only inside the Compose
network. See [`architecture.md`](architecture.md).

**What is the difference between liveness and readiness?**

Liveness asks whether the application process is running. Readiness asks whether
the application can serve useful traffic, including its database dependency. In
the controlled drill, liveness stayed `200` while readiness became `503` when
PostgreSQL stopped. See [`demo-runbook.md`](demo-runbook.md).

## Containers and configuration

**Why not publish the application and database ports directly?**

Nginx is the controlled entry point. Keeping FastAPI and PostgreSQL private
reduces the exposed attack surface and keeps routing behavior consistent.

**Why use immutable image digests?**

A tag such as `latest` can point to different content tomorrow. A digest names
the exact image bytes that were reviewed, deployed, and can be rolled back.

## Infrastructure and configuration management

**Why use both Terraform and Ansible?**

Terraform creates and tracks cloud resources such as the VPC, IAM role, EC2
instance, and S3 buckets. Ansible configures the running server: packages,
files, services, containers, monitoring, and backup jobs. Terraform answers
“what infrastructure exists?”; Ansible answers “how is this server configured?”

**Why does Terraform need state?**

Configuration describes the desired infrastructure. State maps Terraform
addresses to the real resources it manages, helping it calculate create, update,
or destroy actions and detect drift. State is sensitive and was stored in a
versioned, encrypted, access-controlled S3 backend during the cloud phase.

## Cloud access and delivery

**How did administration work with no inbound SSH rule?**

The SSM agent initiated outbound HTTPS connections to AWS. Its instance profile
supplied temporary role credentials and the SSM core policy authorized agent
operations. Operators used Session Manager through AWS authorization rather than
opening port 22 to the internet.

**Why use GitHub OIDC instead of an AWS access key secret?**

OIDC exchanges a verified workflow identity for short-lived AWS role
credentials. The trust policy limits which repository and environment may assume
the role, removing the need to store a long-lived AWS access key in GitHub.

## Observability and incidents

**How do logs, metrics, and alarms differ?**

Logs describe individual events with context. Metrics measure behavior over
time. Alarms evaluate a metric against a rule and change state when action may be
needed. During the database incident, readiness and 5xx symptoms were correlated
with request and application logs and alarm history.

**What is the strongest troubleshooting story?**

The database-dependency incident is strongest because it contains a controlled
failure, multiple correlated signals, a recovery, verification, and prevention
actions. See the [postmortem](postmortems/m11-database-dependency-incident.md).

## Recovery and cost

**What are RPO and RTO?**

RPO is the maximum acceptable data-loss window. RTO is the target time to restore
service. A daily backup schedule supports an approximately 24-hour RPO; the lab
restore completed in 15 seconds, which is evidence from one small controlled
exercise, not a universal production guarantee.

**Why is `terraform destroy` not the whole teardown check?**

Resources can remain outside state or have delayed deletion. Teardown therefore
also used independent service inventories, a workload-first/backend-last order,
GitHub-variable cleanup, KMS waiting-period recording, and delayed billing review.

## Scaling and limitations

**What changes for a team or higher availability?**

Use multiple application instances across availability zones behind a load
balancer, a managed multi-AZ database, autoscaling, private subnets and endpoints,
central secret rotation, notification routing and on-call ownership, stronger
environment separation, policy-as-code, and larger recovery/load tests.

The current single-instance lab proves operations and automation concepts. It
does not claim high availability, production scale, or current public hosting.

## Practical defense checklist

A reviewer should be able to ask for and receive:

1. a local startup and health demonstration;
2. an explanation of a request from Nginx to PostgreSQL;
3. a readiness failure and recovery demonstration;
4. a Terraform-versus-Ansible explanation;
5. an SSM and OIDC trust-boundary explanation;
6. one alarm or log investigation story;
7. a backup/restore RPO and RTO explanation;
8. evidence that cloud resources and residual cost were checked after teardown;
9. an honest description of limitations and the next production improvements.
