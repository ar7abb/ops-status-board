# Terraform compute, storage, and backup design

M09-T04 defines the resources that will later run and protect the AWS workload. The configuration has been formatted, validated, and security-scanned, but it has not been planned or applied. No workload resource exists yet.

## The simple model

```text
EC2 = the virtual computer
EBS = the computer's attached disk
S3  = independent object storage for recovery files
KMS = the controlled encryption key for those files
```

Terraform defines one Ubuntu 24.04 `t3.micro` instance in the existing public subnet. It receives an explicit public IPv4 address so its SSM Agent can initiate outbound HTTPS connections. Its security group still has no inbound rules or SSH access.

## Root disk lifecycle

The instance has a 25 GiB encrypted `gp3` root EBS volume. Stopping the instance preserves the volume and its data. Terminating the instance deletes this root volume because `delete_on_termination` is enabled.

This disk holds the operating system, Docker, images, application files, and live PostgreSQL data. It is disposable infrastructure, not the independent recovery copy.

## Backup lifecycle

PostgreSQL backup archives and checksums will later be uploaded under the `postgresql/` prefix in a separate S3 bucket. The bucket:

- blocks all public access;
- rejects non-TLS requests;
- disables ACL-based ownership;
- encrypts objects with a rotating customer-managed KMS key;
- enables S3 Bucket Keys to reduce KMS request traffic;
- enables versioning;
- expires current backup objects after 30 days;
- removes noncurrent versions after 7 days;
- removes incomplete multipart uploads after 7 days; and
- resists accidental Terraform destruction and refuses deletion while objects remain.

Destroying EC2 therefore deletes its root disk but does not delete the independent S3 recovery objects. The protected bucket and KMS key require an explicit, evidence-preserving teardown procedure later.

## Least-privileged machine access

The existing EC2 role keeps its Systems Manager policy. A new inline policy permits only:

- listing the backup bucket under `postgresql/`;
- uploading and downloading objects under `postgresql/*`; and
- using only the backup KMS key to generate data keys and decrypt backups.

It does not grant access to unrelated buckets or objects. Human deployment/session permissions remain separate from this machine role.

## Cost and approval boundary

The future cost-bearing items include EC2 runtime, 25 GiB EBS storage, one public IPv4 address, S3 storage/requests, and one customer-managed KMS key. Current official AWS pricing must be reviewed in M09-T05 before a saved plan receives explicit approval. Promotional credits do not replace that review or the USD 5 out-of-pocket target.

M09-T04 does not run `terraform plan` or `terraform apply`. The instance ID and backup bucket name are declared as Terraform outputs for later operator verification only.

## Optional scaling follow-up

The core remains one instance. A later short-lived scaling lab may evaluate a launch template, multiple application instances, health checks, load testing, shared-state behavior, and complete cleanup. Merely launching two independent virtual machines would not prove that the stateful application scales correctly.
