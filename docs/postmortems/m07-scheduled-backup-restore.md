# M07 Scheduled Backup and Clean Restore Verification

## Summary

A scheduled logical PostgreSQL backup was added for the Ops Status Board lab
server and verified through a clean restore drill.

This was a controlled resilience exercise, not a production incident.

## Backup policy

- A systemd timer starts a backup shortly after VM boot.
- The timer repeats after each successful 24-hour interval while the VM remains
  online.
- The service keeps the seven newest managed logical PostgreSQL archives.
- Each archive has a SHA-256 checksum.
- The backup service prevents concurrent runs with a lock.

## Verification performed

1. Confirmed the backup timer was active and had run successfully.
2. Confirmed a new timestamped archive existed in the protected backup
   directory.
3. Verified the archive checksum.
4. Restored the archive into a separate disposable PostgreSQL database.
5. Queried the restored `incidents` table successfully.
6. Removed the disposable restore database and temporary container archive.
7. Confirmed the protected archive remained after cleanup.

The live database was never used as a restore target.

## Result

The backup and clean restore workflow completed successfully. The restored
database contained the expected schema and was queryable.

## Limitation and follow-up

The lab VM is not powered on continuously. Its practical recovery point
objective depends on the most recent successful backup; it is not a guaranteed
calendar-based recovery point while the VM is off.

Future scheduled-backup failures should be investigated through the systemd
service journal, followed by a controlled backup, checksum check, and clean
restore verification.