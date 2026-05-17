"""Unit tests for ``fedora_setup.runner`` (DRY_RUN wrappers)."""

from __future__ import annotations

import pytest

from fedora_setup import runner
from fedora_setup.context import Context


@pytest.fixture
def dry_ctx() -> Context:
    return Context(dry_run=True)


def test_command_exists_finds_bash() -> None:
    assert runner.command_exists("bash") is True


def test_command_exists_missing_command() -> None:
    assert runner.command_exists("__no_such_cmd_xyz__") is False


def test_dnf_install_dry_run(
    dry_ctx: Context, capsys: pytest.CaptureFixture[str]
) -> None:
    runner.dnf_install(dry_ctx, "curl", "wget", "git")
    out = capsys.readouterr().out
    assert "DRY_RUN: sudo dnf install -y" in out
    assert "curl" in out
    assert "wget" in out
    assert "git" in out


def test_dnf_install_no_packages_is_noop(
    dry_ctx: Context, capsys: pytest.CaptureFixture[str]
) -> None:
    runner.dnf_install(dry_ctx)
    assert capsys.readouterr().out == ""


def test_dnf_upgrade_dry_run(
    dry_ctx: Context, capsys: pytest.CaptureFixture[str]
) -> None:
    runner.dnf_upgrade(dry_ctx)
    assert "DRY_RUN: sudo dnf upgrade" in capsys.readouterr().out


def test_dnf_copr_enable_dry_run(
    dry_ctx: Context, capsys: pytest.CaptureFixture[str]
) -> None:
    runner.dnf_copr_enable(dry_ctx, "atim/lazygit")
    out = capsys.readouterr().out
    assert "DRY_RUN" in out
    assert "atim/lazygit" in out


def test_dnf_remove_dry_run(
    dry_ctx: Context, capsys: pytest.CaptureFixture[str]
) -> None:
    runner.dnf_remove(dry_ctx, "ffmpeg-free")
    out = capsys.readouterr().out
    assert "DRY_RUN: sudo dnf remove" in out
    assert "ffmpeg-free" in out


def test_dnf_group_update_dry_run(
    dry_ctx: Context, capsys: pytest.CaptureFixture[str]
) -> None:
    runner.dnf_group_update(dry_ctx, "core")
    out = capsys.readouterr().out
    assert "DRY_RUN" in out
    assert "core" in out


def test_dnf_config_manager_dry_run(
    dry_ctx: Context, capsys: pytest.CaptureFixture[str]
) -> None:
    runner.dnf_config_manager(dry_ctx, "--add-repo", "https://example.com/repo")
    out = capsys.readouterr().out
    assert "DRY_RUN" in out
    assert "example.com" in out


def test_systemctl_enable_dry_run(
    dry_ctx: Context, capsys: pytest.CaptureFixture[str]
) -> None:
    runner.systemctl_enable(dry_ctx, "libvirtd")
    out = capsys.readouterr().out
    assert "DRY_RUN: sudo systemctl enable" in out
    assert "libvirtd" in out


def test_cargo_install_dry_run(
    dry_ctx: Context, capsys: pytest.CaptureFixture[str]
) -> None:
    runner.cargo_install(dry_ctx, "cargo-watch")
    out = capsys.readouterr().out
    assert "DRY_RUN: cargo install --locked cargo-watch" in out


def test_run_installer_dry_run(
    dry_ctx: Context, capsys: pytest.CaptureFixture[str]
) -> None:
    runner.run_installer(dry_ctx, "https://example.com/install.sh", "-y")
    out = capsys.readouterr().out
    assert "DRY_RUN" in out
    assert "example.com" in out


def test_rpm_import_dry_run(
    dry_ctx: Context, capsys: pytest.CaptureFixture[str]
) -> None:
    runner.rpm_import(dry_ctx, "https://packages.microsoft.com/keys/microsoft.asc")
    out = capsys.readouterr().out
    assert "DRY_RUN: sudo rpm --import" in out
    assert "microsoft.asc" in out


def test_sudo_tee_repo_dry_run(
    dry_ctx: Context, capsys: pytest.CaptureFixture[str]
) -> None:
    runner.sudo_tee_repo(dry_ctx, "/etc/yum.repos.d/test.repo", "[test]\nname=Test")
    out = capsys.readouterr().out
    assert "DRY_RUN" in out
    assert "/etc/yum.repos.d/test.repo" in out


def test_usermod_groups_dry_run(
    dry_ctx: Context, capsys: pytest.CaptureFixture[str]
) -> None:
    runner.usermod_groups(dry_ctx, "kvm,libvirt", "testuser")
    out = capsys.readouterr().out
    assert "DRY_RUN: sudo usermod -aG" in out
    assert "kvm,libvirt" in out
    assert "testuser" in out
