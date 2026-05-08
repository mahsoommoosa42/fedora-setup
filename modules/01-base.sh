#!/usr/bin/env bash
section "1 · System Update & Base Tools"

info "Updating system packages..."
dnf_upgrade

info "Installing essential base tools..."
# fd (not fd-find) is the correct Fedora package name
dnf_install \
    curl wget git git-delta \
    htop btop \
    ripgrep fd fzf jq \
    bat eza zoxide \
    man-pages bash-completion \
    tmux stow

success "Base tools installed"
