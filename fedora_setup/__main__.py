"""Entry point for ``python3 -m fedora_setup``.

Replaces the old ``setup.sh`` orchestrator. Builds a :class:`Context` from
environment variables / CLI args, runs the pre-flight checks, then
imports each module in :data:`fedora_setup.modules.MODULE_ORDER` and calls
``module.run(ctx)``.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import colors, detect
from .context import Context
from .modules import MODULE_ORDER
from .shell_init import ensure_shell_init

BANNER = """\
  \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510
  \u2502       Fedora KDE Dev Environment Setup      \u2502
  \u2502  C++ \u00b7 Python \u00b7 JS \u00b7 Rust \u00b7 Kernel          \u2502
  \u2502  CUDA \u00b7 Vulkan \u00b7 FFmpeg                     \u2502
  \u2502  Claude Code \u00b7 Devin \u00b7 Fonts \u00b7 VS Code      \u2502
  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518\
"""


def _is_root() -> bool:
    if hasattr(os, "geteuid"):
        return os.geteuid() == 0
    return False


def _is_fedora() -> bool:
    try:
        return "Fedora" in Path("/etc/os-release").read_text(errors="ignore")
    except OSError:
        return False


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fedora_setup",
        description="Configure a Fedora developer workstation (native or WSL2).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying the system.",
    )
    parser.add_argument(
        "--clean-install",
        action="store_true",
        help="Remove existing fedora-setup configuration before installing.",
    )
    return parser


def _print_banner_and_env(ctx: Context) -> None:
    print(colors.BOLD)
    print(BANNER)
    print(colors.RESET)

    env_label = "WSL2 Fedora" if detect.is_wsl() else "Native Fedora"
    nvidia_label = "detected" if detect.has_nvidia() else "not detected"
    systemd_label = "available" if detect.has_systemd() else "not available"

    colors.info(f"Environment : {env_label}")
    colors.info(f"NVIDIA GPU  : {nvidia_label}")
    colors.info(f"systemd     : {systemd_label}")

    if ctx.dry_run:
        colors.warn("DRY_RUN mode \u2014 no changes will be made to this system")
    if ctx.clean_install:
        colors.warn("CLEAN_INSTALL mode \u2014 existing configs will be removed")

    print()


def _print_summary(ctx: Context) -> None:
    print()
    print(f"{colors.BOLD}{colors.GREEN}  All done! Reload your shell:{colors.RESET}")
    print()
    print(f"    {colors.YELLOW}source ~/.bashrc{colors.RESET}")
    print()
    print(f"{colors.BOLD}  Quick reference:{colors.RESET}")
    print(f"    {colors.BLUE}C++{colors.RESET}      \u2192  cmake, ninja, clangd, bear, ccache, mold")
    print(f"    {colors.BLUE}Python{colors.RESET}   \u2192  uv init / uv add / uv run / ruff / mypy")
    print(f"    {colors.BLUE}JS/TS{colors.RESET}    \u2192  bun init / bun add / bun run / tsx")
    print(f"    {colors.BLUE}Rust{colors.RESET}     \u2192  cargo new / cargo nextest / cargo watch")

    if not detect.is_wsl():
        print(
            f"    {colors.BLUE}Kernel{colors.RESET}   \u2192  "
            "kernel-devel, qemu-kvm, bpftrace, aarch64 cross-gcc"
        )

    print(f"    {colors.BLUE}CUDA{colors.RESET}     \u2192  nvcc --version / nvidia-smi  (NVIDIA GPU only)")
    print(f"    {colors.BLUE}Vulkan{colors.RESET}   \u2192  vulkaninfo --summary / glslc (via shaderc)")
    print(f"    {colors.BLUE}FFmpeg{colors.RESET}   \u2192  ffmpeg -hwaccels")

    ai_tools = "claude / devin" if detect.is_wsl() else "claude / devin / code"
    print(f"    {colors.BLUE}AI{colors.RESET}       \u2192  {ai_tools}")

    print(f"    {colors.BLUE}Git TUI{colors.RESET}  \u2192  lazygit")
    print(f"    {colors.BLUE}Fonts{colors.RESET}    \u2192  JetBrainsMono / FiraCode / CascadiaCode Nerd Fonts")
    print(f"    {colors.BLUE}Prompt{colors.RESET}   \u2192  starship (configure: ~/.config/starship.toml)")
    print()

    if not detect.is_wsl():
        print(
            f"{colors.YELLOW}  Note: Log out and back in for kvm/libvirt "
            f"group changes to take effect.{colors.RESET}"
        )
        print(
            f"{colors.YELLOW}  Note: Reboot required after NVIDIA driver "
            f"installation.{colors.RESET}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    overrides: dict[str, object] = {}
    if args.dry_run:
        overrides["dry_run"] = True
    if args.clean_install:
        overrides["clean_install"] = True
    ctx = Context.from_env(**overrides)

    if _is_root():
        colors.die("Do not run as root. sudo will be invoked when needed.")

    if not _is_fedora():
        colors.warn("This script targets Fedora. Proceed at your own risk on other distros.")

    # Ensure the shell-init file exists and is sourced from each shell config
    # before any module tries to append to it.
    ensure_shell_init(ctx, ctx.bashrc)
    zshrc = ctx.home / ".zshrc"
    if zshrc.is_file():
        ensure_shell_init(ctx, zshrc)
    bash_profile = ctx.home / ".bash_profile"
    if bash_profile.is_file():
        ensure_shell_init(ctx, bash_profile)

    _print_banner_and_env(ctx)

    for _name, module in MODULE_ORDER:
        module.run(ctx)

    _print_summary(ctx)
    return 0


if __name__ == "__main__":
    sys.exit(main())
