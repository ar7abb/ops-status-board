# Protected cloud release

Status: verified in the M10 secure-delivery drill. The final running state is the
known pre-drill healthy release after an explicit manual rollback.

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

For this lab, the controlled failure used a nonexistent digest in the allowed
repository. It tested visible release failure without taking the healthy application
down. The later manual rollback proves deliberate selection and restoration of the
previous artifact, but it is not evidence of recovering from an application outage.

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

## Verified M10 drill

- Protected CI built source `4095b8478f061c197bbcfd8c830ace66d9bdae11`
  as digest `sha256:e6f800e940bb0708ddecae4b19d2a31e7824408a4ab783018f0d006178bf03e7`.
- The protected deployment run obtained temporary OIDC credentials and passed the
  digest, OCI source-revision, `/version`, and HTTP readiness gates.
- A separate nonexistent-digest run failed visibly in the deployment step. A direct
  check confirmed that the successful candidate remained ready and running.
- A separate manual rollback restored digest
  `sha256:086ef2a3450f944847371ce2c99b9fb0140ee094662e856e1871e7e11e118525`
  and revision `c182896ae300ca873f42d53b3cb6b43201ac5263`.
- Post-rollback checks confirmed HTTP readiness, exact `/version`, database presence,
  four healthy CloudWatch alarms, SSM Online status, and Terraform convergence.
- The helper itself compared database container identity before and after each
  successful application replacement. No migration, database restart, infrastructure
  replacement, or volume removal occurred.

GitHub reported that the pinned AWS credentials action currently targets Node.js 20
and was forced onto Node.js 24 by the runner. The action succeeded; the warning is
retained as dependency-maintenance evidence rather than treated as a deployment error.

## References

- [Docker Compose up](https://docs.docker.com/reference/cli/docker/compose/up/)
- [SSM command result and eventual consistency](https://docs.aws.amazon.com/systems-manager/latest/APIReference/API_GetCommandInvocation.html)
