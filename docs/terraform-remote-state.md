# Terraform Remote State

This document defines the protected Terraform state design, cost boundary, and
recovery rules for the Ops Status Board AWS environment.

## State ownership

The `infra/bootstrap` configuration creates and protects the S3 state bucket.
Its own state starts locally because the bucket cannot store state before it
exists.

The `infra/aws` configuration is initialized to use that bucket as its remote
backend. Its state object will use a project-specific key and native S3 locking
when workload state is first written.

No account identifier, real bucket name, credential, saved plan, private
variable value, or raw state content belongs in Git.

## Protection controls

The state bucket uses:

- all four S3 Block Public Access settings;
- default SSE-S3 encryption with S3-managed keys;
- versioning for recovery from overwrite or deletion;
- a bucket policy that denies requests without TLS;
- Terraform `prevent_destroy` protection while the lifecycle rule remains in
  configuration; and
- `force_destroy = false` so a non-empty bucket is not emptied automatically.

The main Terraform backend uses `use_lockfile = true` so concurrent writers
cannot update the same state safely at the same time. Because bucket versioning
is enabled, completed lock operations can leave noncurrent lock versions and
delete markers that use normal S3 storage.

## Current cost plan

Rates were checked for S3 Standard in Europe (Stockholm) on 2026-08-30.

| Component | Current unit price | Conservative project assumption |
| --- | ---: | ---: |
| S3 Standard storage, first 50 TB | USD 0.023 per GB-month | 100 state versions at 1 MB each |
| PUT, COPY, POST, or LIST requests | USD 0.005 per 1,000 requests | 1,000 requests per month |
| GET and other requests | USD 0.004 per 10,000 requests | 10,000 requests per month |
| SSE-S3 encryption | No additional encryption fee | Enabled |
| Block Public Access and bucket policy | No separate feature fee | Enabled |

Under these deliberately high assumptions, expected remote-state usage remains
below approximately USD 0.02 per month. This is an estimate, not a spending
guarantee. Every retained version uses normal storage, and actual usage must be
checked in AWS Billing and Cost Management.

Sources:

- <https://aws.amazon.com/s3/pricing/>
- <https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonS3/current/eu-north-1/index.json>

## Recovery rules

State recovery is a controlled incident action, not a routine Terraform step.

Before restoring state:

1. Stop all Terraform runs and confirm that no legitimate writer is active.
2. Preserve the current state version and relevant timestamps as private
   evidence.
3. Identify a known-good S3 object version without printing state contents.
4. Confirm the selected version belongs to the expected backend key.
5. Obtain task-scoped approval before changing the current state object.

Restore the selected earlier content as a new current object version. Do not
immediately delete the damaged version or other history. After restoration:

1. Pull the restored state without printing private values publicly.
2. Verify that Terraform can parse it;
3. compare state with the expected AWS inventory;
4. run a refresh-only or normal read-only plan;
5. reject any unexpected create, replace, or destroy action; and
6. resume writes only after the mapping is understood.

A stale `.tflock` object may be removed only after proving that no Terraform
process or automation run still owns it. Removing a lock does not repair state,
and restoring state does not prove that a lock is stale.

If the local bootstrap state is lost, do not run `apply` blindly. Preserve
evidence, identify the existing bucket and protection resources, rebuild their
Terraform mappings with controlled imports, and review a no-change plan before
continuing.

## Teardown boundary

The workload state must be preserved or deliberately disposed of before the
state bucket is removed. Terraform `prevent_destroy` must be removed only during
the final approved teardown. A successful `terraform destroy` is not sufficient
evidence by itself; S3 versions, lock objects, the bootstrap state, AWS
inventory, and delayed billing must also be checked.
