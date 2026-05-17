"""Side-effect wrappers (port of ``lib/utils.sh``).

Every function in this module respects ``ctx.dry_run``: when set, it prints
a ``DRY_RUN: ...`` line and returns without touching the system. The output
strings are kept identical to the Bash version so that integration tests
that grep the captured output continue to work.

Modules **must not** invoke ``subprocess.run`` directly. All side-effects go
through one of these wrappers.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Iterable

from . import colors
from .context import Context


def command_exists(cmd: str) -> bool:
    """Return ``True`` if ``cmd`` is on ``$PATH``."""
    return shutil.which(cmd) is not None


def _format_args(args: Iterable[str]) -> str:
    return " ".join(args)


def _dry(ctx: Context, message: str) -> bool:
    """Print ``DRY_RUN: <message>`` and return True when in dry-run mode."""
    if ctx.dry_run:
        print(f"DRY_RUN: {message}")
        return True
    return False


def _run(cmd: list[str], *, check: bool = True) -> int:
    """Thin wrapper around ``subprocess.run`` returning the exit code."""
    result = subprocess.run(cmd, check=False)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd)
    return result.returncode


# ── dnf wrappers ─────────────────────────────────────────────────────────────

def dnf_install(ctx: Context, *packages: str) -> None:
    if not packages:
        return
    if _dry(ctx, f"sudo dnf install -y {_format_args(packages)}"):
        return
    _run(["sudo", "dnf", "install", "-y", *packages])


def dnf_upgrade(ctx: Context) -> None:
    if _dry(ctx, "sudo dnf upgrade -y --refresh"):
        return
    _run(["sudo", "dnf", "upgrade", "-y", "--refresh"])


def dnf_copr_enable(ctx: Context, *repos: str) -> None:
    if _dry(ctx, f"sudo dnf copr enable -y {_format_args(repos)}"):
        return
    _run(["sudo", "dnf", "copr", "enable", "-y", *repos])


def dnf_remove(ctx: Context, *packages: str) -> None:
    if _dry(ctx, f"sudo dnf remove -y {_format_args(packages)}"):
        return
    # Mirror the Bash version: never fail the whole run if a package is missing.
    subprocess.run(
        ["sudo", "dnf", "remove", "-y", *packages],
        check=False,
        stderr=subprocess.DEVNULL,
    )


def dnf_group_update(ctx: Context, *groups: str) -> None:
    if _dry(ctx, f"sudo dnf groupupdate -y {_format_args(groups)}"):
        return
    _run(["sudo", "dnf", "groupupdate", "-y", *groups])


def dnf_config_manager(ctx: Context, *args: str) -> None:
    if _dry(ctx, f"sudo dnf config-manager {_format_args(args)}"):
        return
    _run(["sudo", "dnf", "config-manager", *args])


# ── systemctl / cargo / installers ───────────────────────────────────────────

def systemctl_enable(ctx: Context, *services: str) -> None:
    if _dry(ctx, f"sudo systemctl enable --now {_format_args(services)}"):
        return
    result = subprocess.run(
        ["sudo", "systemctl", "enable", "--now", *services],
        check=False,
    )
    if result.returncode != 0:
        colors.warn(
            "systemctl failed — run "
            f"'sudo systemctl enable --now {_format_args(services)}' after first boot"
        )


def cargo_install(ctx: Context, *crates: str) -> None:
    if _dry(ctx, f"cargo install --locked {_format_args(crates)}"):
        return
    result = subprocess.run(
        ["cargo", "install", "--locked", *crates],
        check=False,
    )
    if result.returncode != 0:
        colors.warn(f"Failed to install {_format_args(crates)} — skipping")


def run_installer(ctx: Context, url: str, *args: str) -> None:
    """Pipe ``curl -fsSL <url> | sh -s -- <args>`` (or the dry-run echo).

    Uses ``sh`` (not ``bash``) because many install scripts (e.g. starship)
    explicitly reject being run with bash to avoid non-POSIX behaviour.
    """
    if _dry(ctx, f"curl -fsSL {url} | sh -s -- {_format_args(args)}"):
        return
    curl = subprocess.Popen(
        ["curl", "-fsSL", url],
        stdout=subprocess.PIPE,
    )
    try:
        result = subprocess.run(["sh", "-s", "--", *args], stdin=curl.stdout, check=False)
    finally:
        if curl.stdout is not None:
            curl.stdout.close()
        curl.wait()
    if result.returncode != 0:
        colors.warn(f"Installer failed: {url}")


def rpm_import(ctx: Context, *keys: str) -> None:
    if _dry(ctx, f"sudo rpm --import {_format_args(keys)}"):
        return
    _run(["sudo", "rpm", "--import", *keys])


def sudo_tee_repo(ctx: Context, dest: str, content: str) -> None:
    if _dry(ctx, f"sudo tee {dest}"):
        return
    proc = subprocess.Popen(
        ["sudo", "tee", dest],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
    )
    proc.communicate(input=(content + "\n").encode("utf-8"))
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, ["sudo", "tee", dest])


def usermod_groups(ctx: Context, groups: str, user: str) -> None:
    if _dry(ctx, f"sudo usermod -aG {groups} {user}"):
        return
    _run(["sudo", "usermod", "-aG", groups, user])


# ── GPU / driver helpers ─────────────────────────────────────────────────────

def akmods_dracut(ctx: Context) -> None:
    if _dry(ctx, "sudo akmods --force && sudo dracut --force"):
        return
    subprocess.run(["sudo", "akmods", "--force"], check=False)
    subprocess.run(["sudo", "dracut", "--force"], check=False)


def download_file(ctx: Context, url: str, dest: Path) -> None:
    if _dry(ctx, f"download {url} -> {dest}"):
        return
    if shutil.which("wget"):
        _run(["wget", "-O", str(dest), url])
    elif shutil.which("curl"):
        _run(["curl", "-L", "-o", str(dest), url])
    else:
        colors.die("Neither wget nor curl available to download file")


def run_sudo_script(ctx: Context, script: Path, *args: str) -> None:
    cmd_str = f"sudo {script} {' '.join(args)}"
    if _dry(ctx, cmd_str):
        return
    subprocess.run(["sudo", str(script), *args], check=False)


def run_to_file(ctx: Context, cmd: list[str], output_file: Path) -> None:
    if _dry(ctx, f"{' '.join(cmd)} > {output_file}"):
        return
    with output_file.open("w", encoding="utf-8") as f:
        subprocess.run(cmd, stdout=f, check=False)


# ── filesystem helpers ───────────────────────────────────────────────────────

def remove_path(ctx: Context, path: Path | str) -> None:
    """Remove a file or symlink (used by cleanup)."""
    p = Path(path)
    if not p.exists() and not p.is_symlink():
        return
    if _dry(ctx, f"rm -f {p}"):
        return
    colors.info(f"Removing {p}")
    try:
        p.unlink()
    except IsADirectoryError:
        # rm -f on a directory is a no-op in Bash; mirror that.
        pass
    except FileNotFoundError:
        pass
