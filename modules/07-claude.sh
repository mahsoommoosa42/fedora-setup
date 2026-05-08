#!/usr/bin/env bash
section "7 · Claude Code"

if command_exists claude; then
    info "Claude Code already installed, updating..."
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        echo "DRY_RUN: claude update"
    else
        claude update 2>/dev/null || true
    fi
else
    info "Installing Claude Code..."
    run_installer "https://claude.ai/install.sh"
fi

success "Claude Code installed — run: claude"
warn "Authenticate with your Anthropic account on first run"
