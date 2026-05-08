#!/usr/bin/env bash
# Shared utilities. Every side-effecting call goes through a wrapper so
# DRY_RUN=1 can be used for safe testing without touching the real system.

BASHRC="${BASHRC:-$HOME/.bashrc}"

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
