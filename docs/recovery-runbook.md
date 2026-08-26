# PostgreSQL Backup and Restore Runbook

This runbook covers the scheduled logical PostgreSQL backups and clean restore
verification for Ops Status Board.

The deployment uses a root-owned Compose file at
`/opt/ops-status-board/compose.yaml`.

## Scope and safety rules

- These archives contain PostgreSQL schema and data only. They do not back up
  the whole VM, Docker images, Nginx configuration, Grafana data, or secrets.
- Never print or copy private environment-file contents.
- Never restore an archive over the live `ops_status_board` database.
- Restore tests use the separate `ops_status_board_restore_check` database.
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

## Verify the newest archive

Select the newest managed archive without printing private configuration:

```bash
latest_backup="$(
  sudo find /var/backups/ops-status-board \
    -maxdepth 1 \
    -type f \
    -name 'ops-status-board-????????T??????Z.dump' \
    -printf '%T@ %p\n' |
    sort -nr |
    head -n 1 |
    cut -d' ' -f2-
)"

printf '%s\n' "$latest_backup"
sudo sha256sum --check "${latest_backup}.sha256"
```

The checksum result must end in `OK`.

## Verify a clean restore

Choose a protected archive and a disposable database name:

```bash
backup_path="/var/backups/ops-status-board/REPLACE_WITH_BACKUP_NAME.dump"
```

Confirm the disposable database does not already exist:

```bash
sudo docker compose \
  -f /opt/ops-status-board/compose.yaml \
  exec -T db \
  sh -c 'psql \
    --username="$POSTGRES_USER" \
    --dbname=postgres \
    --tuples-only \
    --no-align \
    --command "SELECT datname FROM pg_database;"' |
  grep -Fx 'ops_status_board_restore_check' || true
```

The command must return no database name before continuing.

Copy the archive into the database container temporarily:

```bash
sudo docker compose \
  -f /opt/ops-status-board/compose.yaml \
  cp "$backup_path" db:/tmp/ops-status-board-restore-check.dump
```

Create the empty disposable database:

```bash
sudo docker compose \
  -f /opt/ops-status-board/compose.yaml \
  exec -T db \
  sh -c 'createdb \
    --username="$POSTGRES_USER" \
    ops_status_board_restore_check'
```

Restore into that database only:

```bash
sudo docker compose \
  -f /opt/ops-status-board/compose.yaml \
  exec -T db \
  sh -c 'pg_restore \
    --username="$POSTGRES_USER" \
    --dbname=ops_status_board_restore_check \
    --exit-on-error \
    /tmp/ops-status-board-restore-check.dump'
```

Verify the restored schema and data are queryable:

```bash
sudo docker compose \
  -f /opt/ops-status-board/compose.yaml \
  exec -T db \
  sh -c 'psql \
    --username="$POSTGRES_USER" \
    --dbname=ops_status_board_restore_check \
    --tuples-only \
    --no-align \
    --command "SELECT current_database(), count(*) FROM incidents;"'
```

The result must name `ops_status_board_restore_check`. The incident count must
match the live database at the time the archive was created.

## Clean up after the restore test

Delete only the disposable database and temporary container copy:

```bash
sudo docker compose \
  -f /opt/ops-status-board/compose.yaml \
  exec -T db \
  sh -c 'dropdb \
    --username="$POSTGRES_USER" \
    ops_status_board_restore_check && \
    rm -f /tmp/ops-status-board-restore-check.dump'
```

Confirm the live application remains ready:

```bash
curl --fail --show-error --silent \
  http://127.0.0.1/health/ready
```

## Recovery evidence and postmortem notes

Record privately after every restore verification:

- archive filename, UTC timestamp, size, and checksum result;
- timer and service result;
- disposable restore database name;
- restored incident count;
- cleanup result; and
- final application readiness result.

For a failed scheduled backup, preserve the service journal, identify whether
the database or Docker service was unavailable, fix the cause, run one
controlled backup, verify its checksum, and repeat the clean restore test.

Do not commit credentials, tokens, private addresses, private recovery
evidence, or archive contents.
