# Ansible automation

This directory contains the version-controlled Ansible source for managing the
Ops Status Board practice server.

## Boundaries

- **Control node:** Ubuntu under WSL2, where Ansible is installed.
- **Managed node:** the separate Ubuntu Server VirtualBox VM.
- **Transport:** SSH using a passphrase-protected administrator key.
- **Real inventory:** private and stored outside this repository.
- **Repository inventory:** `inventory/hosts.ini.example` contains placeholders
  only.

## WSL control-node setup

Create and activate the isolated Ansible environment:

```bash
python3 -m venv ~/.venvs/ops-status-board-ansible
source ~/.venvs/ops-status-board-ansible/bin/activate
python -m pip install "ansible-core==2.21.3"
```

At the start of an Ansible session, start an SSH agent and unlock the
administrator key for that session:

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519_ops_server_admin
```

The private key remains passphrase-protected on disk. The SSH agent holds an
unlocked temporary copy in memory only for the active session.

## Private inventory

Copy the example inventory to a private location outside the repository and
replace its placeholders. Do not commit a real inventory, VM IP address, or
private-key path.

The local lab inventory is expected at:

```text
~/.config/ops-status-board-ansible/hosts.ini
```

## Connectivity verification

Verify that Ansible can authenticate and run a module without changing the
server:

```bash
ansible \
  -i ~/.config/ops-status-board-ansible/hosts.ini \
  ops_servers \
  -m ansible.builtin.ping
```

Verify an explicitly privileged command when required:

```bash
ansible \
  -i ~/.config/ops-status-board-ansible/hosts.ini \
  ops_servers \
  --become \
  --ask-become-pass \
  -m ansible.builtin.command \
  -a 'id -un'
```

Use privilege escalation only for tasks that require it. Do not enable sudo
globally in the inventory.

## Baseline roles

`playbooks/baseline.yml` applies the server baseline in this order:

| Role | Responsibility |
|---|---|
| `base` | Refresh APT metadata and install `ca-certificates`, `curl`, and `gnupg`. |
| `security` | Maintain SSH hardening and the UFW policy. |
| `docker` | Maintain Docker's signed APT source, Docker Engine, Buildx, Compose, and the Docker service. |
| `application` | Preserve the root-only runtime boundary, verify existing secret files, render the pinned Compose definition, and deploy after a Compose change. |
| `observability` | Maintain private Prometheus/Grafana configuration, credentials, persistence, capacity limits, and Compose validation. |
| `nginx` | Manage the reverse-proxy site, enabled-site symlink, and safe Nginx validation/reload sequence. |

The repository-root `ansible.cfg` sets the local role search path and keeps SSH
host-key checking enabled.

Install the declared Ansible collection dependency before using the security
role:

```bash
ansible-galaxy collection install -r ansible/requirements.yml
```

The private inventory must define the trusted workstation source and allowed SSH
accounts. Keep their real values outside Git:

```ini
ops_allowed_workstation_source=REPLACE_WITH_TRUSTED_WORKSTATION_IP
ops_ssh_allowed_users=REPLACE_WITH_ALLOWED_SSH_USERS
```

The security role validates the complete SSH configuration before reloading SSH.
It allows SSH and HTTP only from the trusted workstation, denies incoming
traffic by default, allows outgoing traffic, and enables UFW at boot.

The Docker role does not add the deployment user to the `docker` group. Docker
daemon access is effectively root-level access, so operational Docker commands
continue to use `sudo`.

From the repository root, validate the baseline without contacting the server:

```bash
ansible-playbook \
  -i ~/.config/ops-status-board-ansible/hosts.ini \
  ansible/playbooks/baseline.yml \
  --syntax-check
```

Preview changes safely:

```bash
ansible-playbook \
  -i ~/.config/ops-status-board-ansible/hosts.ini \
  ansible/playbooks/baseline.yml \
  --check \
  --diff \
  --ask-become-pass
```

Apply the baseline only after reviewing the preview:

```bash
ansible-playbook \
  -i ~/.config/ops-status-board-ansible/hosts.ini \
  ansible/playbooks/baseline.yml \
  --ask-become-pass
```

A repeat run should report `changed=0`. This proves the baseline is
idempotent.

## Observability core

The observability role renders a bearer-authenticated Prometheus scrape job and
a provisioned Grafana data source. Prometheus remains on the private Compose
network. Grafana binds only to server loopback and is reached through Nginx at
`/grafana/`.

Prometheus and Grafana data use persistent, role-managed host directories.
Grafana's administrator password is generated once on the managed server and
stored in a root-only environment file. The metrics credential is derived from
the existing protected application credential without logging its value; real
credentials never enter Git.

See [`../docs/observability.md`](../docs/observability.md) for the capacity
budget, pinned-image decision, known limitations, and verification evidence.

## Operator dashboard

Grafana provisions the read-only **Ops Status Board** dashboard from the
repository. It uses the provisioned Prometheus data source rather than a
browser-to-application connection.

| Panel | PromQL query | Operator question answered |
| --- | --- | --- |
| Application availability | `min(up{job="ops-status-board"})` | Can Prometheus currently scrape the application? `1` means yes; `0` means no. |
| HTTP request rate | `sum(rate(ops_status_board_http_requests_total[5m]))` | How many requests per second has the application handled recently? |
| HTTP p95 request duration | `histogram_quantile(0.95, sum by (le) (rate(ops_status_board_http_request_duration_seconds_bucket[5m])))` | How slow are the slowest 5% of recent requests? |
| HTTP 5xx rate | `sum(rate(ops_status_board_http_requests_total{status_code=~"5.."}[5m]))` | Is the application returning server errors? |

The application excludes `/metrics` requests from its HTTP request metrics, so
Prometheus scrapes do not appear as false operator traffic. Grafana remains
loopback-only on the VM and is accessed through Nginx at `/grafana/`.

## Application deployment and drift correction
The application Compose definition is rendered from
`roles/application/templates/compose.yaml.j2`. Its image references are
immutable digests stored in non-secret role defaults. Real `app.env` and
`postgres.env` files remain root-owned on the managed server and are never
stored in this repository.
After the application and observability roles render their required files,
Ansible validates the complete Compose definition. A notified deployment pulls
the pinned images, runs migrations, and starts the application and monitoring
stack.
The named PostgreSQL volume is retained; do not use `docker compose down -v`
unless intentional database deletion is required.
The Nginx site is rendered from
`roles/nginx/templates/ops-status-board.conf.j2`. A configuration change
notifies handlers that run `nginx -t` before reloading Nginx. A failed
validation prevents the reload.
To prove idempotence, apply the baseline twice. The immediate repeat run should
report `changed=0`:
```bash
ansible-playbook \
  -i ~/.config/ops-status-board-ansible/hosts.ini \
  ansible/playbooks/baseline.yml \
  --ask-become-pass
```
For a controlled drift-correction exercise, change only a harmless comment in
the managed Nginx site file, then apply the baseline again. Ansible should
restore the template, validate Nginx, reload it, and leave the health endpoint
available.
