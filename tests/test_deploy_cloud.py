"""Local contract tests: no AWS calls, containers, or runtime writes."""

import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "deploy_cloud", Path(__file__).parents[1] / "scripts" / "deploy_cloud.py"
)
deploy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(deploy)
OLD = "ghcr.io/ar7abb/ops-status-board@sha256:" + "a" * 64
NEW = "ghcr.io/ar7abb/ops-status-board@sha256:" + "b" * 64


@pytest.mark.parametrize(
    "value",
    ["latest", OLD + ";id", OLD.upper(), "other.example/app@sha256:" + "a" * 64],
)
def test_rejects_unreviewable_images(value):
    with pytest.raises(ValueError):
        deploy.validate_image(value)


def test_changes_only_application_image():
    source = (
        "services:\n  db:\n    image: postgres:16\n"
        f"  app:\n    image: {OLD}\n  migrate:\n    image: {OLD}\n"
    )
    source = source.replace(
        f"  app:\n    image: {OLD}\n",
        (
            f"  app:\n    image: {OLD}\n    environment:\n"
            f'      APP_VERSION: "{"c" * 40}"\n'
        ),
    )
    result = deploy.replace_app_release(source, NEW, "d" * 40)
    assert result.count(NEW) == 1
    assert 'APP_VERSION: "' + "d" * 40 + '"' in result
    assert f"  migrate:\n    image: {OLD}" in result
    assert "image: postgres:16" in result


def test_first_release_adds_version_override():
    source = f"services:\n  app:\n    image: {OLD}\n"
    result = deploy.replace_app_release(source, NEW, "d" * 40)
    assert result == (
        f"services:\n  app:\n    image: {NEW}\n"
        f'    environment:\n      APP_VERSION: "{"d" * 40}"\n'
    )


@pytest.mark.parametrize(
    "source", ["", "  app:\n    image: latest\n", f"  app:\n    image: {OLD}\n" * 2]
)
def test_unknown_compose_layout_fails_closed(source):
    with pytest.raises(ValueError):
        deploy.replace_app_release(source, NEW, "d" * 40)


def test_atomic_write_permissions(tmp_path):
    target = tmp_path / "release.json"
    deploy.atomic_write(target, "{}\n")
    assert target.read_text() == "{}\n"
    assert target.stat().st_mode & 0o777 == 0o600
    assert list(tmp_path.iterdir()) == [target]
