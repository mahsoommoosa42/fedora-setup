"""Module 11 · Editors, LSP, DAP & Zellij terminal workspace."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .. import colors, detect, runner, shell_init
from ..context import Context

VSCODE_REPO = """[code]
name=Visual Studio Code
baseurl=https://packages.microsoft.com/yumrepos/vscode
enabled=1
gpgcheck=1
gpgkey=https://packages.microsoft.com/keys/microsoft.asc"""

# Zellij is not yet packaged in Fedora 44 repos — install pre-built musl binary.
ZELLIJ_URL = (
    "https://github.com/zellij-org/zellij/releases/latest/download/"
    "zellij-x86_64-unknown-linux-musl.tar.gz"
)

_ASSETS = Path(__file__).parent.parent / "assets"


def _install_uv_tool(ctx: Context, tool: str) -> None:
    if ctx.dry_run:
        print(f"DRY_RUN: uv tool install {tool}")
        return
    result = subprocess.run(["uv", "tool", "install", tool], check=False)
    if result.returncode != 0:
        colors.warn(f"uv tool install {tool} failed (exit {result.returncode}) — continuing")


def run(ctx: Context) -> None:
    colors.section("11 · Editors, LSP, DAP & Zellij")

    # ── Neovim + system LSP/DAP packages ─────────────────────────────────────
    colors.info("Installing Neovim, clangd, LLDB...")
    runner.dnf_install(ctx, "neovim", "nodejs", "clang-tools-extra", "lldb")

    colors.info("Installing pyright and debugpy via uv...")
    for tool in ("pyright", "debugpy"):
        _install_uv_tool(ctx, tool)

    colors.info("Writing Neovim IDE configuration to ~/.config/nvim ...")
    nvim_dst = ctx.home / ".config" / "nvim"
    runner.copy_tree(ctx, _ASSETS / "nvim", nvim_dst)
    colors.success("Neovim ready — launch with: nvim  (plugins bootstrap on first run)")

    # ── Zellij: pre-built binary from GitHub (not yet in Fedora 44 repos) ────
    colors.info("Installing Zellij from GitHub release (not in Fedora 44 repos)...")
    bin_dir = ctx.home / ".local" / "bin"
    runner.download_extract_tarball(ctx, ZELLIJ_URL, bin_dir)

    if not ctx.dry_run:
        zellij_bin = bin_dir / "zellij"
        if zellij_bin.exists():
            zellij_bin.chmod(0o755)
            colors.success(f"Zellij installed at {zellij_bin}")
        else:
            colors.warn(
                "Zellij binary not found after download — "
                f"check network access or download manually: {ZELLIJ_URL}"
            )

    colors.info("Writing Zellij configuration to ~/.config/zellij ...")
    runner.copy_tree(ctx, _ASSETS / "zellij", ctx.home / ".config" / "zellij")

    shell_init.clean_shell_init(ctx, "zellij alias")
    shell_init.append_to_shell_init(
        ctx,
        "zellij alias",
        "# Zellij — terminal workspace (Alt prefix, see CHEATSHEET.md)\n"
        "alias zj='zellij'",
    )

    # Disable XON/XOFF flow control so Ctrl+S reaches Neovim over SSH
    shell_init.clean_shell_init(ctx, "stty -ixon")
    shell_init.append_to_shell_init(
        ctx,
        "stty -ixon",
        "# Disable XON/XOFF so Ctrl+S works in Neovim over SSH\n"
        "stty -ixon 2>/dev/null || true",
    )

    colors.success("Zellij ready — launch with: zellij  (or: zj)")

    # ── VS Code (native only) ─────────────────────────────────────────────────
    if detect.is_wsl():
        colors.info("WSL: skipping VS Code RPM installation")
        colors.info("  → Install VS Code for Windows and use the Remote-WSL extension")
        colors.info("  → Or run: curl -fsSL https://code-server.dev/install.sh | sh")
    else:
        colors.info("Adding VS Code Microsoft repository...")
        runner.rpm_import(ctx, "https://packages.microsoft.com/keys/microsoft.asc")
        runner.sudo_tee_repo(ctx, "/etc/yum.repos.d/vscode.repo", VSCODE_REPO)
        colors.info("Installing VS Code...")
        runner.dnf_install(ctx, "code")
        colors.success("VS Code installed — launch with: code")

    # ── Devin CLI (all platforms) ─────────────────────────────────────────────
    colors.info("Installing Devin CLI...")
    runner.run_installer(ctx, "https://cli.devin.ai/install.sh")
    colors.success("Devin CLI installed — run: devin  (also available as a Zellij tab)")
