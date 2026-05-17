"""Module 02 · Extra CLI tooling (gh, lazygit, starship, …)."""

from __future__ import annotations

from .. import colors, runner, shell_init
from ..context import Context


def run(ctx: Context) -> None:
    colors.section("2 · Extra CLI Tooling")

    colors.info("Installing dnf-plugins-core...")
    runner.dnf_install(ctx, "dnf-plugins-core")

    colors.info("Installing modern CLI tools from standard repos...")
    runner.dnf_install(
        ctx,
        "gh", "direnv", "tokei", "hyperfine", "just", "mold",
    )

    colors.info("Enabling lazygit COPR and installing...")
    runner.dnf_copr_enable(ctx, "atim/lazygit")
    runner.dnf_install(ctx, "lazygit")

    colors.info("Note: bandwhich, hexyl, dust, sd will be installed via cargo in Section 9")

    colors.info("Installing starship prompt...")
    local_bin = ctx.home / ".local" / "bin"
    if not ctx.dry_run:
        local_bin.mkdir(parents=True, exist_ok=True)
    # Install to ~/.local/bin to avoid the sudo requirement for /usr/local/bin.
    # The starship script also requires sh (not bash) to avoid POSIX warnings.
    runner.run_installer(
        ctx, "https://starship.rs/install.sh", "-y", "--bin-dir", str(local_bin),
    )

    # Ensure ~/.local/bin is on PATH before starship init runs.
    shell_init.append_to_shell_init(
        ctx,
        "local bin path",
        'export PATH="$HOME/.local/bin:$PATH"',
    )

    starship_config = ctx.home / ".config" / "starship.toml"
    shell_init.remove_file(ctx, starship_config)
    shell_init.clean_shell_init(ctx, "starship init")

    if not starship_config.exists():
        colors.info("Creating default starship config with nerd-font preset...")
        starship_config.parent.mkdir(parents=True, exist_ok=True)
        runner.run_to_file(ctx, ["starship", "preset", "nerd-font"], starship_config)
    else:
        colors.info(f"Starship config already exists at {starship_config} (skipping preset)")

    shell_init.append_to_shell_init(
        ctx,
        "starship init",
        '# Starship — cross-shell prompt\n'
        'eval "$(starship init bash)"',
    )

    colors.success("Extra tooling installed")
