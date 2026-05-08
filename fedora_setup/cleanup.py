"""Cleanup tool — port of ``cleanup.sh``.

Removes shell-init source lines, the shell-init file itself, tool config
files and (optionally) installed packages. Runnable via:

    python3 -m fedora_setup.cleanup [--dry-run] [--remove-packages]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from . import colors
from .context import Context

PACKAGES_TO_REMOVE: tuple[str, ...] = (
    "starship", "zoxide", "eza", "bat", "fzf", "ripgrep",
    "fd-find", "btop", "lazygit", "neovim", "uv", "bun",
)


def _file_contains(path: Path, needle: str) -> bool:
    if not path.is_file():
        return False
    try:
        return needle in path.read_text(errors="ignore")
    except OSError:
        return False


def _remove_source_line(ctx: Context, file: Path) -> None:
    if not file.is_file():
        return

    source_line = f'source "{ctx.shell_init_path}"'
    if not _file_contains(file, source_line):
        return

    if ctx.dry_run:
        print(f"DRY_RUN: Would remove source line from {file}")
        return

    colors.info(f"Removing source line from {file}")
    lines = file.read_text(encoding="utf-8").splitlines(keepends=True)
    file.write_text(
        "".join(line for line in lines if source_line not in line),
        encoding="utf-8",
    )


def _remove_file(ctx: Context, path: Path) -> None:
    if not path.is_file():
        return
    if ctx.dry_run:
        print(f"DRY_RUN: Would remove {path}")
        return
    colors.info(f"Removing {path}")
    path.unlink()


def _maybe_remove_directory(ctx: Context, directory: Path) -> None:
    if not directory.is_dir():
        return
    try:
        if any(directory.iterdir()):
            return
    except OSError:
        return
    if ctx.dry_run:
        print(f"DRY_RUN: Would remove empty directory {directory}")
    else:
        try:
            directory.rmdir()
        except OSError:
            pass


def _confirm(prompt: str) -> bool:
    try:
        response = input(prompt).strip()
    except EOFError:
        return False
    return response == "yes"


def _remove_packages(ctx: Context) -> None:
    colors.warn("--remove-packages is DANGEROUS and may break your system.")
    if not ctx.dry_run and not _confirm("Really remove packages? [yes/NO]: "):
        colors.info("Skipping package removal")
        return

    colors.info("Removing packages...")
    installed: list[str] = []
    for pkg in PACKAGES_TO_REMOVE:
        try:
            result = subprocess.run(
                ["rpm", "-q", pkg],
                capture_output=True,
                check=False,
            )
        except FileNotFoundError:
            return
        if result.returncode == 0:
            installed.append(pkg)

    if not installed:
        return

    if ctx.dry_run:
        print(f"DRY_RUN: Would remove: {' '.join(installed)}")
    else:
        subprocess.run(
            ["sudo", "dnf", "remove", "-y", *installed],
            check=False,
        )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Remove all configurations added by fedora-setup.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without changing anything",
    )
    parser.add_argument(
        "--remove-packages",
        action="store_true",
        help="Also remove installed packages (dangerous)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    ctx = Context.from_env(dry_run=args.dry_run)

    if not ctx.dry_run:
        print(colors.BOLD)
        print("  This will remove ALL configurations added by fedora-setup.")
        print(f"  {colors.RED}This action cannot be undone.{colors.RESET}")
        print()
        if not _confirm("Continue? [yes/NO]: "):
            colors.info("Aborted")
            return 0

    colors.info("Removing source line from shell configs...")
    for cfg_name in (".bashrc", ".zshrc", ".bash_profile"):
        _remove_source_line(ctx, ctx.home / cfg_name)

    colors.info("Removing shell-init file...")
    _remove_file(ctx, ctx.shell_init_path)
    _maybe_remove_directory(ctx, ctx.shell_init_path.parent)

    colors.info("Removing tool configuration files...")
    _remove_file(ctx, ctx.home / ".config" / "starship.toml")
    _remove_file(ctx, ctx.home / ".ccache" / "ccache.conf")
    _remove_file(ctx, ctx.home / ".fzf")

    if args.remove_packages:
        _remove_packages(ctx)
    elif not ctx.dry_run:
        colors.info("Package removal skipped (use --remove-packages to enable)")

    print()
    if ctx.dry_run:
        colors.success("Dry run complete. No changes were made.")
        colors.info("Run without --dry-run to actually remove configurations.")
    else:
        colors.success("Cleanup complete.")
        colors.info("Restart your shell or run 'exec bash' to apply changes.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
