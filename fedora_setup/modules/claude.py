"""Module 07 · Claude Code CLI."""

from __future__ import annotations

import subprocess

from .. import colors, runner
from ..context import Context


def run(ctx: Context) -> None:
    colors.section("7 · Claude Code")

    if runner.command_exists("claude"):
        colors.info("Claude Code already installed, updating...")
        if ctx.dry_run:
            print("DRY_RUN: claude update")
        else:
            subprocess.run(
                ["claude", "update"],
                check=False,
                stderr=subprocess.DEVNULL,
            )
    else:
        colors.info("Installing Claude Code...")
        runner.run_installer(ctx, "https://claude.ai/install.sh")

    colors.success("Claude Code installed — run: claude")
    colors.warn("Authenticate with your Anthropic account on first run")
