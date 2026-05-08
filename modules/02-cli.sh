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

# Clean existing starship config if CLEAN_INSTALL is set
STARSHIP_CONFIG="$HOME/.config/starship.toml"
remove_file "$STARSHIP_CONFIG"
clean_config "starship init"

# Create default starship config with nerd-font preset if not already present
if [[ ! -f "$STARSHIP_CONFIG" ]]; then
    info "Creating default starship config with nerd-font preset..."
    mkdir -p "$(dirname "$STARSHIP_CONFIG")"
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        echo "DRY_RUN: starship preset nerd-font > $STARSHIP_CONFIG"
    else
        starship preset nerd-font > "$STARSHIP_CONFIG"
    fi
else
    info "Starship config already exists at $STARSHIP_CONFIG (skipping preset)"
fi

append_if_missing "starship init" \
'# Starship — cross-shell prompt
eval "$(starship init bash)"'

success "Extra tooling installed"
