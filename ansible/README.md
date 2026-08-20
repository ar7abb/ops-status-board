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