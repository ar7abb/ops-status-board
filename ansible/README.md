```markdown
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
```