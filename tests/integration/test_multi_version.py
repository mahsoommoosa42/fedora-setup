"""Multi-version integration tests across Fedora 39, 40, and 41."""
from __future__ import annotations

import pytest

from helpers import exec_in


@pytest.mark.integration
def test_setup_exits_zero_all_versions(fedora_native_multi):
    """Test that setup.sh exits cleanly on all supported Fedora versions."""
    code, out = exec_in(fedora_native_multi, "bash /setup/setup.sh 2>&1")
    assert code == 0, f"setup.sh exited {code} on Fedora {fedora_native_multi.name.split(':')[1]}:\n{out}"


@pytest.mark.integration
def test_base_tools_installed_all_versions(fedora_native_multi):
    """Test that base tools are available on all supported Fedora versions."""
    code, _ = exec_in(fedora_native_multi, "command -v git")
    assert code == 0, "git not found"

    code, _ = exec_in(fedora_native_multi, "command -v curl")
    assert code == 0, "curl not found"

    code, _ = exec_in(fedora_native_multi, "command -v wget")
    assert code == 0, "wget not found"


@pytest.mark.integration
def test_dry_run_mode_all_versions(fedora_native_multi):
    """Test that DRY_RUN mode works correctly on all supported Fedora versions."""
    code, out = exec_in(fedora_native_multi, "bash /setup/setup.sh 2>&1")
    assert "DRY_RUN mode" in out, "DRY_RUN mode message not found in output"
    assert code == 0, f"setup.sh failed in DRY_RUN mode on Fedora {fedora_native_multi.name.split(':')[1]}"


@pytest.mark.integration
def test_wsl_detection_all_versions(fedora_wsl_multi):
    """Test that WSL detection works correctly on all supported Fedora versions."""
    code, out = exec_in(fedora_wsl_multi, "bash /setup/setup.sh 2>&1")
    assert "WSL2 Fedora" in out, "WSL detection failed"
    assert code == 0, f"setup.sh failed on WSL Fedora {fedora_wsl_multi.name.split(':')[1]}"


@pytest.mark.integration
def test_module_sections_present_all_versions(fedora_native_multi):
    """Test that all module sections are present in output on all supported Fedora versions."""
    code, out = exec_in(fedora_native_multi, "bash /setup/setup.sh 2>&1")
    assert code == 0

    # Check for major sections
    sections = [
        "System Update",
        "Extra CLI",
        "C++",
        "Python",
        "JavaScript",
        "Rust",
        "NVIDIA",
        "Vulkan",
        "FFmpeg",
        "Git",
        "Shell",
    ]

    for section in sections:
        assert section in out, f"Section '{section}' not found in output"