"""Failure-path tests use fake Docker/AWS; never contact a live instance."""

import importlib.util
import json
from pathlib import Path

import pytest


def module(name):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).parents[1] / "scripts" / f"{name}.py"
    )
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


IMAGE = "ghcr.io/ar7abb/ops-status-board@sha256:" + "b" * 64
OLD = "ghcr.io/ar7abb/ops-status-board@sha256:" + "a" * 64
REVISION = "c" * 40


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    helper = module("deploy_cloud")
    monkeypatch.setattr(helper, "RUNTIME", tmp_path)
    monkeypatch.setattr(helper.os, "geteuid", lambda: 0)
    source = (
        f"services:\n  app:\n    image: {OLD}\n"
        f'    environment:\n      APP_VERSION: "{"a" * 40}"\n'
    )
    (tmp_path / "compose.yaml").write_text(source)
    calls = []

    def checked(command, **kwargs):
        calls.append(command)
        if command[1:3] == ["image", "inspect"]:
            return REVISION
        if command[-4:] == ["ps", "--all", "--quiet", "app"]:
            return "app-container"
        if command[-3:] == ["ps", "--quiet", "db"]:
            return "db-container"
        if command[1] == "inspect":
            return IMAGE if any("up" in call for call in calls) else OLD
        return ""

    monkeypatch.setattr(helper, "checked", checked)
    monkeypatch.setattr(helper, "readiness", lambda: None)
    monkeypatch.setattr(
        helper,
        "urlopen",
        lambda *args, **kwargs: type(
            "Response",
            (),
            {
                "status": 200,
                "__enter__": lambda self: self,
                "__exit__": lambda *args: None,
                "read": lambda self: json.dumps({"version": REVISION}).encode(),
            },
        )(),
    )
    return helper, calls, source


def test_success_never_restarts_database_or_runs_migrations(runtime, tmp_path):
    helper, calls, _ = runtime
    helper.deploy(IMAGE, REVISION)
    start = next(call for call in calls if "up" in call)
    assert start[-1] == "app" and "--no-deps" in start and "--wait" in start
    assert not any("down" in call or "migrate" in call for call in calls)
    assert (tmp_path / "last-healthy-release.json").exists()


def test_failed_pull_preserves_compose(runtime, tmp_path, monkeypatch):
    helper, _, original = runtime

    def fail(*args, **kwargs):
        raise RuntimeError("pull failed")

    monkeypatch.setattr(helper, "checked", fail)
    with pytest.raises(RuntimeError):
        helper.deploy(IMAGE, REVISION)
    assert (tmp_path / "compose.yaml").read_text() == original
    assert not (tmp_path / "last-healthy-release.json").exists()


def test_health_failure_stays_failed_without_automatic_rollback(
    runtime, tmp_path, monkeypatch
):
    helper, calls, _ = runtime
    checkpoint = tmp_path / "last-healthy-release.json"
    checkpoint.write_text("previous healthy checkpoint")

    def fail():
        raise RuntimeError("not ready")

    monkeypatch.setattr(helper, "readiness", fail)
    with pytest.raises(RuntimeError):
        helper.deploy(IMAGE, REVISION)
    assert checkpoint.read_text() == "previous healthy checkpoint"
    assert len([call for call in calls if "up" in call]) == 1


def test_source_mismatch_cannot_start_container(runtime, tmp_path):
    helper, calls, original = runtime
    with pytest.raises(RuntimeError, match="source revision"):
        helper.deploy(IMAGE, "d" * 40)
    assert (tmp_path / "compose.yaml").read_text() == original
    assert not any("up" in call for call in calls)


def test_dispatch_rejects_shell_injection():
    dispatcher = module("dispatch_cloud_release")
    with pytest.raises(ValueError):
        dispatcher.inputs(
            {
                "RELEASE_IMAGE": IMAGE + "$(id)",
                "RELEASE_REVISION": REVISION,
                "RELEASE_OPERATION": "deploy",
            }
        )


def test_remote_failure_never_becomes_success(monkeypatch):
    dispatcher = module("dispatch_cloud_release")
    results = iter(
        [
            {"InstanceInformationList": [{"PingStatus": "Online"}]},
            {"Command": {"CommandId": "fake-command"}},
            {"Status": "Failed", "ResponseCode": 1},
        ]
    )
    monkeypatch.setattr(dispatcher, "aws", lambda *a, **k: next(results))
    with pytest.raises(RuntimeError, match="separate manual rollback"):
        dispatcher.dispatch(
            {
                "RELEASE_IMAGE": IMAGE,
                "RELEASE_REVISION": REVISION,
                "RELEASE_OPERATION": "deploy",
                "INSTANCE_ID": "i-" + "a" * 17,
            }
        )
