# Local observability

The local observability lab monitors the Ops Status Board deployment on the
separate Ubuntu 24.04 VirtualBox server. It is deliberately private and
resource-constrained. This is a learning and recovery environment, not a
production monitoring recommendation.

## Data and request paths

```text
Windows browser
    -> UFW-restricted port 80
    -> Nginx /grafana/
    -> Grafana on 127.0.0.1:3000
    -> Prometheus on the private Compose network
       -> FastAPI /metrics on app:8000
       -> Node Exporter on node-exporter:9100
       -> PostgreSQL Exporter on postgres-exporter:9187
```

Prometheus pulls metric samples from the three targets every 15 seconds and
stores time series locally. Grafana queries Prometheus and renders the
provisioned panels; it does not scrape the application or exporters itself.
Node Exporter reads host CPU, memory, and filesystem information through
read-only host mounts. PostgreSQL Exporter connects through the private Compose
network with a dedicated least-privilege database role.

PostgreSQL, Prometheus, Node Exporter, and PostgreSQL Exporter have no
host-published ports. FastAPI and Grafana bind only to server loopback. Nginx
is the single browser-facing entry point, and UFW limits HTTP access to the
trusted workstation.

## Capacity budget

The VM has one vCPU and 2 GiB RAM. The service ceilings are intentionally small:

| Service | Memory limit | CPU limit | Persistence |
|---|---:|---:|---|
| PostgreSQL | 512 MiB | 0.50 | Named database volume |
| FastAPI | 512 MiB | 0.50 | Stateless container |
| Prometheus | 256 MiB | 0.25 | Managed host directory |
| Grafana | 256 MiB | 0.25 | Managed host directory |
| Node Exporter | 128 MiB | 0.10 | Stateless container |
| PostgreSQL Exporter | 128 MiB | 0.10 | Stateless container |

The memory ceilings total 1.75 GiB. CPU limits total 1.7 CPUs on a one-vCPU VM;
they are ceilings rather than reservations, so simultaneous load can cause
contention. This is acceptable for the controlled lab but must be measured
again before increasing scrape volume, retention, or dashboard scope.

Prometheus retains at most seven days or 512 MB, whichever limit is reached
first. Grafana state is persisted but does not have an independent size cap, so
filesystem usage remains an operator check.

Monitoring exposed root-filesystem pressure at about 84% use. After taking a
VM snapshot, the existing LVM logical volume and mounted filesystem were
extended online. The root filesystem grew from about 12 GiB to about 18 GiB,
usage fell to about 55%, and about 5.5 GiB remained unallocated in the volume
group. This was capacity remediation, not a substitute for backups.

## Immutable images and security decisions

The role pins exact multi-platform image-index digests:

- Prometheus `main-distroless`:
  `sha256:ad35927d381b41cb12367d4a052c891b88ef63ef51b2635bd64384465179a774`
- Grafana `nightly-distroless-slim`:
  `sha256:0e129ffd8db39fda955414b47c490557e4ffb3f9dc8af08a6095770d79b49606`
- Docker Hardened Images Node Exporter:
  `sha256:9132a34f18996feaee1c76dcb332d23c8414eb8eff9443d7f04caff3c0d65f8e`
- Docker Hardened Images PostgreSQL Exporter:
  `sha256:d7471e1ae929237fa3e1b11f2c5d78f2ce20b86e2e51b23e0bc52d5711d229f0`

On 2026-08-21, the exact Prometheus and Grafana digests passed the project's
blocking HIGH/CRITICAL Trivy gate with `--ignore-unfixed`. A broader scan still
reported the unknown-severity Go advisory `GO-2026-5932`, with no fixed version
available at that time. Stable upstream images tested during selection
contained blocking HIGH/CRITICAL findings, so the official development builds
are an explicit local-lab exception, not a production recommendation.

On 2026-08-24, the exact authenticated Docker Hardened Images exporter digests
reported zero HIGH/CRITICAL findings under the same blocking policy. They
require registry authentication to pull, which is an operational dependency.
Every candidate digest must be re-scanned and smoke-tested before an update.

## Credentials and persistence

The application currently uses its protected bearer credential for both
administrative writes and Prometheus scraping. Ansible extracts the value from
existing private server configuration without logging it, writes a root-managed
token file outside Git, and mounts that file read-only into Prometheus. A
dedicated read-only metrics identity remains a future application-security
improvement.

Grafana's administrator password and the PostgreSQL Exporter connection data
are generated and retained in root-only mode-`0600` environment files outside
Git. The exporter uses a dedicated PostgreSQL login with `CONNECT` and
`pg_monitor`, not the database superuser. Prometheus and Grafana data survive
container replacement through role-managed host directories.

## Dashboard and alert behavior

The provisioned dashboard answers these operational questions:

- Is the application currently scrapeable?
- What is the HTTP request rate and p95 request duration?
- Are HTTP 5xx responses occurring?
- How much host CPU and memory are available?
- How full is the root filesystem?
- How many PostgreSQL connections are open?

A value of zero means a matching series exists and currently measures zero.
`No data` means the query found no matching series in the selected time range;
for example, no 5xx series exists until at least one matching response has been
observed.

Prometheus also loads `OpsStatusBoardUnavailable`, which becomes pending when
the application target is down and fires after one continuous minute. External
email or chat delivery is optional backlog; the core evidence is the local
pending, firing, and recovered lifecycle.

## Verification evidence

Verification through 2026-08-25 established that:

- Ansible deployed all six services without unreachable or failed hosts;
- FastAPI remained healthy through Nginx and Grafana reported a healthy local
  database;
- Prometheus returned `up == 1` for the application, Node Exporter, and
  PostgreSQL Exporter jobs;
- Node Exporter exposed real host metrics and PostgreSQL Exporter reported
  `pg_up 1` with database activity;
- Grafana rendered application availability, traffic, p95 latency, host CPU,
  available memory, root-filesystem usage, and PostgreSQL connection panels;
- `promtool` validated both the complete Prometheus configuration and its alert
  rule file;
- a controlled application outage moved the alert through pending, firing, and
  recovered states, after which readiness passed again; and
- repeat Ansible runs reported `changed=0` with no failed or unreachable hosts.

The alert-rule work also proved two deployment details: the Prometheus image's
default entrypoint must be overridden when invoking `promtool`, and adding a new
bind mount requires container recreation rather than only restarting the old
container.

## Remaining M07 boundaries

- M07-T03 traced one controlled 404 across the safe client response, FastAPI
  structured JSON log, and Nginx structured access log using one request ID;
  normal readiness passed afterward.
- M07-T05 scheduled a protected logical PostgreSQL backup, verified its
  checksum, restored it into a clean disposable database, removed test
  artifacts, and recorded the recovery postmortem.
- The local HTTP route does not provide TLS; UFW restricts it to the trusted
  workstation.
- Loki/Alloy, external alert delivery, advanced dashboard expansion, and a
  dedicated metrics identity are useful candidates but do not block core M07.
- Development/nightly image stability and authenticated hardened-image pulls
  remain explicit operational risks.
