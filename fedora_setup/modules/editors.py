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

_ASSETS = Path(__file__).parent.parent / "assets"


def run(ctx: Context) -> None:
    colors.section("11 · Editors, LSP, DAP & Zellij")

    # ── Neovim + system LSP/DAP dependencies ─────────────────────────────────
    colors.info("Installing Neovim + LSP/DAP system packages...")
    runner.dnf_install(ctx, "neovim", "nodejs", "clang-tools-extra", "lldb")

    colors.info("Installing Python LSP and DAP tools via uv...")
    for tool in ("pyright", "debugpy"):
        if ctx.dry_run:
            print(f"DRY_RUN: uv tool install {tool}")
        else:
            subprocess.run(["uv", "tool", "install", tool], check=False)

    colors.info("Writing Neovim IDE configuration...")
    runner.copy_tree(ctx, _ASSETS / "nvim", ctx.home / ".config" / "nvim")
    colors.success("Neovim ready — launch with: nvim  (plugins install on first run)")

    # ── Zellij terminal workspace ─────────────────────────────────────────────
    colors.info("Installing Zellij terminal workspace...")
    runner.dnf_install(ctx, "zellij")

    colors.info("Writing Zellij configuration...")
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
        "# Allow Ctrl+S in terminal apps (disables XON/XOFF flow control)\n"
        "stty -ixon 2>/dev/null || true",
    )

    colors.success("Zellij ready — launch with: zellij  (or: zj)")

    # ── VS Code (native only) ─────────────────────────────────────────────────
    if detect.is_wsl():
        colors.info("WSL: skipping VS Code RPM installation")
        colors.info("  → Install VS Code for Windows and use the Remote-WSL extension")
        colors.info("  → Or run: curl -fsSL https://code-server.dev/install.sh | sh")
    else:
        colors.info("Adding VS Code repository...")
        runner.rpm_import(ctx, "https://packages.microsoft.com/keys/microsoft.asc")
        runner.sudo_tee_repo(ctx, "/etc/yum.repos.d/vscode.repo", VSCODE_REPO)
        runner.dnf_install(ctx, "code")
        colors.success("VS Code installed — launch with: code")

    # ── Devin CLI (all platforms) ─────────────────────────────────────────────
    colors.info("Installing Devin CLI...")
    runner.run_installer(ctx, "https://cli.devin.ai/install.sh")
    colors.success("Devin CLI installed — run: devin  (also available as a Zellij tab)")
