#!/usr/bin/env bash
# =============================================================================
# cleanup.sh — Remove all configurations added by fedora-setup
# Reverts shell configs, removes tool config files, and optionally uninstalls packages
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/colors.sh"

FEDORA_SETUP_SHELL_INIT="${HOME}/.config/fedora-setup/shell-init.sh"

# ── Dry run / confirmation ───────────────────────────────────────────────────

DRY_RUN=0
REMOVE_PACKAGES=0

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN=1; shift ;;
        --remove-packages) REMOVE_PACKAGES=1; shift ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Remove all configurations added by fedora-setup."
            echo ""
            echo "Options:"
            echo "  --dry-run          Show what would be removed without changing anything"
            echo "  --remove-packages  Also remove installed packages (dangerous)"
            echo "  --help, -h         Show this help"
            exit 0
            ;;
        *)
            warn "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [[ $DRY_RUN -eq 0 ]]; then
    echo -e "${BOLD}"
    echo "  This will remove ALL configurations added by fedora-setup."
    echo "  ${RED}This action cannot be undone.${RESET}"
    echo ""
    read -rp "Continue? [yes/NO]: " confirm
    if [[ "$confirm" != "yes" ]]; then
        info "Aborted"
        exit 0
    fi
fi

# ── Helper functions ───────────────────────────────────────────────────────────

remove_source_line() {
    local file="$1"
    local source_line="source \"$FEDORA_SETUP_SHELL_INIT\""

    if [[ ! -f "$file" ]]; then
        return 0
    fi

    if grep -qF "$source_line" "$file" 2>/dev/null; then
        if [[ $DRY_RUN -eq 1 ]]; then
            echo "DRY_RUN: Would remove source line from $file"
        else
            info "Removing source line from $file"
            sed -i "\|$source_line|d" "$file"
        fi
    fi
}

remove_file() {
    local file="$1"
    if [[ -f "$file" ]]; then
        if [[ $DRY_RUN -eq 1 ]]; then
            echo "DRY_RUN: Would remove $file"
        else
            info "Removing $file"
            rm -f "$file"
        fi
    fi
}

# ── Remove source line from shell configs ────────────────────────────────────

info "Removing source line from shell configs..."

SHELL_CONFIGS=(
    "$HOME/.bashrc"
    "$HOME/.zshrc"
    "$HOME/.bash_profile"
)

for cfg in "${SHELL_CONFIGS[@]}"; do
    remove_source_line "$cfg"
done

# ── Remove shell-init file ────────────────────────────────────────────────────

info "Removing shell-init file..."

remove_file "$FEDORA_SETUP_SHELL_INIT"

# Also remove the directory if it's empty
if [[ -d "$(dirname "$FEDORA_SETUP_SHELL_INIT")" ]]; then
    if [[ -z "$(ls -A "$(dirname "$FEDORA_SETUP_SHELL_INIT")")" ]]; then
        if [[ $DRY_RUN -eq 1 ]]; then
            echo "DRY_RUN: Would remove empty directory $(dirname "$FEDORA_SETUP_SHELL_INIT")"
        else
            rmdir "$(dirname "$FEDORA_SETUP_SHELL_INIT")" 2>/dev/null || true
        fi
    fi
fi

# ── Tool config files ────────────────────────────────────────────────────────

info "Removing tool configuration files..."

# Starship
remove_file "$HOME/.config/starship.toml"

# ccache
remove_file "$HOME/.ccache/ccache.conf"

# fzf (if installed to home)
remove_file "$HOME/.fzf"

# ── Package removal (optional) ───────────────────────────────────────────────

if [[ $REMOVE_PACKAGES -eq 1 ]]; then
    warn "--remove-packages is DANGEROUS and may break your system."
    if [[ $DRY_RUN -eq 0 ]]; then
        read -rp "Really remove packages? [yes/NO]: " pkg_confirm
        if [[ "$pkg_confirm" != "yes" ]]; then
            info "Skipping package removal"
        else
            info "Removing packages..."
            # Common packages installed by the setup script
            PACKAGES=(
                starship
                zoxide
                eza
                bat
                fzf
                ripgrep
                fd-find
                btop
                lazygit
                neovim
                uv
                bun
            )

            # Filter to only installed packages
            INSTALLED=()
            for pkg in "${PACKAGES[@]}"; do
                if rpm -q "$pkg" &>/dev/null; then
                    INSTALLED+=("$pkg")
                fi
            done

            if [[ ${#INSTALLED[@]} -gt 0 ]]; then
                if [[ $DRY_RUN -eq 1 ]]; then
                    echo "DRY_RUN: Would remove: ${INSTALLED[*]}"
                else
                    sudo dnf remove -y "${INSTALLED[@]}" || true
                fi
            fi
        fi
    fi
else
    if [[ $DRY_RUN -eq 0 ]]; then
        info "Package removal skipped (use --remove-packages to enable)"
    fi
fi

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
if [[ $DRY_RUN -eq 1 ]]; then
    success "Dry run complete. No changes were made."
    info "Run without --dry-run to actually remove configurations."
else
    success "Cleanup complete."
    info "Restart your shell or run 'exec bash' to apply changes."
fi