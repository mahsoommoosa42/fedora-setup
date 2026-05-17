"""Unit tests for ``fedora_setup.detect``."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from fedora_setup import detect


@pytest.fixture(autouse=True)
def _clear_detect_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Always start tests with no detection env-var overrides set."""
    for var in (
        "IS_WSL",
        "WSL_DISTRO_NAME",
        "HAS_NVIDIA",
        "SYSTEMD_DIR_OVERRIDE",
        "PROC_VERSION_OVERRIDE",
        "LSPCI_STUB_OUTPUT",
    ):
        monkeypatch.delenv(var, raising=False)


# ── is_wsl ────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("value", ["1", "true", "yes", "on", "TRUE", "True"])
def test_is_wsl_truthy_override(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("IS_WSL", value)
    assert detect.is_wsl() is True


@pytest.mark.parametrize("value", ["0", "false", "no", "off"])
def test_is_wsl_falsy_override(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("IS_WSL", value)
    assert detect.is_wsl() is False


def test_is_wsl_via_distro_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WSL_DISTRO_NAME", "fedora")
    assert detect.is_wsl() is True


def test_is_wsl_via_proc_version_microsoft(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proc_version = tmp_path / "version"
    proc_version.write_text("Linux version 5.15.167.4-microsoft-standard-WSL2\n")
    monkeypatch.setenv("PROC_VERSION_OVERRIDE", str(proc_version))
    assert detect.is_wsl() is True


def test_is_wsl_falls_back_to_native(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proc_version = tmp_path / "version"
    proc_version.write_text("Linux version 6.8.0-59-generic (gcc version 13)\n")
    monkeypatch.setenv("PROC_VERSION_OVERRIDE", str(proc_version))
    assert detect.is_wsl() is False


# ── has_nvidia ────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("value", ["1", "true", "yes"])
def test_has_nvidia_truthy_override(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("HAS_NVIDIA", value)
    assert detect.has_nvidia() is True


@pytest.mark.parametrize("value", ["0", "false"])
def test_has_nvidia_falsy_override(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("HAS_NVIDIA", value)
    assert detect.has_nvidia() is False


# ── has_systemd ───────────────────────────────────────────────────────────────


def test_has_systemd_existing_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SYSTEMD_DIR_OVERRIDE", str(tmp_path))
    assert detect.has_systemd() is True


def test_has_systemd_missing_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SYSTEMD_DIR_OVERRIDE", "/nonexistent/path/xyz")
    assert detect.has_systemd() is False


# ── is_interactive ────────────────────────────────────────────────────────────


def test_is_interactive_returns_bool() -> None:
    # Just verify it doesn't crash and returns a bool.
    assert isinstance(detect.is_interactive(), bool)


# ── get_fedora_versions ───────────────────────────────────────────────────────


def test_get_fedora_versions_returns_three_descending_ints() -> None:
    versions = detect.get_fedora_versions()
    assert isinstance(versions, list)
    assert len(versions) >= 1
    assert all(isinstance(v, int) for v in versions)
    assert versions == sorted(versions, reverse=True)
