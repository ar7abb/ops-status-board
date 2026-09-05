"""Instance-side, app-only release helper. Run as root through protected SSM.

No migrations, database restarts, automatic rollback, or credential output.
The caller supplies a reviewed digest and expected OCI source revision.
"""

import argparse
import fcntl
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.request import urlopen

RUNTIME = Path("/opt/ops-status-board")
IMAGE_PATTERN = r"ghcr\.io/ar7abb/ops-status-board@sha256:[0-9a-f]{64}"


def checked(command, timeout=300):
    """Capture output: Docker errors can contain private runtime details."""
    result = subprocess.run(
        command, capture_output=True, text=True, timeout=timeout, check=False
    )
    if result.returncode:
        raise RuntimeError(
            f"{command[0]} operation failed; private inspection required"
        )
    return result.stdout.strip()


def validate_image(image):
    if re.fullmatch(IMAGE_PATTERN, image) is None:
        raise ValueError(
            "Only an exact application repository SHA-256 digest is allowed"
        )
    return image


def replace_app_release(source, image, revision):
    """Change only the app image and public version in the Compose contract."""
    validate_image(image)
    if re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise ValueError("Expected a full reviewed source commit")
    pattern = rf"(?m)^(  app:\n    image: )({IMAGE_PATTERN})$"
    result, count = re.subn(pattern, lambda match: match[1] + image, source)
    if count != 1:
        raise ValueError("Expected exactly one immutable app image; refusing to edit")
    version_pattern = r'(?m)^(      APP_VERSION: ")[0-9a-f]+("$)'
    result, version_count = re.subn(
        version_pattern, lambda match: match[1] + revision + match[2], result
    )
    if version_count == 0:
        image_line = f"  app:\n    image: {image}\n"
        replacement = (
            image_line + f'    environment:\n      APP_VERSION: "{revision}"\n'
        )
        result, insertion_count = (
            result.replace(image_line, replacement),
            result.count(image_line),
        )
        if insertion_count != 1:
            raise ValueError("Could not safely add the app version override")
    elif version_count != 1:
        raise ValueError("Expected at most one app version override; refusing to edit")
    return result


def atomic_write(path, text, mode=0o600):
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".release-")
    try:
        with os.fdopen(descriptor, "w") as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def readiness():
    with urlopen("http://127.0.0.1/health/ready", timeout=5) as response:
        if response.status != 200 or json.load(response) != {"status": "ok"}:
            raise RuntimeError("Readiness gate failed")


def deploy(image, revision):
    validate_image(image)
    if re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise ValueError("Expected a full reviewed source commit")
    if os.geteuid() != 0:
        raise RuntimeError("This helper requires the protected root SSM context")
    compose_path = RUNTIME / "compose.yaml"
    compose = ["docker", "compose", "-f", str(compose_path)]
    with (RUNTIME / ".deployment.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        original = compose_path.read_text()
        candidate = replace_app_release(original, image, revision)
        # Pull and validate before editing configuration or touching the container.
        checked(["docker", "pull", image])
        actual_revision = checked(
            [
                "docker",
                "image",
                "inspect",
                "--format",
                '{{index .Config.Labels "org.opencontainers.image.revision"}}',
                image,
            ]
        )
        if actual_revision != revision:
            raise RuntimeError(
                "Published image source revision does not match approval"
            )
        current = checked(compose + ["ps", "--all", "--quiet", "app"])
        if not current or "\n" in current:
            raise RuntimeError("Expected one existing application container")
        previous = checked(
            ["docker", "inspect", "--format", "{{.Config.Image}}", current]
        )
        validate_image(previous)
        database = checked(compose + ["ps", "--quiet", "db"])
        if not database or "\n" in database:
            raise RuntimeError("Expected one existing database container")
        atomic_write(
            RUNTIME / "deployment-attempt.json",
            json.dumps(
                {
                    "previous_image": previous,
                    "requested_image": image,
                    "requested_revision": revision,
                }
            )
            + "\n",
        )
        atomic_write(compose_path, candidate, 0o644)
        checked(compose + ["config", "--quiet"])
        # Failure stays failed. A separate approved run selects the previous digest.
        checked(
            compose
            + ["up", "--detach", "--no-deps", "--wait", "--wait-timeout", "120", "app"],
            timeout=180,
        )
        running = checked(compose + ["ps", "--quiet", "app"])
        running_image = checked(
            ["docker", "inspect", "--format", "{{.Config.Image}}", running]
        )
        if running_image != image:
            raise RuntimeError("Running digest differs from approved digest")
        if checked(compose + ["ps", "--quiet", "db"]) != database:
            raise RuntimeError("Database identity changed unexpectedly")
        readiness()
        with urlopen("http://127.0.0.1/version", timeout=5) as response:
            if response.status != 200 or json.load(response) != {"version": revision}:
                raise RuntimeError("Version gate failed")
        atomic_write(
            RUNTIME / "last-healthy-release.json",
            json.dumps({"image": image, "revision": revision}) + "\n",
        )
        print("Approved digest and source revision verified; readiness HTTP 200.")
        print(
            "Database container unchanged; no migrations or volume removal performed."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--revision", required=True)
    arguments = parser.parse_args()
    try:
        deploy(arguments.image, arguments.revision)
    except Exception:
        # Do not leak command output, host identifiers, or runtime configuration.
        raise SystemExit(
            "Deployment failed. Inspect privately; rollback is manual."
        ) from None
