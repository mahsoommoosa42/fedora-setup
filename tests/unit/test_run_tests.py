"""Unit tests for tests/run_tests.py.

Covers CLI argument routing and the _interactive_env() behaviour without
requiring Docker or an SSH client to be present.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

# ── load run_tests as a module ────────────────────────────────────────────────

_RUN_TESTS_PATH = Path(__file__).parent.parent / "run_tests.py"


@pytest.fixture(scope="module")
def run_tests() -> ModuleType:
    spec = importlib.util.spec_from_file_location("run_tests", _RUN_TESTS_PATH)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# ── helpers ───────────────────────────────────────────────────────────────────

def _fake_exec_run(cmd, **kwargs):
    """Return a mock exec result whose .output is an empty byte stream."""
    result = MagicMock()
    result.exit_code = 0
    result.output = iter([])
    return result


def _make_mock_docker(image_found: bool = True):
    """Build a minimal mock docker module + client."""
    container = MagicMock()
    container.exec_run.side_effect = _fake_exec_run

    client = MagicMock()
    if image_found:
        client.images.get.return_value = MagicMock()
    else:
        client.images.get.side_effect = Exception("ImageNotFound")
        client.images.build.return_value = (MagicMock(), [])
    client.containers.run.return_value = container

    # Low-level API used for streaming setup.sh output + exit code.
    client.api.exec_create.return_value = {"Id": "fake-exec-id"}
    client.api.exec_start.return_value = iter([])  # empty byte stream
    client.api.exec_inspect.return_value = {"ExitCode": 0}

    docker_mod = MagicMock()
    docker_mod.from_env.return_value = client
    # Make ImageNotFound a real exception subclass so except clauses work.
    docker_mod.errors.ImageNotFound = type("ImageNotFound", (Exception,), {})

    return docker_mod, client, container


# ── CLI routing ───────────────────────────────────────────────────────────────


def test_interactive_flag_routes_to_interactive_env(
    run_tests: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    called: list[bool] = []
    monkeypatch.setattr(run_tests, "_interactive_env", lambda dry_run=False: called.append(dry_run) or 0)
    monkeypatch.setattr(sys, "argv", ["run_tests.py", "-i"])
    run_tests.main()
    assert called == [False]


def test_interactive_dry_run_flag_passes_through(
    run_tests: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    called: list[bool] = []
    monkeypatch.setattr(run_tests, "_interactive_env", lambda dry_run=False: called.append(dry_run) or 0)
    monkeypatch.setattr(sys, "argv", ["run_tests.py", "-i", "--dry-run"])
    run_tests.main()
    assert called == [True]


# ── _interactive_env: container startup ───────────────────────────────────────


def test_container_not_started_as_root(
    run_tests: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """setup.sh rejects root — the container must not be started with user='root'."""
    docker_mod, client, _container = _make_mock_docker()
    monkeypatch.setitem(sys.modules, "docker", docker_mod)
    monkeypatch.setitem(sys.modules, "docker.errors", docker_mod.errors)
    with patch("builtins.input", return_value=None):
        run_tests._interactive_env(dry_run=True)
    _, kwargs = client.containers.run.call_args
    assert kwargs.get("user") not in ("root", "0")


def test_port_bound_to_localhost(
    run_tests: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """sshd port must be bound to 127.0.0.1, not exposed externally."""
    docker_mod, client, _container = _make_mock_docker()
    monkeypatch.setitem(sys.modules, "docker", docker_mod)
    monkeypatch.setitem(sys.modules, "docker.errors", docker_mod.errors)
    with patch("builtins.input", return_value=None):
        run_tests._interactive_env(dry_run=True)
    _, kwargs = client.containers.run.call_args
    host, _port = kwargs["ports"]["22/tcp"]
    assert host == "127.0.0.1"


def test_dry_run_sets_env_var(
    run_tests: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    docker_mod, client, _container = _make_mock_docker()
    monkeypatch.setitem(sys.modules, "docker", docker_mod)
    monkeypatch.setitem(sys.modules, "docker.errors", docker_mod.errors)
    with patch("builtins.input", return_value=None):
        run_tests._interactive_env(dry_run=True)
    _, kwargs = client.containers.run.call_args
    assert kwargs["environment"].get("DRY_RUN") == "1"


def test_real_run_omits_dry_run_env_var(
    run_tests: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    docker_mod, client, _container = _make_mock_docker()
    monkeypatch.setitem(sys.modules, "docker", docker_mod)
    monkeypatch.setitem(sys.modules, "docker.errors", docker_mod.errors)
    with patch("builtins.input", return_value=None):
        run_tests._interactive_env(dry_run=False)
    _, kwargs = client.containers.run.call_args
    assert "DRY_RUN" not in kwargs["environment"]


# ── _interactive_env: execution order ────────────────────────────────────────


def test_setup_runs_before_sshd(
    run_tests: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """setup.sh must be submitted via exec_create before any exec_run SSH commands."""
    docker_mod, client, container = _make_mock_docker()
    monkeypatch.setitem(sys.modules, "docker", docker_mod)
    monkeypatch.setitem(sys.modules, "docker.errors", docker_mod.errors)
    with patch("builtins.input", return_value=None):
        run_tests._interactive_env(dry_run=True)

    # setup.sh is submitted via client.api.exec_create (low-level streaming API).
    setup_cmd = client.api.exec_create.call_args[0][1]
    assert "/setup/setup.sh" in setup_cmd

    # SSH setup commands (including sshd) come via container.exec_run afterwards.
    ssh_cmds = [str(c[0][0]) for c in container.exec_run.call_args_list]
    assert any("sshd" in c and "openssh" not in c for c in ssh_cmds)


def test_ssh_setup_cmds_use_bash(
    run_tests: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Shell features (pipes, redirects) in SSH setup require an explicit bash wrapper."""
    docker_mod, _client, container = _make_mock_docker()
    monkeypatch.setitem(sys.modules, "docker", docker_mod)
    monkeypatch.setitem(sys.modules, "docker.errors", docker_mod.errors)
    with patch("builtins.input", return_value=None):
        run_tests._interactive_env(dry_run=True)

    for call in container.exec_run.call_args_list:
        cmd = call[0][0]
        # setup.sh is passed as a plain list; SSH setup cmds must use bash.
        if isinstance(cmd, list) and "/setup/setup.sh" not in cmd:
            assert cmd[:2] == ["/bin/bash", "-c"], f"Missing bash wrapper: {cmd}"


# ── _interactive_env: cleanup ─────────────────────────────────────────────────


def test_container_killed_if_setup_fails(
    run_tests: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If setup.sh exits non-zero the container must be stopped before returning."""
    docker_mod, client, container = _make_mock_docker()
    client.api.exec_inspect.return_value = {"ExitCode": 1}
    monkeypatch.setitem(sys.modules, "docker", docker_mod)
    monkeypatch.setitem(sys.modules, "docker.errors", docker_mod.errors)
    monkeypatch.setattr("builtins.input", lambda: None)
    result = run_tests._interactive_env(dry_run=True)
    assert result == 1
    container.stop.assert_called_once()
    container.remove.assert_called_once()


def test_container_removed_after_user_exits(
    run_tests: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    docker_mod, _client, container = _make_mock_docker()
    monkeypatch.setitem(sys.modules, "docker", docker_mod)
    monkeypatch.setitem(sys.modules, "docker.errors", docker_mod.errors)
    monkeypatch.setattr("builtins.input", lambda: None)
    run_tests._interactive_env(dry_run=True)
    container.stop.assert_called_once()
    container.remove.assert_called_once()


def test_container_removed_on_keyboard_interrupt(
    run_tests: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    docker_mod, _client, container = _make_mock_docker()
    monkeypatch.setitem(sys.modules, "docker", docker_mod)
    monkeypatch.setitem(sys.modules, "docker.errors", docker_mod.errors)
    monkeypatch.setattr("builtins.input", lambda: (_ for _ in ()).throw(KeyboardInterrupt()))
    run_tests._interactive_env(dry_run=True)
    container.stop.assert_called_once()
    container.remove.assert_called_once()
