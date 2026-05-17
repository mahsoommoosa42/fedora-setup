"""Module 09 · Rust via rustup."""

from __future__ import annotations

import subprocess

from .. import colors, runner, shell_init
from ..context import Context

CARGO_TOOLS = (
    "cargo-watch",
    "cargo-expand",
    "cargo-nextest",
    "cargo-audit",
    "cargo-bloat",
    "cargo-flamegraph",
)

EXTRA_CRATES = ("bandwhich", "hexyl", "du-dust", "sd")


def run(ctx: Context) -> None:
    colors.section("9 · Rust via rustup")

    cargo_bin = ctx.home / ".cargo" / "bin"
    rustup = str(cargo_bin / "rustup")
    cargo = str(cargo_bin / "cargo")

    if runner.command_exists("rustup") or cargo_bin.joinpath("rustup").exists():
        colors.info("rustup already installed, updating...")
        if ctx.dry_run:
            print("DRY_RUN: rustup update")
        else:
            subprocess.run([rustup, "update"], check=False)
    else:
        colors.info("Installing Rust via rustup...")
        runner.run_installer(
            ctx,
            "https://sh.rustup.rs",
            "-y",
            "--default-toolchain", "stable",
            "--profile", "default",
            "--component", "rust-analyzer",
            "--component", "rust-src",
            "--component", "clippy",
            "--component", "rustfmt",
        )

    shell_init.clean_shell_init(ctx, "rustup PATH")
    shell_init.append_to_shell_init(
        ctx,
        "rustup PATH",
        '. "$HOME/.cargo/env"',
    )

    colors.info("Adding Rust targets...")
    if ctx.dry_run:
        print("DRY_RUN: rustup target add aarch64-unknown-linux-gnu thumbv7em-none-eabihf")
    else:
        subprocess.run([rustup, "target", "add", "aarch64-unknown-linux-gnu"], check=False)
        subprocess.run([rustup, "target", "add", "thumbv7em-none-eabihf"], check=False)

    colors.info("Installing cargo tools...")
    for crate in CARGO_TOOLS:
        runner.cargo_install(ctx, crate, cargo=cargo)

    colors.info("Installing extra CLI tools via cargo (not in Fedora repos)...")
    for crate in EXTRA_CRATES:
        runner.cargo_install(ctx, crate, cargo=cargo)

    colors.success("Rust ready")
