# Local observability

The local observability lab monitors the Ops Status Board deployment on the
separate Ubuntu 24.04 VirtualBox server. It is deliberately private and
resource-constrained. This is a learning and recovery environment, not a
production monitoring recommendation.

## Request and metrics path

```text
Windows browser
    -> UFW-restricted port 80
    -> Nginx /grafana/
    -> Grafana on 127.0.0.1:3000
    -> Prometheus on the private Compose network
    -> FastAPI /metrics on app:8000
```

PostgreSQL and Prometheus have no host-published ports. FastAPI and Grafana bind
only to server loopback. Nginx is the single browser-facing entry point, and
UFW limits HTTP access to the trusted workstation.

## Capacity budget

The pre-deployment VM baseline was one vCPU and 2 GiB RAM. The root filesystem
had approximately 4 GiB available before the monitoring images and data were
added.

| Service | Memory limit | CPU limit | Persistence |
|---|---:|---:|---|
| PostgreSQL | 512 MiB | 0.50 | Named database volume |
| FastAPI | 512 MiB | 0.50 | Stateless container |
| Prometheus | 256 MiB | 0.25 | Managed host directory |
| Grafana | 256 MiB | 0.25 | Managed host directory |

The memory ceilings total 1.5 GiB. CPU limits total 1.5 CPUs on a one-vCPU VM;
they are ceilings rather than reservations, so simultaneous load will cause
contention. This is acceptable for the controlled lab but must be measured
again before increasing scrape volume or retention.

Prometheus retains at most seven days or 512 MB, whichever limit is reached
first. Grafana state is persisted but does not have an independent size cap, so
filesystem usage remains an operator check.

## Immutable images and security decision

The role pins exact multi-platform image-index digests:

- Prometheus `main-distroless`:
  `sha256:ad35927d381b41cb12367d4a052c891b88ef63ef51b2635bd64384465179a774`
- Grafana `nightly-distroless-slim`:
  `sha256:0e129ffd8db39fda955414b47c490557e4ffb3f9dc8af08a6095770d79b49606`

On 2026-08-21, both exact digests passed the project's blocking Trivy gate:
HIGH/CRITICAL vulnerability and secret scanning, `--ignore-unfixed`, and exit
code 1 for blocking findings. A broader scan still reported the unknown-severity
Go advisory `GO-2026-5932`, with no fixed version available at that time.

Stable upstream images tested during selection contained blocking
HIGH/CRITICAL findings. The selected images are official upstream development
builds, so they reduce the findings seen by the configured gate but introduce
compatibility and regression risk. This is an explicit local-lab exception,
not a claim that the images are vulnerability-free or production-approved.
Re-scan the exact candidate digest and repeat the smoke test before every image
change.

## Credentials and persistence

The application currently exposes one bearer credential for protected writes
and metrics. Ansible derives Prometheus's token file from that existing private
server configuration, never logs its value, stores the file outside Git, and
mounts it read-only into Prometheus. A separate read-only metrics identity is a
future application-security improvement.

Grafana's administrator password is generated once on the managed server. Its
environment file is root-owned with mode `0600`; the generated value is neither
templated into source control nor printed by Ansible. Prometheus and Grafana
data survive container replacement through role-managed host directories with
container-specific numeric ownership.

## Verification evidence

The deployment was verified on 2026-08-21:

- the Ansible play completed with no unreachable or failed hosts;
- Compose showed PostgreSQL and FastAPI healthy, with Prometheus and Grafana
  running;
- FastAPI remained available through Nginx at `/health/ready`;
- Grafana's `/grafana/api/health` reported a healthy database;
- `promtool query instant ... up` returned
  `up{instance="app:8000", job="ops-status-board"} => 1`;
- Grafana Explore returned the same `up` series through the provisioned data
  source; and
- an immediate repeat Ansible run reported `changed=0`, proving idempotence.

## Known boundaries

- The local HTTP route does not provide TLS; UFW restricts it to the trusted
  workstation.
- Prometheus is not a general-purpose log store. Structured log and request-ID
  investigation remains a separate M07 task.
- Dashboard provisioning, alert rules, outage drills, and scheduled recovery
  work are not completed by this core deployment.
- Development/nightly image stability and the shared metrics/write credential
  must remain visible risks until replaced by stable, clean candidates and a
  dedicated metrics identity.
