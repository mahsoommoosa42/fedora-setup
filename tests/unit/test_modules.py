"""Module-level dry-run tests for the Python ports of ``modules/*.sh``."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from fedora_setup.context import Context
from fedora_setup.modules import MODULE_ORDER


@pytest.fixture
def ctx(tmp_path: Path) -> Context:
    return Context(dry_run=True, home=tmp_path)


def _run(name: str, ctx: Context) -> None:
    module = next(mod for display, mod in MODULE_ORDER if display == name)
    module.run(ctx)


# ── 01 base ───────────────────────────────────────────────────────────────────


def test_base_emits_dry_run_dnf(
    ctx: Context, capsys: pytest.CaptureFixture[str]
) -> None:
    _run("01-base", ctx)
    out = capsys.readouterr().out
    assert "DRY_RUN: sudo dnf" in out


# ── 02 cli_tools ─────────────────────────────────────────────────────────────


def test_cli_tools_installs_starship(
    ctx: Context, capsys: pytest.CaptureFixture[str]
) -> None:
    """starship installation must be attempted via the official URL installer."""
    _run("02-cli", ctx)
    out = capsys.readouterr().out
    assert "starship" in out
    assert "starship.rs/install.sh" in out


# ── 04 kernel ─────────────────────────────────────────────────────────────────


def test_kernel_skipped_on_wsl(
    ctx: Context, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("IS_WSL", "1")
    _run("04-kernel", ctx)
    out = capsys.readouterr().out
    assert "WSL: skipping kernel module" in out
    assert "kernel-devel" not in out


def test_kernel_runs_on_native(
    ctx: Context, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("IS_WSL", "0")
    _run("04-kernel", ctx)
    out = capsys.readouterr().out
    assert "kernel-devel" in out
    assert "DRY_RUN: sudo systemctl enable" in out


# ── 08 fonts ──────────────────────────────────────────────────────────────────


def test_fonts_skips_kde_on_wsl(
    ctx: Context, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("IS_WSL", "1")
    _run("08-fonts", ctx)
    out = capsys.readouterr().out
    assert "WSL: skipping KDE" in out
    assert "kwriteconfig6" not in out


# ── 10 gpu ────────────────────────────────────────────────────────────────────


def test_gpu_skips_akmod_on_wsl(
    ctx: Context, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("IS_WSL", "1")
    monkeypatch.setenv("HAS_NVIDIA", "1")
    _run("10-gpu", ctx)
    out = capsys.readouterr().out
    assert "WSL: skipping akmod" in out
    assert "akmod-nvidia" not in out
    assert "wsl/lib" in out


def test_gpu_installs_akmod_on_native(
    ctx: Context, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("IS_WSL", "0")
    monkeypatch.setenv("HAS_NVIDIA", "1")
    _run("10-gpu", ctx)
    out = capsys.readouterr().out
    assert "akmod-nvidia" in out
    assert "wsl/lib" not in out


# ── 11 editors ────────────────────────────────────────────────────────────────


def test_editors_skips_vscode_on_wsl(
    ctx: Context, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("IS_WSL", "1")
    _run("11-editors", ctx)
    out = capsys.readouterr().out
    assert "WSL: skipping VS Code" in out
    assert "vscode.repo" not in out
    assert "windsurf.repo" not in out


def test_editors_includes_vscode_on_native(
    ctx: Context, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("IS_WSL", "0")
    _run("11-editors", ctx)
    out = capsys.readouterr().out
    assert "vscode.repo" in out


# ── 13 shell ──────────────────────────────────────────────────────────────────


def test_shell_writes_markers(tmp_path: Path) -> None:
    # Use a non-dry-run context so the module actually writes the file.
    real_ctx = Context(dry_run=False, home=tmp_path)
    _run("13-shell", real_ctx)
    text = real_ctx.shell_init_path.read_text()
    for marker in ("zoxide init", "fzf keybindings", "eza aliases", "bat alias"):
        assert marker in text


def test_shell_is_idempotent(tmp_path: Path) -> None:
    real_ctx = Context(dry_run=False, home=tmp_path)
    _run("13-shell", real_ctx)
    _run("13-shell", real_ctx)
    text = real_ctx.shell_init_path.read_text()
    # Each marker should appear exactly once in the begin-fence comment.
    assert text.count("# >>> fedora-setup: zoxide init >>>") == 1


# ── module registry sanity ────────────────────────────────────────────────────


def test_module_order_has_thirteen_modules() -> None:
    assert len(MODULE_ORDER) == 13


def test_each_module_has_run_callable() -> None:
    for name, module in MODULE_ORDER:
        assert hasattr(module, "run"), f"{name} is missing run()"
        assert callable(module.run), f"{name}.run is not callable"


def test_modules_can_all_be_imported() -> None:
    for name, _module in MODULE_ORDER:
        importlib.import_module(f"fedora_setup.modules.{_module.__name__.split('.')[-1]}")
