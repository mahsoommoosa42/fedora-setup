#!/usr/bin/env bash
section "2 · Extra CLI Tooling"

info "Installing dnf-plugins-core..."
dnf_install dnf-plugins-core

info "Installing modern CLI tools from standard repos..."
dnf_install \
    gh direnv tokei hyperfine bottom just mold

info "Enabling lazygit COPR and installing..."
dnf_copr_enable atim/lazygit
dnf_install lazygit

info "Note: bandwhich, hexyl, dust, sd will be installed via cargo in Section 9"

info "Installing starship prompt..."
run_installer "https://starship.rs/install.sh" -y

append_if_missing "starship init" \
'# Starship — cross-shell prompt
eval "$(starship init bash)"'

success "Extra tooling installed"
