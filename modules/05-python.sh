#!/usr/bin/env bash
section "5 · Python via uv"

if command_exists uv; then
    info "uv already installed, updating..."
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        echo "DRY_RUN: uv self update"
    else
        uv self update
    fi
else
    info "Installing uv..."
    run_installer "https://astral.sh/uv/install.sh"
fi

append_if_missing "uv PATH" \
'# uv — Python package manager
export PATH="$HOME/.local/bin:$PATH"'

export PATH="$HOME/.local/bin:$PATH"

info "Installing Python 3.13 via uv..."
if [[ "${DRY_RUN:-0}" == "1" ]]; then
    echo "DRY_RUN: uv python install 3.13"
else
    uv python install 3.13
fi

info "Installing global Python tools..."
for tool in ruff mypy ipython pytest httpie; do
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        echo "DRY_RUN: uv tool install $tool"
    else
        uv tool install "$tool"
    fi
done

append_if_missing "uv tool PATH" \
'# uv tool binaries
export PATH="$HOME/.local/share/uv/tools/bin:$PATH"
eval "$(uv generate-shell-completion bash 2>/dev/null || true)"'

success "Python ready — manage projects with: uv init, uv add, uv run"
