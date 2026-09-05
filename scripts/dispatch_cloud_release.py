"""Protected GitHub runner: submit one bounded SSM release and preserve failure."""

import argparse
import base64
import json
import os
import re
import shlex
import subprocess
import time
from pathlib import Path


def inputs(environment):
    image = environment.get("RELEASE_IMAGE", "")
    revision = environment.get("RELEASE_REVISION", "")
    operation = environment.get("RELEASE_OPERATION", "")
    if not re.fullmatch(r"ghcr\.io/ar7abb/ops-status-board@sha256:[0-9a-f]{64}", image):
        raise ValueError("An exact application SHA-256 digest is required")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("A full source commit is required")
    if operation not in {"deploy", "rollback", "approved-invalid-digest-drill"}:
        raise ValueError("Unknown release operation")
    return image, revision, operation


def aws(*arguments, allow_pending=False):
    result = subprocess.run(
        ["aws", *arguments, "--output", "json"],
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    if result.returncode:
        if allow_pending and "InvocationDoesNotExist" in result.stderr:
            return None
        raise RuntimeError(
            "AWS operation failed; inspect privately without credentials"
        )
    return json.loads(result.stdout)


def command(script, image, revision):
    """Use a fixed Python invocation; inputs never become executable shell syntax."""
    encoded = base64.b64encode(script.encode()).decode()
    python = (
        "import base64,sys; "
        f"sys.argv=['release','--image',{image!r},'--revision',{revision!r}]; "
        f"exec(compile(base64.b64decode('{encoded}'),'release','exec'))"
    )
    return "python3 -c " + shlex.quote(python)


def dispatch(environment):
    image, revision, operation = inputs(environment)
    instance = environment.get("INSTANCE_ID", "")
    if not re.fullmatch(r"i-[0-9a-f]{8,17}", instance):
        raise ValueError("Expected one configured EC2 instance")
    information = aws(
        "ssm",
        "describe-instance-information",
        "--filters",
        f"Key=InstanceIds,Values={instance}",
    )["InstanceInformationList"]
    if len(information) != 1 or information[0]["PingStatus"] != "Online":
        raise RuntimeError("Intended SSM target is not online")
    script = Path(__file__).with_name("deploy_cloud.py").read_text()
    parameters = {
        "commands": [command(script, image, revision)],
        "executionTimeout": ["600"],
    }
    submitted = aws(
        "ssm",
        "send-command",
        "--instance-ids",
        instance,
        "--document-name",
        "AWS-RunShellScript",
        "--timeout-seconds",
        "60",
        "--comment",
        f"Protected application {operation}",
        "--parameters",
        json.dumps(parameters),
    )
    identifier = submitted["Command"]["CommandId"]
    print("SSM release submitted; waiting for the actual command result.", flush=True)
    deadline = time.monotonic() + 780
    while time.monotonic() < deadline:
        result = aws(
            "ssm",
            "get-command-invocation",
            "--command-id",
            identifier,
            "--instance-id",
            instance,
            allow_pending=True,
        )
        if result is None or result["Status"] in {"Pending", "InProgress", "Delayed"}:
            time.sleep(10)
            continue
        if result["Status"] != "Success" or result["ResponseCode"] != 0:
            raise RuntimeError(
                "Remote release failed; a separate manual rollback is required"
            )
        # Never forward raw remote stdout/stderr into public CI logs.
        print("Remote digest/source verification and HTTP readiness passed.")
        return
    raise RuntimeError(
        "SSM result timed out. Execution may continue; inspect before any retry."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true")
    arguments = parser.parse_args()
    try:
        if arguments.validate_only:
            inputs(os.environ)
            print("Immutable release inputs validated.")
        else:
            dispatch(os.environ)
    except Exception:
        raise SystemExit(
            "Release failed or result unknown. Inspect privately; never assume success."
        ) from None
