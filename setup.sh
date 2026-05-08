#!/usr/bin/env bash
# =============================================================================
# setup.sh — Fedora Dev Environment Setup
# Supports: Native Fedora KDE Plasma and WSL2 Fedora
# Usage:
#   ./setup.sh                           # real install
#   DRY_RUN=1 ./setup.sh                # safe preview (no changes made)
#   CLEAN_INSTALL=1 ./setup.sh          # remove existing configs before install
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$SCRIPT_DIR/lib/colors.sh"
source "$SCRIPT_DIR/lib/detect.sh"
source "$SCRIPT_DIR/lib/utils.sh"

# Ensure the shell-init file exists and is sourced from shell configs
# This must happen before any module tries to append to it
ensure_shell_init "$BASHRC"
if [[ -f "$HOME/.zshrc" ]]; then
    ensure_shell_init "$HOME/.zshrc"
fi
if [[ -f "$HOME/.bash_profile" ]]; then
    ensure_shell_init "$HOME/.bash_profile"
fi

[[ "$(id -u)" -eq 0 ]] && die "Do not run as root. sudo will be invoked when needed."

if ! grep -q "Fedora" /etc/os-release 2>/dev/null; then
    warn "This script targets Fedora. Proceed at your own risk on other distros."
fi

echo -e "${BOLD}"
cat <<'BANNER'
  ┌─────────────────────────────────────────────┐
  │       Fedora KDE Dev Environment Setup      │
  │  C++ · Python · JS · Rust · Kernel          │
  │  CUDA · Vulkan · FFmpeg                     │
  │  Claude Code · Fonts · VS Code · Windsurf   │
  └─────────────────────────────────────────────┘
BANNER
echo -e "${RESET}"

info "Environment : $(is_wsl && echo 'WSL2 Fedora' || echo 'Native Fedora')"
info "NVIDIA GPU  : $(has_nvidia && echo 'detected' || echo 'not detected')"
info "systemd     : $(has_systemd && echo 'available' || echo 'not available')"
[[ "${DRY_RUN:-0}" == "1" ]] && warn "DRY_RUN mode — no changes will be made to this system"
[[ "${CLEAN_INSTALL:-0}" == "1" ]] && warn "CLEAN_INSTALL mode — existing configs will be removed"

echo ""

for mod in \
    01-base 02-cli 03-cpp 04-kernel \
    05-python 06-js 07-claude 08-fonts \
    09-rust 10-gpu 11-editors 12-git 13-shell
do
    source "$SCRIPT_DIR/modules/${mod}.sh"
done

# =============================================================================
echo ""
echo -e "${BOLD}${GREEN}  All done! Reload your shell:${RESET}"
echo ""
echo -e "    ${YELLOW}source ~/.bashrc${RESET}"
echo ""
echo -e "${BOLD}  Quick reference:${RESET}"
echo -e "    ${BLUE}C++${RESET}      →  cmake, ninja, clangd, bear, ccache, mold"
echo -e "    ${BLUE}Python${RESET}   →  uv init / uv add / uv run / ruff / mypy"
echo -e "    ${BLUE}JS/TS${RESET}    →  bun init / bun add / bun run / tsx"
echo -e "    ${BLUE}Rust${RESET}     →  cargo new / cargo nextest / cargo watch"
if ! is_wsl; then
    echo -e "    ${BLUE}Kernel${RESET}   →  kernel-devel, qemu-kvm, bpftrace, aarch64 cross-gcc"
fi
echo -e "    ${BLUE}CUDA${RESET}     →  nvcc --version / nvidia-smi  (NVIDIA GPU only)"
echo -e "    ${BLUE}Vulkan${RESET}   →  vulkaninfo --summary / glslc (via shaderc)"
echo -e "    ${BLUE}FFmpeg${RESET}   →  ffmpeg -hwaccels"
echo -e "    ${BLUE}AI${RESET}       →  claude$(is_wsl || echo ' / windsurf / code')"
echo -e "    ${BLUE}Git TUI${RESET}  →  lazygit"
echo -e "    ${BLUE}Fonts${RESET}    →  JetBrainsMono / FiraCode / CascadiaCode Nerd Fonts"
echo -e "    ${BLUE}Prompt${RESET}   →  starship (configure: ~/.config/starship.toml)"
echo ""
if ! is_wsl; then
    echo -e "${YELLOW}  Note: Log out and back in for kvm/libvirt group changes to take effect.${RESET}"
    echo -e "${YELLOW}  Note: Reboot required after NVIDIA driver installation.${RESET}"
fi
