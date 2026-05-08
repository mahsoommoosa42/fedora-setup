"""Integration tests for native (non-WSL) Fedora setup in DRY_RUN mode."""
from __future__ import annotations

import pytest

from helpers import exec_in

EXPECTED_SECTIONS = [
    "1 · System Update",
    "2 · Extra CLI",
    "3 · C++",
    "4 · Kernel",
    "5 · Python",
    "6 · JavaScript",
    "7 · Claude",
    "8 · Nerd Fonts",
    "9 · Rust",
    "10 · NVIDIA",
    "11 · Editors",
    "12 · Git",
    "13 · Shell",
]


@pytest.fixture(scope="module")
def native_output(fedora_native):
    """Run setup.sh once and cache the output for this module's tests."""
    code, out = exec_in(fedora_native, "bash /setup/setup.sh 2>&1")
    return code, out


def test_setup_exits_zero(native_output):
    code, out = native_output
    assert code == 0, f"setup.sh exited {code}:\n{out}"


@pytest.mark.parametrize("section", EXPECTED_SECTIONS)
def test_section_present(native_output, section):
    _, out = native_output
    assert section in out, f"Missing section header: {section!r}"


def test_no_wsl_skip_messages(native_output):
    _, out = native_output
    assert "WSL: skipping" not in out


def test_kernel_packages_present(native_output):
    _, out = native_output
    assert "kernel-devel" in out


def test_kde_not_skipped(native_output):
    _, out = native_output
    assert "WSL: skipping KDE" not in out


def test_vs_code_not_skipped(native_output):
    _, out = native_output
    assert "WSL: skipping VS Code" not in out


def test_dry_run_dnf_prefix(native_output):
    _, out = native_output
    assert "DRY_RUN: sudo dnf" in out


def test_no_akmod_skip_message(native_output):
    _, out = native_output
    assert "WSL: skipping akmod" not in out
