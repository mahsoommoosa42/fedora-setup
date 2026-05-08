"""Slow post-install verification tests.

These tests run setup.sh WITHOUT DRY_RUN inside a dedicated container, then
verify that the installed tools are actually present. This takes 10-30 minutes
and requires a real network connection.

Run with:
    uv run pytest -m slow tests/integration/test_verify.py
"""
from __future__ import annotations

from pathlib import Path

import docker
import pytest

from helpers import exec_in
from conftest import PROJECT_ROOT, IMAGE_NAME, _get_or_build_image

EXPECTED_COMMANDS = [
    "git",
    "gh",
    "lazygit",
    "starship",
    "uv",
    "bun",
    "rustc",
    "nvim",
]

EXPECTED_BASHRC_MARKERS = [
    "zoxide",
    "fzf keybindings",
    "eza aliases",
    "bat alias",
    "HISTSIZE",
    "uv PATH",
    "bun PATH",
    "rustup PATH",
    "starship init",
]


@pytest.fixture(scope="module")
def real_install_container(docker_client):
    """Container that runs a full (non-dry-run) native install. Very slow."""
    _get_or_build_image(docker_client)
    container = docker_client.containers.run(
        IMAGE_NAME,
        command="sleep infinity",
        detach=True,
        tty=False,
        environment={"IS_WSL": "0", "HAS_NVIDIA": "0"},
        volumes={str(PROJECT_ROOT): {"bind": "/setup", "mode": "ro"}},
    )
    # Run setup non-interactively; ignore exit code (some tools may fail without network)
    exec_in(container, "bash /setup/setup.sh 2>&1 || true")
    yield container
    container.remove(force=True)


@pytest.mark.slow
@pytest.mark.parametrize("cmd", EXPECTED_COMMANDS)
def test_command_available(real_install_container, cmd):
    code, _ = exec_in(real_install_container, f"command -v {cmd}")
    assert code == 0, f"Command not found after install: {cmd}"


@pytest.mark.slow
def test_git_pager_is_delta(real_install_container):
    _, out = exec_in(real_install_container, "git config --global core.pager")
    assert out == "delta", f"Unexpected pager: {out!r}"


@pytest.mark.slow
@pytest.mark.parametrize("marker", EXPECTED_BASHRC_MARKERS)
def test_bashrc_contains_marker(real_install_container, marker):
    code, _ = exec_in(real_install_container, f'grep -qF "{marker}" ~/.bashrc')
    assert code == 0, f"Marker not found in ~/.bashrc: {marker!r}"
