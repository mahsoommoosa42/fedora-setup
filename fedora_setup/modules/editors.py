"""Module 11 · Editors & LSP support."""

from __future__ import annotations

import subprocess

from .. import colors, detect, runner
from ..context import Context

VSCODE_REPO = """[code]
name=Visual Studio Code
baseurl=https://packages.microsoft.com/yumrepos/vscode
enabled=1
gpgcheck=1
gpgkey=https://packages.microsoft.com/keys/microsoft.asc"""


def run(ctx: Context) -> None:
    colors.section("11 · Editors & LSP Support")

    colors.info("Installing Neovim...")
    # nodejs is needed by some nvim LSP plugins
    runner.dnf_install(ctx, "neovim", "nodejs")

    colors.info("Installing clangd LSP...")
    runner.dnf_install(ctx, "clang-tools-extra")

    colors.info("Installing pyright via uv...")
    if ctx.dry_run:
        print("DRY_RUN: uv tool install pyright")
    else:
        subprocess.run(["uv", "tool", "install", "pyright"], check=False)

    colors.success("clangd and pyright installed")

    if detect.is_wsl():
        colors.info("WSL: skipping VS Code RPM installation")
        colors.info("  → Install VS Code for Windows and use the Remote-WSL extension")
        colors.info("  → Or run: curl -fsSL https://code-server.dev/install.sh | sh")
        return

    colors.info("Adding VS Code repository...")
    runner.rpm_import(ctx, "https://packages.microsoft.com/keys/microsoft.asc")
    runner.sudo_tee_repo(ctx, "/etc/yum.repos.d/vscode.repo", VSCODE_REPO)
    runner.dnf_install(ctx, "code")
    colors.success("VS Code installed — launch with: code")

    colors.info("Installing Devin CLI...")
    runner.run_installer(ctx, "https://cli.devin.ai/install.sh")
    colors.success("Devin CLI installed — run: devin")
