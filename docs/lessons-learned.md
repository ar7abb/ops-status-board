# Lessons Learned

This document contains selected technical lessons from building Ops Status Board. It intentionally excludes private coaching records, confidence scores, credentials, account details, and machine-specific identifiers.

## Workstation and server roles

Windows is the host platform. Ubuntu under WSL2 is the Linux development workstation where project files and Linux tooling live. A separate Ubuntu VM is the practice server, so deployment and operations can be tested across a real machine boundary before moving to AWS.

## Package management and trust

`apt update` refreshes the package information available from configured repositories; `apt upgrade` installs newer versions of already installed packages. Repository signatures verify origin and integrity, but they are not antivirus checks and do not guarantee bug-free software. A failed or expired verification must be investigated rather than bypassed.

## Docker concepts and privilege

A Docker image is an immutable, reusable package template. A container is an isolated Linux process created from an image. Docker Compose reads a YAML description of services, networks, volumes, and relationships, then asks the Docker daemon to create the desired application stack.

Membership in the Docker group is effectively root-level authority because it allows a user to command the daemon. It is a security decision, not merely a convenience for avoiding repeated `sudo` commands. Published container ports also need explicit network and firewall review because Docker can alter packet-filtering behavior.

## Git identity and GitHub authentication

Git author identity records who created a commit. SSH authentication separately proves permission to access GitHub. The public SSH key may be registered with GitHub; the private key and its passphrase must never be shared. A local commit reaches GitHub only after a configured remote and an explicit push.

## Safe repository migration

Copy-first migration preserves a recovery source until destination hashes match. Ignore rules reduce accidental staging, but they do not replace reviewing `git status` and the staged diff. Public repositories should contain product code and curated technical evidence, while raw coaching history, detailed environment state, credentials, database dumps, and sensitive evidence remain private and outside every Git worktree.
