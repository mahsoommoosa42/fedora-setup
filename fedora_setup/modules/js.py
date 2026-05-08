"""Module 06 · JavaScript via Bun."""

from __future__ import annotations

import os
import subprocess

from .. import colors, runner, shell_init
from ..context import Context


def run(ctx: Context) -> None:
    colors.section("6 · JavaScript via Bun")

    if runner.command_exists("bun"):
        colors.info("Bun already installed, updating...")
        if ctx.dry_run:
            print("DRY_RUN: bun upgrade")
        else:
            subprocess.run(["bun", "upgrade"], check=False)
    else:
        colors.info("Installing Bun...")
        runner.run_installer(ctx, "https://bun.sh/install")

    shell_init.clean_shell_init(ctx, "bun PATH")

    shell_init.append_to_shell_init(
        ctx,
        "bun PATH",
        '# Bun — JavaScript runtime & package manager\n'
        'export BUN_INSTALL="$HOME/.bun"\n'
        'export PATH="$BUN_INSTALL/bin:$PATH"\n'
        '[ -s "$HOME/.bun/_bun" ] && source "$HOME/.bun/_bun"',
    )

    bun_install = ctx.home / ".bun"
    os.environ["BUN_INSTALL"] = str(bun_install)
    os.environ["PATH"] = f"{bun_install}/bin:{os.environ.get('PATH', '')}"

    colors.info("Installing global JS/TS tools...")
    if ctx.dry_run:
        print("DRY_RUN: bun install -g typescript tsx eslint prettier @antfu/ni")
    else:
        subprocess.run(
            ["bun", "install", "-g", "typescript", "tsx", "eslint", "prettier", "@antfu/ni"],
            check=False,
        )

    colors.success("Bun ready — use: bun init, bun add, bun run, bun test")
