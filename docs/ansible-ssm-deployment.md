# Ansible deployment through AWS Systems Manager

## Purpose

Terraform creates and tracks the AWS infrastructure. Ansible then configures
the operating system inside the EC2 instance. Systems Manager provides the
transport, so the instance needs no inbound SSH rule or key pair.

## Connection path

```text
Ansible in WSL
  -> temporary AWS browser-login credentials
  -> Systems Manager service
  -> SSM Agent on EC2
  -> temporary private S3 module transfer
  -> privileged Ansible module execution
```

The controller needs the Session Manager plugin, `amazon.aws`, `boto3`, and
`botocore[crt]`. The CRT extra supports the AWS CLI login credential provider.
The AWS profile and private inventory both use the Stockholm region.

## Runtime-secret boundary

Terraform creates random database and administrator credentials as encrypted
Standard Parameter Store values. The instance profile grants the workload only
the required parameter reads and KMS decryption. During configuration, the
instance installs a pinned AWS CLI v2 from AWS's HTTPS installer, retrieves the
values locally, and materializes two root-owned `0600` environment files.
Secret values are not committed, copied into the public inventory, or logged by
Ansible.

## Cloud-specific role choices

The cloud playbook reuses the project's established roles while changing only
the environment-specific boundaries:

- SSH and UFW management are disabled because Systems Manager is the transport
  and the Terraform security group has no inbound rules.
- Ubuntu package sources use HTTPS because cloud egress permits TCP/443 only.
- Docker, the database, the approved application digest, Nginx, and backup
  scheduling are deployed.
- Prometheus and Grafana remain on the local practice VM; the small cloud
  instance reserves its memory for the application and database.

## Sanitized verification evidence

The deployment was approved and operated through the private SSM inventory.
Verification established:

- Ansible ping succeeded without SSH and privileged execution resolved to
  `root` through `become`.
- The first deployment completed with no failed or unreachable host.
- The readiness endpoint returned HTTP 200 through loopback Nginx.
- The application and PostgreSQL containers were healthy and used pinned image
  digests; the API bound only to `127.0.0.1` and PostgreSQL exposed no host
  port.
- Both runtime files were `600:root:root` without inspecting their contents.
- An immediate repeat playbook run reported `changed=0`.
- The temporary transfer bucket contained zero current objects after use.
- The live security group had zero inbound rules.
- Terraform reported no changes after Ansible configured the operating system.

## Troubleshooting learned

Two controller/host dependency failures were resolved without opening SSH or
making manual server drift:

1. The AWS login credential provider required `botocore[crt]` on the Ansible
   controller.
2. The Ubuntu repositories exposed no installable `awscli` candidate, so the
   role moved to a pinned, idempotent AWS CLI v2 installation from AWS's
   official HTTPS distribution.

The application workload remains active for the controlled drift,
destroy/recreate, cleanup, and cost exercise in M09-T07.
