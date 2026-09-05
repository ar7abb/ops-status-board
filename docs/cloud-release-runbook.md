# Protected cloud release — implementation checkpoint

Status: local implementation under test. M10-T03 and M10-T04 are not complete.
No successful deployment, failure drill, rollback, or v0.5 release is claimed here.

## What the release path does

The manually dispatched `Protected cloud release` workflow requires the protected
`production` environment. It accepts only a complete application image digest and
full source commit. A commit-pinned action obtains temporary AWS credentials.
The runner sends the checked-in Python release helper through Systems Manager.

GitHub serializes release runs without cancelling an active deployment. A second,
instance-side file lock prevents simultaneous helper executions. These locks do
not coordinate independent Ansible or manual Docker commands: do not run those
while a release is active.

The helper pulls the image and checks its OCI source-revision label before changing
the application image in the rendered Compose file. It starts only `app`, with
`--no-deps --wait`, then verifies the digest, HTTP readiness, and unchanged database
container identity. It never runs migrations, removes volumes, or restarts PostgreSQL.
Releases requiring schema changes need a separately reviewed compatibility procedure.

The current `/version` route reports configured `APP_VERSION`, not an immutable image
identity. It must be reconciled during live verification; the running digest and OCI
revision are the artifact-identity evidence. Do not claim the current endpoint proves
the source commit by itself.

## Failure and manual rollback

A failed pull leaves the running application and Compose file unchanged. A failure
after replacement leaves the workflow failed and requires inspection and a separate
approved rollback run. Selecting `rollback` is an operator label, not automatic image
selection: supply the previously verified healthy digest and its source revision.

The helper records a private deployment-attempt file and updates the private
last-healthy-release file only after all gates pass. Record the known healthy digest
and source revision independently before the drill. A timeout means the outcome is
unknown, not that execution stopped; inspect SSM and the host before retrying.

For this lab, the proposed controlled failure is a nonexistent digest in the allowed
repository. This tests visible release failure without taking the healthy application
down. A successful manual redeployment afterward is not evidence of recovering from
an application outage; describe that distinction explicitly.

## Configuration ownership and security

Ansible owns the base Compose template. A successful promotion changes the rendered
application image on the instance. Reconcile `ops_application_image` in the reviewed
Ansible configuration before the next playbook run, or Ansible may restore its older
configured digest. Do not run the application handler during the release drill.

The AWS role has no direct broad storage permissions, but permission to execute
`AWS-RunShellScript` on this instance grants root-level host execution. It can therefore
reach host secrets and the instance role indirectly. The protected environment and
reviewed workflow are important trust boundaries, not a substitute for this disclosure.
Do not give arbitrary contributors production approval or workflow modification rights.

Raw AWS responses and remote command output are not printed in public workflow logs.
Inspect failures privately; never publish environment files, credentials, instance IDs,
account IDs, command payloads containing private values, or database backups.

## Remaining live acceptance checks

1. Refresh the local AWS login; verify intended identity and region privately.
2. Verify current image/source revision, `/version`, readiness, database persistence,
   CloudWatch alarm states, and a no-change Terraform plan.
3. Review and publish the workflow only after required CI passes.
4. Approve one healthy digest deployment and operate the production gate.
5. Separately approve the nonexistent-digest drill and retain its failed run.
6. Manually approve rollback/redeployment of the known healthy digest; verify health,
   database continuity, image/version evidence, monitoring, and Terraform convergence.
7. Reconcile Ansible desired image and sanitized evidence, then close M10-T03.
8. Demonstrate the complete source-to-cloud trace and learner workflow modification;
   publish v0.5 and close M10-T04 only after those checks are verified.

## References

- [Docker Compose up](https://docs.docker.com/reference/cli/docker/compose/up/)
- [SSM command result and eventual consistency](https://docs.aws.amazon.com/systems-manager/latest/APIReference/API_GetCommandInvocation.html)
