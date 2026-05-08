#!/usr/bin/env bash
section "12 · Git Config"

info "Configuring git defaults..."
if [[ "${DRY_RUN:-0}" == "1" ]]; then
    echo "DRY_RUN: git config --global (core.pager=delta, merge, diff, pull, init, rerere, fetch)"
else
    git config --global core.pager         "delta"
    git config --global delta.navigate     true
    git config --global delta.line-numbers true
    git config --global delta.syntax-theme "Dracula"
    git config --global merge.conflictstyle diff3
    git config --global diff.colorMoved    default
    git config --global pull.rebase        true
    git config --global init.defaultBranch main
    git config --global rerere.enabled     true
    git config --global fetch.prune        true
fi

if [[ -z "$(git config --global user.name 2>/dev/null)" ]]; then
    if is_interactive; then
        echo ""
        read -rp "  Git user.name:  " git_name
        read -rp "  Git user.email: " git_email
        if [[ "${DRY_RUN:-0}" != "1" ]]; then
            git config --global user.name  "$git_name"
            git config --global user.email "$git_email"
        fi
        success "Git identity configured"
    else
        warn "No TTY — skipping git identity prompt. Run after first boot:"
        warn "  git config --global user.name  'Your Name'"
        warn "  git config --global user.email 'you@example.com'"
    fi
else
    info "Git identity already set: $(git config --global user.name)"
fi

success "Git configured with delta as pager"
