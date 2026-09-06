# M11 Controlled Database-Dependency Incident

## Summary

A controlled failure exercise stopped the PostgreSQL container while the
application and EC2 instance remained online. The exercise verified that the
service exposed the dependency failure through readiness checks, structured
logs, and the CloudWatch HTTP 5xx alarm, and that normal service returned after
PostgreSQL was restarted.

This was a planned resilience drill, not a production incident. The database
volume was never removed or recreated.

## Impact

- The liveness endpoint remained healthy because the application process was
  still running.
- The readiness endpoint returned HTTP 503 because the application could not
  reach PostgreSQL.
- Database-backed API requests returned HTTP 500 during the failure window.
- No data loss was observed after recovery.
- The controlled disruption lasted approximately 70 seconds.

## Timeline

All times below are UTC on 2026-09-06.

| Time | Event |
| --- | --- |
| 15:12:45 | A ten-minute automatic recovery guard was armed, then PostgreSQL was stopped. |
| 15:12:52 | Readiness requests returned 503 and database-backed API requests returned 500. |
| 15:13:13 | The CloudWatch HTTP 5xx alarm changed from `OK` to `ALARM`. |
| 15:13:55 | PostgreSQL was restarted manually and passed its readiness check. |
| 15:18:13 | After the configured evaluation window, the HTTP 5xx alarm returned to `OK`. |

## Detection and correlation

The failure was visible in several independent signals:

1. `/health/live` continued returning HTTP 200, proving that the application
   process itself was alive.
2. `/health/ready` returned HTTP 503, identifying that the application was not
   ready to serve traffic because a required dependency was unavailable.
3. Structured Nginx access logs recorded the failing paths, status codes, and
   request IDs.
4. Application logs recorded two database operational errors during the
   incident window.
5. The CloudWatch metric filter counted repeated 5xx responses and drove the
   HTTP 5xx alarm from `OK` to `ALARM` and back to `OK` after recovery.
6. EC2 status, disk, and memory alarms stayed `OK`, which narrowed the problem
   to the application dependency rather than the host.

## Root cause

PostgreSQL was intentionally stopped. The application process and host stayed
healthy, but database connections failed until the PostgreSQL container was
started again.

## Recovery

PostgreSQL was restarted with Docker Compose. Recovery was accepted only after:

- PostgreSQL reported that it was ready to accept connections;
- both liveness and readiness returned HTTP 200;
- the database-backed incidents endpoint returned successfully;
- the PostgreSQL container was confirmed running; and
- the CloudWatch HTTP 5xx alarm returned to `OK`.

## Safety controls

- A transient systemd recovery guard would have restarted PostgreSQL after ten
  minutes if manual recovery failed.
- The exercise used `docker compose stop` and `start`; it did not use
  `docker compose down -v` or remove the named database volume.
- The recovery guard was disabled after successful manual recovery.
- No secrets, private addresses, account identifiers, or raw stack traces are
  included in this report.

## Lessons

- Liveness and readiness answer different questions. Liveness shows that the
  process is running; readiness shows whether the service can safely receive
  requests.
- A host can be healthy while an application dependency is broken. Correlating
  alarms, access logs, application logs, and container state makes diagnosis
  faster than relying on one signal.
- Alarm recovery is intentionally delayed by the evaluation window. A healthy
  endpoint does not make an alarm return to `OK` immediately.
- A safe failure drill needs an automatic recovery guard and an explicit rule
  against deleting persistent volumes.

## Follow-up

The current lab correctly exposes database loss through readiness and
monitoring. A future improvement could map expected database-unavailable errors
on database-backed API routes to a deliberate service-unavailable response,
while continuing to keep internal error details out of client responses.
