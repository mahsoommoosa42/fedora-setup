#!/usr/bin/env bash
section "6 · JavaScript via Bun"

if command_exists bun; then
    info "Bun already installed, updating..."
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        echo "DRY_RUN: bun upgrade"
    else
        bun upgrade
    fi
else
    info "Installing Bun..."
    run_installer "https://bun.sh/install"
fi

clean_config "bun PATH"

append_if_missing "bun PATH" \
'# Bun — JavaScript runtime & package manager
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"
[ -s "$HOME/.bun/_bun" ] && source "$HOME/.bun/_bun"'

export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"

info "Installing global JS/TS tools..."
if [[ "${DRY_RUN:-0}" == "1" ]]; then
    echo "DRY_RUN: bun install -g typescript tsx eslint prettier @antfu/ni"
else
    bun install -g typescript tsx eslint prettier @antfu/ni
fi

success "Bun ready — use: bun init, bun add, bun run, bun test"
