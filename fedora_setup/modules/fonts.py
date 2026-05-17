"""Module 08 · Nerd Fonts + KDE/Konsole config."""

from __future__ import annotations

import subprocess
import tarfile
import tempfile
import urllib.request
from pathlib import Path

from .. import colors, detect, runner
from ..context import Context

NF_BASE = "https://github.com/ryanoasis/nerd-fonts/releases/latest/download"
KONSOLE_PROFILE = """[Appearance]
ColorScheme=Dracula
Font=JetBrainsMono Nerd Font Mono,12,-1,5,400,0,0,0,0,0,0,0,0,0,0,1

[General]
Name=Dev
Parent=FALLBACK/
TerminalCenter=true
TerminalMargin=6

[Scrolling]
ScrollBarPosition=2
"""


def _font_already_installed(fonts_dir: Path, font_name: str) -> bool:
    if not fonts_dir.exists():
        return False
    return any(font_name in p.name for p in fonts_dir.iterdir())


def _install_nerd_font(ctx: Context, fonts_dir: Path, font_name: str) -> None:
    if _font_already_installed(fonts_dir, font_name):
        colors.info(f"Font {font_name} already installed, skipping")
        return

    if ctx.dry_run:
        print(f"DRY_RUN: install Nerd Font {font_name}")
        return

    archive = f"{font_name}.tar.xz"
    target_dir = fonts_dir / font_name
    target_dir.mkdir(parents=True, exist_ok=True)

    colors.info(f"Downloading {font_name} Nerd Font...")
    with tempfile.TemporaryDirectory() as tmp:
        archive_path = Path(tmp) / archive
        urllib.request.urlretrieve(f"{NF_BASE}/{archive}", archive_path)
        try:
            with tarfile.open(archive_path) as tf:
                ttf_members = [m for m in tf.getmembers() if m.name.endswith(".ttf")]
                tf.extractall(target_dir, members=ttf_members)
        except (tarfile.TarError, OSError):
            pass
    colors.success(f"{font_name} Nerd Font installed")


def run(ctx: Context) -> None:
    colors.section("8 · Nerd Fonts")

    fonts_dir = ctx.home / ".local" / "share" / "fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)

    for font in ("JetBrainsMono", "FiraCode", "CascadiaCode", "Meslo"):
        _install_nerd_font(ctx, fonts_dir, font)

    if ctx.dry_run:
        print(f"DRY_RUN: fc-cache -f {fonts_dir}")
    else:
        colors.info("Refreshing font cache...")
        subprocess.run(["fc-cache", "-f", str(fonts_dir)], check=False)

    if detect.is_wsl():
        colors.info("WSL: skipping KDE font and Konsole profile configuration")
        return

    if runner.command_exists("kwriteconfig6"):
        kw_args = [
            "kwriteconfig6",
            "--file", "kdeglobals",
            "--group", "General",
            "--key", "fixed",
            "JetBrainsMono Nerd Font Mono,11,-1,5,400,0,0,0,0,0,0,0,0,0,0,1",
        ]
        if ctx.dry_run:
            print(f"DRY_RUN: {' '.join(kw_args)}")
        else:
            subprocess.run(kw_args, check=False)
            subprocess.run(
                [
                    "qdbus6",
                    "org.kde.KGlobalSettings",
                    "/KGlobalSettings",
                    "notifyChange",
                    "4",
                    "0",
                ],
                check=False,
                stderr=subprocess.DEVNULL,
            )
        colors.success("KDE monospace font set to JetBrainsMono Nerd Font Mono 11pt")
    else:
        colors.warn(
            "kwriteconfig6 not found — set font manually in "
            "System Settings \u2192 Fonts \u2192 Fixed width"
        )

    konsole_dir = ctx.home / ".local" / "share" / "konsole"
    konsole_profile = konsole_dir / "Dev.profile"
    if not konsole_profile.exists():
        if ctx.dry_run:
            print(f"DRY_RUN: write Konsole 'Dev' profile to {konsole_profile}")
        else:
            konsole_dir.mkdir(parents=True, exist_ok=True)
            konsole_profile.write_text(KONSOLE_PROFILE, encoding="utf-8")
        colors.success("Konsole 'Dev' profile created")


__all__ = ["run", "_install_nerd_font", "shutil"]
