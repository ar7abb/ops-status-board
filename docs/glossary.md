# Ops Status Board Glossary

This glossary defines terms as they are used in this project.

## Repository

A project directory managed by Git, including its files and recorded history. The local repository is in WSL2; GitHub stores its remote copy.

## Branch

A named line of work that points to a commit. A local branch does not automatically exist on GitHub; it must be pushed to create or update its remote branch.

## Upstream branch

The remote branch tracked by a local branch. Git uses this relationship to report whether the local branch is ahead or behind and to choose a default destination for commands such as `git push`.

## Commit

A recorded snapshot of staged changes in local Git history. Creating a commit does not publish it to GitHub; publication requires a push.

## Docker image

An immutable, reusable package containing an application's filesystem, runtime, dependencies, and startup instructions.

## Container

A running or stopped instance created from an image. It remains a Linux process while Docker isolates its filesystem, networking, and other resources.

## Reverse proxy

Software that receives client requests and forwards them to another service. In the planned server architecture, Nginx will act as the reverse proxy in front of FastAPI.

## WIP limit

A work-in-progress limit that restricts how many tasks should occupy a workflow stage at once. This project allows at most one task in **In Progress**; the GitHub Project limit is a warning, so the learner and reviewer must enforce the rule.
