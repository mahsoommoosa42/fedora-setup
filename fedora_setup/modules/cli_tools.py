"""Module 02 · Extra CLI tooling (gh, lazygit, starship, …)."""

from __future__ import annotations

import subprocess

from .. import colors, runner, shell_init
from ..context import Context


def run(ctx: Context) -> None:
    colors.section("2 · Extra CLI Tooling")

    colors.info("Installing dnf-plugins-core...")
    runner.dnf_install(ctx, "dnf-plugins-core")

    colors.info("Installing modern CLI tools from standard repos...")
    runner.dnf_install(
        ctx,
        "gh", "direnv", "tokei", "hyperfine", "bottom", "just", "mold",
    )

    colors.info("Enabling lazygit COPR and installing...")
    runner.dnf_copr_enable(ctx, "atim/lazygit")
    runner.dnf_install(ctx, "lazygit")

    colors.info("Note: bandwhich, hexyl, dust, sd will be installed via cargo in Section 9")

    colors.info("Installing starship prompt...")
    runner.run_installer(ctx, "https://starship.rs/install.sh", "-y")

    starship_config = ctx.home / ".config" / "starship.toml"
    shell_init.remove_file(ctx, starship_config)
    shell_init.clean_shell_init(ctx, "starship init")

    if not starship_config.exists():
        colors.info("Creating default starship config with nerd-font preset...")
        starship_config.parent.mkdir(parents=True, exist_ok=True)
        if ctx.dry_run:
            print(f"DRY_RUN: starship preset nerd-font > {starship_config}")
        else:
            with starship_config.open("w", encoding="utf-8") as f:
                subprocess.run(
                    ["starship", "preset", "nerd-font"],
                    stdout=f,
                    check=False,
                )
    else:
        colors.info(f"Starship config already exists at {starship_config} (skipping preset)")

    shell_init.append_to_shell_init(
        ctx,
        "starship init",
        '# Starship — cross-shell prompt\n'
        'eval "$(starship init bash)"',
    )

    colors.success("Extra tooling installed")
