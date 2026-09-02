# Terraform drift, destruction, and recreation

M09-T07 tested whether the AWS workload could be corrected, removed, and
recreated from reviewed code. The protected Terraform backend was deliberately
outside the workload state and remained available throughout the exercise.
Private identifiers, credentials, state, database contents, and raw cloud
inventory are not published.

## Controlled drift

A harmless EC2 management tag was changed outside Terraform. Terraform then
reported one in-place difference between the configuration and live AWS state:

```text
Plan: 0 to add, 1 to change, 0 to destroy.
```

The saved correction plan was reviewed, hashed, and explicitly approved before
apply. Apply restored the configured tag, and a following plan reported no
changes. This proves the distinction between detection and correction: `plan`
describes the proposed reconciliation, while `apply` performs it.

## Recovery and approval boundaries

Before destruction, the exercise verified a private database recovery copy and
its checksum. The workload buckets were empty, current cost evidence remained
inside the promotional-credit gate, and the protected remote-state foundation
was excluded from the destroy plan.

The exact saved destroy plan proposed:

```text
Plan: 0 to add, 0 to change, 33 to destroy.
```

Its checksum and complete Terraform address inventory were reviewed before a
separate destructive approval. After apply, workload state was empty and direct
inventory checks found no active instance, volume, or workload security-group
rule. The backend independently returned a no-change plan.

The old customer-managed KMS key entered AWS `PendingDeletion` instead of
disappearing immediately. This is expected: AWS KMS enforces a waiting period
for customer-managed key deletion, makes the pending key unusable, and does not
charge for it while deletion is pending. See the AWS documentation for
[deleting KMS keys](https://docs.aws.amazon.com/kms/latest/developerguide/deleting-keys.html)
and [KMS pricing](https://aws.amazon.com/kms/pricing/).

## Equivalent recreation

A fresh saved plan was generated only after cleanup. It proposed the same 33
managed-resource addresses as the destroyed workload:

```text
Plan: 33 to add, 0 to change, 0 to destroy.
```

The new checksum and full address inventory were reviewed under a separate
approval. Terraform then created new network, identity, compute, encrypted
storage, runtime-secret, and configuration-transfer resources. New cloud IDs,
bucket suffixes, and generated secrets were expected; equivalence means the
same reviewed behavior and controls, not identical provider-generated IDs.

The private Ansible inventory was regenerated from new Terraform outputs. SSM
registered the instance without inbound SSH, and Ansible rebuilt the server
from reusable roles. The first run reported expected changes on the empty VM;
the immediate repeat reported:

```text
changed=0  unreachable=0  failed=0
```

Final verification proved:

- HTTP 200 readiness through loopback Nginx;
- healthy application and PostgreSQL containers using pinned image digests;
- root-owned runtime files with mode `0600`;
- zero inbound security-group rules;
- an empty temporary Ansible transfer bucket;
- 33 Terraform-managed workload resources;
- no-change plans for both workload and backend configurations.

The recovery copy was retained as evidence and for the later timed cloud
restore exercise. M09-T07 did not claim that application data was restored;
it proved infrastructure and configuration reproducibility.

## Operational lesson

Terraform creates and tracks cloud infrastructure. Ansible configures the
operating system and deploys the application after a server exists. Remote
state allows Terraform to remember managed cloud objects, while the separate
bootstrap configuration protects the storage that holds that state. Saved
plans, checksums, exact approvals, recovery checkpoints, and post-action
inventory checks turn a dangerous destroy/recreate operation into a controlled,
auditable workflow.
