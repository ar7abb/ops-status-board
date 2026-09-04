# GitHub OIDC delivery identity

## Purpose

GitHub Actions needs an AWS identity before it can operate the cloud deployment
path. The project uses OpenID Connect (OIDC) instead of storing a permanent AWS
access key in GitHub.

The exchange is:

```text
approved GitHub job
  -> short-lived GitHub identity token
  -> AWS verifies audience and subject
  -> AWS issues temporary role credentials
  -> workflow may use only the role's SSM permissions
```

The temporary credentials expire. Knowing the role ARN does not grant access;
AWS still requires a valid signed token whose claims match the trust policy.

## Trust boundary

The role trust uses exact equality checks:

- audience: `sts.amazonaws.com`;
- subject: the approved repository and `production` environment, including
  GitHub's stable owner and repository identifiers.

There is no repository, organization, branch, or environment wildcard. GitHub's
`production` environment accepts only protected branches and requires a human
reviewer. Administrators cannot bypass its configured protection rules. This
combines two controls: GitHub decides whether the protected job may start, and
AWS independently decides whether its token may assume the role.

The exact subject is a required sensitive Terraform input stored only in an
ignored private variable file. Public configuration documents its shape and
purpose without publishing the stable identifiers.

## Permission boundary

Trust answers **who may borrow the role**. The attached permission policy answers
**what the borrowed role may do**.

The role can:

- send the AWS-managed `AWS-RunShellScript` SSM document only to the
  Terraform-managed application instance;
- inspect Systems Manager registration and command results.

It cannot create infrastructure, administer IAM, read runtime parameters,
access database backups, use backup encryption keys, or open inbound network
access.

Some SSM inspection actions require `Resource = "*"` because those read APIs do
not support resource-level restrictions. That wildcard applies only to the
three named read actions; it does not widen `ssm:SendCommand`.

## Workflow controls

The workflow is manually dispatched and references the protected `production`
environment. Its default repository permission is read-only. Only its identity
job receives `id-token: write`, which permits requesting a GitHub OIDC token but
does not itself grant AWS permissions.

The deployment role ARN and instance ID are stored as non-secret GitHub
environment variables. The workflow does not print their values or the AWS
caller identity.

Before using valid credentials, the workflow requests a token with a deliberately
incorrect audience and verifies that AWS rejects it. It then requests the proper
AWS audience, obtains temporary credentials, and confirms that the intended SSM
target is online. It does not print token claims or cloud identifiers. This task
performs no application deployment; immutable digest deployment and rollback
remain separate work.

## Recovery

If the trust or permission boundary is incorrect:

1. disable the GitHub workflow;
2. remove the environment variables;
3. review a Terraform plan that removes only the deployment role, its inline
   policy, and the GitHub OIDC provider;
4. apply only after confirming that the workload, backend, and observability
   resources are unaffected.

No long-lived AWS credential needs rotation because none is stored in GitHub.
