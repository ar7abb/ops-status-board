# CloudWatch observability

The AWS workload uses a small managed CloudWatch design instead of running a
second Prometheus and Grafana stack on the one-GiB EC2 instance. The purpose is
to answer four operational questions without collecting unnecessary data:

1. Is the instance itself healthy?
2. Is the root disk becoming full?
3. Is usable memory becoming dangerously low?
4. Is Nginx repeatedly returning server errors?

## Signal flow

The CloudWatch Agent runs on the existing EC2 instance. Every five minutes it
publishes root-disk used percentage and memory available percentage. It also
ships the structured Nginx access log and the Nginx error log to two separate
CloudWatch log groups. Both groups retain data for seven days.

The instance role can create streams and write events only in those two log
groups. It can publish metrics only in the `CWAgent` namespace. It cannot read
logs, change alarms, or administer CloudWatch.

## Alarm policy

| Alarm | Condition | Reason |
|---|---|---|
| Root disk high | More than 85% used for two five-minute periods | Leaves time to remove or archive data before writes fail |
| Memory low | Less than 10% available for two five-minute periods | Detects sustained memory pressure rather than one short spike |
| Instance status failed | EC2 reports failure for two checks | Detects host or instance impairment independently of the application |
| Repeated HTTP 5xx | At least three server errors in five minutes | Highlights a repeated service failure while ignoring one isolated error |

No notification destination is stored in Terraform. This avoids publishing a
personal address and separates alarm evaluation from notification routing.

## Cost boundary

The design creates three custom metrics, four standard alarms, and two small log
groups. It stays below the published CloudWatch monthly free allowances of ten
custom metrics, ten standard alarm metrics, and five GB of logs under ordinary
lab traffic. Seven-day retention limits stored log growth. Usage and billing can
arrive later, so the existing AWS budget and promotional-credit review remain
separate safeguards.

## Verification evidence

The reviewed Terraform plan proposed eight additions, zero changes, and zero
destructions. Applying that exact plan produced the same counts. The signed AWS
CloudWatch Agent package was fingerprint-checked, signature-verified, installed,
and configured through Ansible over Systems Manager without opening inbound
access.

Verification showed:

- the agent service was active and running;
- Nginx readiness still returned HTTP 200;
- each log group had a live stream and seven-day retention;
- the expected disk and memory metrics existed;
- all four alarms existed and initially reported `OK`;
- a synthetic HTTP 502 log line matched the server-error filter;
- one approved synthetic metric datapoint moved the server-error alarm from
  `OK` to `ALARM`, readiness remained HTTP 200, and the alarm returned to `OK`
  automatically after the datapoint expired;
- a repeated Ansible run reported zero changes and zero failures; and
- Terraform reported no differences between configuration and AWS.

## Recovery

If the monitoring design is too noisy or unexpectedly expensive, first stop the
agent to halt new custom telemetry. Review a Terraform plan that removes only
the CloudWatch log groups, metric filter, alarms, and instance policy, then apply
that reviewed plan. The application, database backup, Terraform backend, and
M09 recovery checkpoint are separate and must remain untouched.
