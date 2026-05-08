#!/usr/bin/env bash
# Shared utilities. Every side-effecting call goes through a wrapper so
# DRY_RUN=1 can be used for safe testing without touching the real system.

BASHRC="${BASHRC:-$HOME/.bashrc}"
FEDORA_SETUP_SHELL_INIT="${FEDORA_SETUP_SHELL_INIT:-$HOME/.config/fedora-setup/shell-init.sh}"

command_exists() { command -v "$1" &>/dev/null; }

dnf_install() {
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        echo "DRY_RUN: sudo dnf install -y $*"; return 0
    fi
    sudo dnf install -y "$@"
}

dnf_upgrade() {
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        echo "DRY_RUN: sudo dnf upgrade -y --refresh"; return 0
    fi
    sudo dnf upgrade -y --refresh
}

dnf_copr_enable() {
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        echo "DRY_RUN: sudo dnf copr enable -y $*"; return 0
    fi
    sudo dnf copr enable -y "$@"
}

dnf_remove() {
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        echo "DRY_RUN: sudo dnf remove -y $*"; return 0
    fi
    sudo dnf remove -y "$@" 2>/dev/null || true
}

dnf_group_update() {
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        echo "DRY_RUN: sudo dnf groupupdate -y $*"; return 0
    fi
    sudo dnf groupupdate -y "$@"
}

dnf_config_manager() {
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        echo "DRY_RUN: sudo dnf config-manager $*"; return 0
    fi
    sudo dnf config-manager "$@"
}

systemctl_enable() {
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        echo "DRY_RUN: sudo systemctl enable --now $*"; return 0
    fi
    sudo systemctl enable --now "$@" \
        || warn "systemctl failed — run 'sudo systemctl enable --now $*' after first boot"
}

cargo_install() {
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        echo "DRY_RUN: cargo install --locked $*"; return 0
    fi
    cargo install --locked "$@" || warn "Failed to install $* — skipping"
}

run_installer() {
    local url="$1"; shift
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        echo "DRY_RUN: curl -fsSL $url | bash -s -- $*"; return 0
    fi
    curl -fsSL "$url" | bash -s -- "$@"
}

rpm_import() {
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        echo "DRY_RUN: sudo rpm --import $*"; return 0
    fi
    sudo rpm --import "$@"
}

sudo_tee_repo() {
    local dest="$1" content="$2"
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        echo "DRY_RUN: sudo tee $dest"; return 0
    fi
    printf '%s\n' "$content" | sudo tee "$dest" > /dev/null
}

usermod_groups() {
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        echo "DRY_RUN: sudo usermod -aG $*"; return 0
    fi
    sudo usermod -aG "$@"
}

append_if_missing() {
    local marker="$1" content="$2" file="${3:-$BASHRC}"
    if ! grep -qF "$marker" "$file" 2>/dev/null; then
        echo "" >> "$file"
        printf '%s\n' "$content" >> "$file"
        success "Added to $file: $marker"
    else
        info "Already in $file: $marker (skipping)"
    fi
}

# ── Shell init file management ────────────────────────────────────────────────

# Ensure the shell-init file exists and is sourced from the user's shell config
ensure_shell_init() {
    local shell_config="$1"

    # Create the init file directory
    mkdir -p "$(dirname "$FEDORA_SETUP_SHELL_INIT")"

    # Create the init file if it doesn't exist
    if [[ ! -f "$FEDORA_SETUP_SHELL_INIT" ]]; then
        cat > "$FEDORA_SETUP_SHELL_INIT" <<'EOF'
# =============================================================================
# Shell initialization for fedora-setup
# This file is sourced by ~/.bashrc, ~/.zshrc, and ~/.bash_profile
# All tool-specific configurations (PATH, aliases, init functions) go here
# =============================================================================
EOF
    fi

    # Add source line to shell config if not present
    local source_line="source \"$FEDORA_SETUP_SHELL_INIT\""
    if ! grep -qF "$source_line" "$shell_config" 2>/dev/null; then
        echo "" >> "$shell_config"
        printf '%s\n' "$source_line" >> "$shell_config"
        success "Added source line to $shell_config"
    fi
}

# Append content to the shell-init file with a marker
append_to_shell_init() {
    local marker="$1" content="$2"

    if ! grep -qF "$marker" "$FEDORA_SETUP_SHELL_INIT" 2>/dev/null; then
        echo "" >> "$FEDORA_SETUP_SHELL_INIT"
        printf '%s\n' "$content" >> "$FEDORA_SETUP_SHELL_INIT"
        success "Added to shell-init: $marker"
    else
        info "Already in shell-init: $marker (skipping)"
    fi
}

# Remove marker from shell-init file (for CLEAN_INSTALL)
clean_shell_init() {
    local marker="$1"
    if [[ "${CLEAN_INSTALL:-0}" == "1" ]]; then
        if grep -qF "$marker" "$FEDORA_SETUP_SHELL_INIT" 2>/dev/null; then
            info "CLEAN_INSTALL: Removing $marker from shell-init"
            sed -i "/$marker/d" "$FEDORA_SETUP_SHELL_INIT"
        fi
    fi
}

# ── Legacy functions (for backward compatibility) ────────────────────────────

clean_config() {
    local marker="$1" file="${2:-$BASHRC}"
    if [[ "${CLEAN_INSTALL:-0}" == "1" ]]; then
        if grep -qF "$marker" "$file" 2>/dev/null; then
            info "CLEAN_INSTALL: Removing $marker from $file"
            # Remove lines containing the marker
            sed -i "/$marker/d" "$file"
        fi
    fi
}

remove_file() {
    local file="$1"
    if [[ "${CLEAN_INSTALL:-0}" == "1" ]]; then
        if [[ -f "$file" ]]; then
            info "CLEAN_INSTALL: Removing $file"
            rm -f "$file"
        fi
    fi
}
