"""Integration tests for WSL2 Fedora setup in DRY_RUN mode."""
from __future__ import annotations

import re

import pytest

from helpers import exec_in


@pytest.fixture(scope="module")
def wsl_output(fedora_wsl):
    code, out = exec_in(fedora_wsl, "bash /setup/setup.sh 2>&1")
    return code, out


@pytest.fixture(scope="module")
def wsl_nvidia_output(fedora_wsl_nvidia):
    code, out = exec_in(fedora_wsl_nvidia, "bash /setup/setup.sh 2>&1")
    return code, out


# ── No-NVIDIA WSL ─────────────────────────────────────────────────────────────

def test_setup_exits_zero_wsl(wsl_output):
    code, out = wsl_output
    assert code == 0, f"setup.sh exited {code}:\n{out}"


def test_kernel_section_skipped(wsl_output):
    _, out = wsl_output
    assert "WSL: skipping kernel module" in out
    # Check that kernel-devel is not being installed via dnf (not on same line)
    assert not re.search(r"dnf install.*kernel-devel", out, re.MULTILINE)


def test_no_kwriteconfig6_in_wsl(wsl_output):
    _, out = wsl_output
    assert "kwriteconfig6" not in out


def test_kde_skipped_in_wsl(wsl_output):
    _, out = wsl_output
    assert "WSL: skipping KDE" in out


def test_no_akmod_in_wsl_no_gpu(wsl_output):
    _, out = wsl_output
    assert "akmod-nvidia" not in out


def test_vs_code_skipped_wsl(wsl_output):
    _, out = wsl_output
    assert "WSL: skipping VS Code" in out


def test_no_libvirtd_in_wsl(wsl_output):
    _, out = wsl_output
    # systemctl should not appear since the kernel module is entirely skipped
    assert "systemctl enable --now libvirtd" not in out


# ── WSL + NVIDIA ──────────────────────────────────────────────────────────────

def test_setup_exits_zero_wsl_nvidia(wsl_nvidia_output):
    code, out = wsl_nvidia_output
    assert code == 0, f"setup.sh exited {code}:\n{out}"


def test_akmod_skipped_wsl_nvidia(wsl_nvidia_output):
    _, out = wsl_nvidia_output
    assert "WSL: skipping akmod" in out
    # Check that akmod-nvidia is not being installed via dnf (not on same line)
    assert not re.search(r"dnf install.*akmod-nvidia", out, re.MULTILINE)


def test_wsl_lib_path_added(wsl_nvidia_output):
    _, out = wsl_nvidia_output
    assert "wsl/lib" in out


def test_cuda_toolkit_installed_wsl_nvidia(wsl_nvidia_output):
    _, out = wsl_nvidia_output
    # CUDA is now installed directly from NVIDIA, not from Fedora repo
    assert "CUDA" in out or "cuda" in out.lower()
