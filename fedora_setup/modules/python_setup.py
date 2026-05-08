"""Module 05 · Python via uv."""

from __future__ import annotations

import os
import subprocess

from .. import colors, runner, shell_init
from ..context import Context


def run(ctx: Context) -> None:
    colors.section("5 · Python via uv")

    if runner.command_exists("uv"):
        colors.info("uv already installed, updating...")
        if ctx.dry_run:
            print("DRY_RUN: uv self update")
        else:
            subprocess.run(["uv", "self", "update"], check=False)
    else:
        colors.info("Installing uv...")
        runner.run_installer(ctx, "https://astral.sh/uv/install.sh")

    shell_init.clean_shell_init(ctx, "uv PATH")
    shell_init.clean_shell_init(ctx, "uv tool PATH")

    shell_init.append_to_shell_init(
        ctx,
        "uv PATH",
        '# uv — Python package manager\n'
        'export PATH="$HOME/.local/bin:$PATH"',
    )

    os.environ["PATH"] = f"{ctx.home}/.local/bin:{os.environ.get('PATH', '')}"

    colors.info("Installing Python 3.13 via uv...")
    if ctx.dry_run:
        print("DRY_RUN: uv python install 3.13")
    else:
        subprocess.run(["uv", "python", "install", "3.13"], check=False)

    colors.info("Installing global Python tools...")
    for tool in ("ruff", "mypy", "ipython", "pytest", "httpie"):
        if ctx.dry_run:
            print(f"DRY_RUN: uv tool install {tool}")
        else:
            subprocess.run(["uv", "tool", "install", tool], check=False)

    shell_init.append_to_shell_init(
        ctx,
        "uv tool PATH",
        '# uv tool binaries\n'
        'export PATH="$HOME/.local/share/uv/tools/bin:$PATH"\n'
        'eval "$(uv generate-shell-completion bash 2>/dev/null || true)"',
    )

    colors.success("Python ready — manage projects with: uv init, uv add, uv run")
