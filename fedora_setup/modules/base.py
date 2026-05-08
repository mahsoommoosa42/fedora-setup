"""Module 01 · System update & base tools."""

from __future__ import annotations

from .. import colors, runner
from ..context import Context


def run(ctx: Context) -> None:
    colors.section("1 · System Update & Base Tools")

    colors.info("Updating system packages...")
    runner.dnf_upgrade(ctx)

    colors.info("Installing essential base tools...")
    # fd (not fd-find) is the correct Fedora package name
    runner.dnf_install(
        ctx,
        "curl", "wget", "git", "git-delta",
        "htop", "btop",
        "ripgrep", "fd", "fzf", "jq",
        "bat", "eza", "zoxide",
        "man-pages", "bash-completion",
        "tmux", "stow",
    )

    colors.success("Base tools installed")
