"""Module 12 · Git configuration."""

from __future__ import annotations

import subprocess

from .. import colors, detect
from ..context import Context

GIT_GLOBAL_DEFAULTS: tuple[tuple[str, str], ...] = (
    ("core.pager", "delta"),
    ("delta.navigate", "true"),
    ("delta.line-numbers", "true"),
    ("delta.syntax-theme", "Dracula"),
    ("merge.conflictstyle", "diff3"),
    ("diff.colorMoved", "default"),
    ("pull.rebase", "true"),
    ("init.defaultBranch", "main"),
    ("rerere.enabled", "true"),
    ("fetch.prune", "true"),
)


def _git_config_get(key: str) -> str:
    try:
        result = subprocess.run(
            ["git", "config", "--global", key],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def _git_config_set(key: str, value: str) -> None:
    subprocess.run(["git", "config", "--global", key, value], check=False)


def run(ctx: Context) -> None:
    colors.section("12 · Git Config")

    colors.info("Configuring git defaults...")
    if ctx.dry_run:
        print(
            "DRY_RUN: git config --global "
            "(core.pager=delta, merge, diff, pull, init, rerere, fetch)"
        )
    else:
        for key, value in GIT_GLOBAL_DEFAULTS:
            _git_config_set(key, value)

    if not _git_config_get("user.name"):
        if detect.is_interactive():
            print()
            git_name = input("  Git user.name:  ").strip()
            git_email = input("  Git user.email: ").strip()
            if not ctx.dry_run:
                _git_config_set("user.name", git_name)
                _git_config_set("user.email", git_email)
            colors.success("Git identity configured")
        else:
            colors.warn("No TTY — skipping git identity prompt. Run after first boot:")
            colors.warn("  git config --global user.name  'Your Name'")
            colors.warn("  git config --global user.email 'you@example.com'")
    else:
        colors.info(f"Git identity already set: {_git_config_get('user.name')}")

    colors.success("Git configured with delta as pager")
