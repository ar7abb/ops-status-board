# Evidence-preserving AWS teardown

## Purpose

I removed the temporary AWS implementation after completing its restore,
incident, delivery, monitoring, and integrated-audit exercises. I preserved
sanitized evidence first, reviewed every destructive boundary, removed resources
in dependency order, and then checked AWS directly for leftovers.

Release `v0.9` remains the immutable checkpoint for the verified live design.
The repository keeps the Terraform and Ansible configuration needed to explain
and reproduce that design, but it does not claim that the cloud service remains
online.

## Safe order

1. I confirmed that the recovery, incident, audit, repository, and release
   evidence was complete.
2. I inventoried both Terraform states and the matching AWS resource families.
3. I applied a reviewed saved workload destroy plan before touching remote state.
4. I deliberately deleted the approved PostgreSQL backup versions, then removed
   the final empty workload bucket.
5. I proved that the workload state and independent workload inventories were
   empty.
6. I removed stale GitHub environment variables that referenced the destroyed
   deployment role and instance.
7. I applied a separately reviewed saved bootstrap destroy plan.
8. I deliberately deleted the approved remote-state versions and delete markers,
   then removed the final empty backend bucket.
9. I repeated independent AWS and GitHub inventories after both Terraform states
   were empty.

The two Terraform roots made this order possible: Terraform could continue
reading workload state while destroying the workload. I removed the S3 state
foundation only after that state was no longer needed.

## Approval and plan integrity

Each irreversible stage used a saved Terraform plan. I calculated its SHA-256
digest and compared it immediately before applying the plan. When a versioned S3
bucket remained because its existing Terraform state still recorded
`force_destroy = false`, I stopped, reconciled the partial state, emptied only
the explicitly approved bucket history, and generated a new one-resource plan.
I did not turn a failed plan into an unreviewed broad deletion.

This demonstrates an important operational rule: a plan records exact intended
actions, but providers, versioned storage, and partial failures can still leave
work that must be reconciled and verified.

## State and evidence disposition

The following evidence remains in Git:

- Terraform, Ansible, application, test, and delivery configuration;
- sanitized recovery, incident, observability, delivery, and audit documents;
- protected pull-request and immutable release history; and
- this teardown procedure and its count-only verification results.

The following private data was intentionally destroyed:

- encrypted PostgreSQL backup objects and their versions;
- Terraform workload state and lock history; and
- Terraform bootstrap state-object history and delete markers.

Terraform state can contain generated credentials and infrastructure identifiers,
so it was not copied into the public repository. This private history cannot be
recovered. Future cloud recreation starts with a new bootstrap bucket, a new
backend configuration, and reviewed plans from the committed configuration.

## Final inventory evidence

After teardown, direct read-only service inventories returned zero for:

- active project EC2 instances, EBS volumes, network interfaces, and Elastic IPs;
- project VPCs, subnets, security groups, internet gateways, and route tables;
- project CloudWatch log groups and alarms;
- project Systems Manager parameters;
- project IAM roles, instance profiles, and customer-managed policies;
- workload, transfer, backup, and Terraform-state S3 buckets; and
- stale GitHub production variables for the destroyed role and instance.

Both Terraform roots also had empty state after their respective destroys. These
independent checks matter because empty Terraform state can mean either that AWS
deleted a resource or that Terraform merely forgot it.

The customer-managed backup encryption key entered `PendingDeletion`. AWS KMS
enforces a waiting period rather than deleting customer-managed keys immediately.
The alias and dependent workload resources were removed, so the destroyed
application cannot use that key while deletion is pending.

## Billing boundary

The immediate current-month Cost Explorer query returned an estimated amount
effectively equal to USD 0.00. This is an immediate estimate, not finalized
post-teardown billing, because AWS usage and credits can appear later.

A delayed read-only check on 2026-09-07 repeated the complete project inventory:
all checked resource categories remained zero, both Terraform states remained
empty, and the KMS deletion remained scheduled. Cost Explorer returned an
estimated amount effectively equal to USD 0.00. The result closes the delayed
Milestone 11 gate without misrepresenting estimated data as a finalized invoice.
`terraform destroy` did not provide this evidence; the later independent checks
did.

## Junior DevOps lessons

- Preserve useful evidence before deleting the systems that generated it.
- Destroy dependents before foundations: workload first, state backend last.
- Review saved plans and verify their hashes before destructive applies.
- Treat partial failure as reconciliation, not permission to rerun broad deletes.
- Verify Terraform state and AWS service inventories independently.
- Remember that S3 versioning retains old objects and KMS deletion is delayed.
- Remove deployment variables and identities for systems that no longer exist.
- Separate immediate resource cleanup from delayed billing confirmation.
