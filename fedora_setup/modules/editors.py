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

WINDSURF_REPO = """[windsurf]
name=Windsurf Editor
baseurl=https://windsurf-stable.codeiumdata.com/wVxpZuBSvCwhYjtp/rpm/stable/x86_64
enabled=1
gpgcheck=1
gpgkey=https://windsurf-stable.codeiumdata.com/wVxpZuBSvCwhYjtp/windsurf.gpg"""


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
        colors.info("WSL: skipping VS Code and Windsurf RPM installation")
        colors.info("  \u2192 Install VS Code for Windows and use the Remote-WSL extension")
        colors.info("  \u2192 Or run: curl -fsSL https://code-server.dev/install.sh | sh")
        return

    colors.info("Adding VS Code repository...")
    runner.rpm_import(ctx, "https://packages.microsoft.com/keys/microsoft.asc")
    runner.sudo_tee_repo(ctx, "/etc/yum.repos.d/vscode.repo", VSCODE_REPO)
    runner.dnf_install(ctx, "code")
    colors.success("VS Code installed — launch with: code")

    colors.info("Adding Windsurf repository...")
    runner.rpm_import(
        ctx,
        "https://windsurf-stable.codeiumdata.com/wVxpZuBSvCwhYjtp/windsurf.gpg",
    )
    runner.sudo_tee_repo(ctx, "/etc/yum.repos.d/windsurf.repo", WINDSURF_REPO)
    runner.dnf_install(ctx, "windsurf")
    colors.success("Windsurf installed — launch with: windsurf")
