# PostgreSQL Backup and Restore Runbook

This runbook covers logical backup and clean restore verification for the
PostgreSQL database used by Ops Status Board.

It is designed for the Ubuntu server deployment whose root-owned Compose file
is `/opt/ops-status-board/compose.yaml`.

## Safety rules

- Never print or copy the contents of the private environment files.
- Never restore a test archive over the live `ops_status_board` database.
- Verify restores in the disposable `ops_status_board_restore_check` database.
- Do not run `docker compose down --volumes`; it deletes PostgreSQL data.
- Record the backup filename, UTC creation time, size, and SHA-256 checksum.
- A backup is not considered verified until a clean restore succeeds.

## Check service health

```bash
sudo docker compose \
  -f /opt/ops-status-board/compose.yaml \
  ps
```

The `db` container must be healthy before starting.

## Create a logical backup

Create the protected backup directory:

```bash
sudo install -d \
  -m 700 \
  -o root \
  -g root \
  /var/backups/ops-status-board
```

Choose a timestamped backup filename:

```bash
backup_stamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_path="/var/backups/ops-status-board/ops-status-board-${backup_stamp}.dump"
```

Create a custom-format PostgreSQL archive inside the database container:

```bash
sudo docker compose \
  -f /opt/ops-status-board/compose.yaml \
  exec -T db \
  sh -c 'pg_dump \
    --username="$POSTGRES_USER" \
    --dbname="$POSTGRES_DB" \
    --format=custom \
    --file=/tmp/ops-status-board.dump'
```

Copy the archive to the protected host directory:

```bash
sudo docker compose \
  -f /opt/ops-status-board/compose.yaml \
  cp db:/tmp/ops-status-board.dump "$backup_path"

sudo chmod 600 "$backup_path"
```

Record its metadata and checksum:

```bash
sudo stat -c '%A %U:%G %s bytes %y %n' "$backup_path"
sudo sha256sum "$backup_path"
```

Remove only the temporary container copy:

```bash
sudo docker compose \
  -f /opt/ops-status-board/compose.yaml \
  exec -T db \
  rm /tmp/ops-status-board.dump
```

## Verify a clean restore

Set `backup_path` to the archive being tested:

```bash
backup_path="/var/backups/ops-status-board/REPLACE_WITH_BACKUP_NAME.dump"
```

Copy it into the database container:

```bash
sudo docker compose \
  -f /opt/ops-status-board/compose.yaml \
  cp "$backup_path" db:/tmp/restore-check.dump
```

Confirm that PostgreSQL can read the archive:

```bash
sudo docker compose \
  -f /opt/ops-status-board/compose.yaml \
  exec -T db \
  sh -c 'set -eu
    pg_restore --list /tmp/restore-check.dump > /tmp/restore-check.list
    head -n 20 /tmp/restore-check.list'
```

Confirm that the disposable database does not already exist:

```bash
sudo docker compose \
  -f /opt/ops-status-board/compose.yaml \
  exec -T db \
  sh -c 'psql \
    --username="$POSTGRES_USER" \
    --dbname=postgres \
    --tuples-only \
    --no-align \
    --command="SELECT datname FROM pg_database WHERE datname = \$\$ops_status_board_restore_check\$\$;"'
```

The command must return no database name before continuing.

Create the empty disposable database:

```bash
sudo docker compose \
  -f /opt/ops-status-board/compose.yaml \
  exec -T db \
  sh -c 'createdb \
    --username="$POSTGRES_USER" \
    --template=template0 \
    ops_status_board_restore_check'
```

Restore the archive:

```bash
sudo docker compose \
  -f /opt/ops-status-board/compose.yaml \
  exec -T db \
  sh -c 'pg_restore \
    --username="$POSTGRES_USER" \
    --dbname=ops_status_board_restore_check \
    --no-owner \
    --no-privileges \
    --exit-on-error \
    /tmp/restore-check.dump'
```

Verify the restored database:

```bash
sudo docker compose \
  -f /opt/ops-status-board/compose.yaml \
  exec -T db \
  sh -c 'psql \
    --username="$POSTGRES_USER" \
    --dbname=ops_status_board_restore_check \
    --command="SELECT current_database() AS database, count(*) AS incidents FROM incidents;"'
```

The restored count must match the source database at backup time.

## Clean up the verification database

Remove only the disposable database:

```bash
sudo docker compose \
  -f /opt/ops-status-board/compose.yaml \
  exec -T db \
  sh -c 'dropdb \
    --username="$POSTGRES_USER" \
    ops_status_board_restore_check'
```

Remove only the temporary archive copy inside the container:

```bash
sudo docker compose \
  -f /opt/ops-status-board/compose.yaml \
  exec -T db \
  rm -f /tmp/restore-check.dump /tmp/restore-check.list
```

Confirm the application is still ready:

```bash
curl --fail --show-error --silent \
  http://127.0.0.1/health/ready
```

## Recovery evidence

For every verification exercise, record privately:

- backup filename and UTC timestamp;
- archive size;
- SHA-256 checksum;
- source incident count;
- restored incident count;
- restore result;
- cleanup result; and
- final application readiness result.

Do not commit environment files, credentials, tokens, private IP addresses, or
private recovery evidence.
