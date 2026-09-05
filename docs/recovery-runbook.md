# PostgreSQL Backup and Restore Runbook

This runbook covers scheduled local and KMS-encrypted S3 PostgreSQL backups,
plus clean isolated restore verification for Ops Status Board.

The deployment uses a root-owned Compose file at
`/opt/ops-status-board/compose.yaml`.

## Scope and safety rules

- These archives contain PostgreSQL schema and data only. They do not back up
  the whole VM, Docker images, Nginx configuration, Grafana data, or secrets.
- Never print or copy private environment-file contents.
- Never restore an archive over the live `ops_status_board` database.
- Cloud restore tests use a separate disposable PostgreSQL container with no
  published port and temporary storage.
- Never run `docker compose down --volumes`; it deletes PostgreSQL data.
- A backup is not considered verified until its checksum and a clean restore
  both succeed.

## Scheduled backup policy

The root-owned systemd timer `ops-status-board-backup.timer` starts one logical
backup shortly after a VM boot, then repeats after each successful 24-hour
interval while the VM remains online.

The backup service:

- writes custom-format archives to `/var/backups/ops-status-board`;
- creates a SHA-256 checksum beside each archive;
- uploads the archive and checksum beneath `postgresql/` in the private backup
  bucket with the approved customer-managed KMS key;
- fails the complete systemd job when either remote upload fails;
- keeps the seven newest managed archives;
- uses a lock so two backups cannot run at once; and
- removes its temporary archive from the database container.

Because this is a lab VM that is not always powered on, its practical recovery
point objective is based on the most recent successful backup, not a guaranteed
calendar schedule while the VM is off.

## Inspect the schedule and last run

```bash
sudo systemctl list-timers --all --no-pager | \
  grep ops-status-board-backup

sudo journalctl \
  -u ops-status-board-backup.service \
  --no-pager \
  --since "7 days ago"
```

A one-shot service normally becomes inactive after a successful backup. The
timer remaining active is the important scheduling evidence.

To intentionally create one new backup for a controlled test:

```bash
sudo systemctl start ops-status-board-backup.service
```

The cloud playbook receives the destination without committing an
account-specific bucket name:

```bash
export OPS_BACKUP_S3_BUCKET="$(
  terraform -chdir=infra/aws output -raw backup_bucket_name
)"
```

The EC2 instance profile, not a static access key on the server, authorizes the
prefix-scoped S3 and KMS operations.

## Verify the newest encrypted S3 archive

Resolve the bucket from Terraform state and select the intended recovery point.
Do not place the resolved bucket identifier in evidence or Git:

```bash
backup_bucket="$(terraform -chdir=infra/aws output -raw backup_bucket_name)"
dump_key="postgresql/REPLACE_WITH_SELECTED_BACKUP.dump"

aws s3api head-object \
  --bucket "$backup_bucket" \
  --key "$dump_key" \
  --query '[ServerSideEncryption,BucketKeyEnabled]'
```

The encryption result must report `aws:kms`. Download both the selected dump
and its `.sha256` object into a root-only temporary directory, then run
`sha256sum --check`. The result must end in `OK` before restoration.

## Verify a clean isolated restore

Start the RTO clock immediately before downloading the selected objects. Refuse
to continue if the named restore container already exists.

Start an isolated PostgreSQL container from the same pinned database image:

```bash
docker run \
  --detach \
  --name ops-status-board-restore-m11 \
  --network none \
  --tmpfs /var/lib/postgresql/data:rw,noexec,nosuid,size=256m \
  --env POSTGRES_HOST_AUTH_METHOD=trust \
  postgres:16.14@sha256:95206741a5b214807675e14165369d05b93a9cf692223b616d07cca227e74b0b
```

After `pg_isready` succeeds, create a new database and prove the application
table does not exist yet:

```bash
docker exec ops-status-board-restore-m11 \
  createdb --username=postgres restore_verification

docker exec ops-status-board-restore-m11 \
  psql --username=postgres --dbname=restore_verification \
  --tuples-only --no-align \
  --command="SELECT to_regclass('public.incidents') IS NULL;"
```

The clean-target query must return `t`. Copy the verified dump into that
container and restore without applying archive ownership or privileges:

```bash
docker cp SELECTED_BACKUP.dump \
  ops-status-board-restore-m11:/tmp/restore.dump

docker exec ops-status-board-restore-m11 \
  pg_restore \
  --username=postgres \
  --dbname=restore_verification \
  --no-owner \
  --no-privileges \
  --exit-on-error \
  /tmp/restore.dump
```

Verify counts plus a known non-sensitive recovery marker. Do not print record
contents from real backups:

```bash
docker exec ops-status-board-restore-m11 \
  psql --username=postgres --dbname=restore_verification \
  --tuples-only --no-align \
  --command="SELECT count(*) FROM incidents;"
```

Stop the RTO clock only after checksum, restore, schema, count, and marker checks
all pass. The restored count must match the database at backup time.

## Clean up after the restore test

Remove only the explicitly named disposable container and protected temporary
download directory:

```bash
docker rm --force ops-status-board-restore-m11
```

Confirm the live application remains ready:

```bash
curl --fail --show-error --silent \
  http://127.0.0.1/health/ready
```

## Verified M11 recovery result

The controlled cloud drill restored one known synthetic incident from a
checksum-verified, KMS-encrypted S3 object into a clean no-network container.
The measured RTO was 15 seconds. The selected object's observed age at completed
verification was 78 seconds. The scheduled policy still has a practical RPO
upper bound of approximately 24 hours while the instance remains online; the
78-second observation does not replace that honest design limit. The synthetic
live row, disposable container, and temporary downloads were removed, and live
readiness remained healthy.

## Recovery evidence and postmortem notes

Record privately after every restore verification:

- sanitized archive timestamp, size, encryption, and checksum result;
- timer and service result;
- clean-target proof and disposable restore target;
- restored incident count;
- measured RTO and observed recovery-point age;
- scheduled RPO upper bound;
- cleanup result; and
- final application readiness result.

For a failed scheduled backup, preserve the service journal, identify whether
the database or Docker service was unavailable, fix the cause, run one
controlled backup, verify its checksum, and repeat the clean restore test.

Do not commit credentials, tokens, private addresses, private recovery
evidence, or archive contents.
