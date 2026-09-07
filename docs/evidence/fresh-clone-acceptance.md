# Fresh-clone acceptance

Date: 2026-09-07

A new clone of the public `main` branch was tested in a disposable directory.
No files, virtual environments, Terraform downloads, containers, networks, or
volumes from the normal development checkout were reused.

## Result

| Check | Result |
|---|---|
| Clone opened on clean `main` | Pass |
| Hash-locked Python dependencies installed | Pass |
| Dependency consistency (`pip check`) | Pass |
| Python tests | 77 passed, 2 skipped, 18 subtests passed |
| Ruff lint | Pass |
| Ruff format check | Pass; 52 files formatted |
| Compose configuration | Pass |
| Container image build | Pass |
| PostgreSQL migration | Pass |
| Application and database health | Pass |
| Liveness, readiness, and version endpoints | HTTP 200 with expected version |
| Terraform bootstrap validation | Pass |
| Terraform workload validation | Pass |
| Disposable resources removed | Pass |

One deprecation warning came from the FastAPI/Starlette test-client dependency.
It did not fail acceptance, but it should be revisited during a future dependency
upgrade rather than hidden.

## Failure found while building the acceptance test

The first test script assumed placeholder names that did not match the published
safe templates. The migration therefore attempted to resolve the literal host
`HOST` and failed. The script was corrected to consume the exact placeholders in
`.env.example` and `postgres.env.example`, then the entire acceptance workflow
was restarted from another new clone. This validates the public template
contract and records the troubleshooting instead of concealing it.

## Boundary

This test proves local reproducibility and static Terraform validity. It does not
recreate AWS resources; the temporary cloud environment remains intentionally
destroyed.
