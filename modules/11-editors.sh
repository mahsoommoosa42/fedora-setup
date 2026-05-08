#!/usr/bin/env bash
section "11 · Editors & LSP Support"

info "Installing Neovim..."
# nodejs is needed by some nvim LSP plugins
dnf_install neovim nodejs

info "Installing clangd LSP..."
dnf_install clang-tools-extra

info "Installing pyright via uv..."
if [[ "${DRY_RUN:-0}" == "1" ]]; then
    echo "DRY_RUN: uv tool install pyright"
else
    uv tool install pyright
fi

success "clangd and pyright installed"

# VS Code and Windsurf are GUI apps — skip in WSL (use Remote-WSL from Windows instead)
if is_wsl; then
    info "WSL: skipping VS Code and Windsurf RPM installation"
    info "  → Install VS Code for Windows and use the Remote-WSL extension"
    info "  → Or run: curl -fsSL https://code-server.dev/install.sh | sh"
    return 0 2>/dev/null || exit 0
fi

# ── VS Code ───────────────────────────────────────────────────────────────────
info "Adding VS Code repository..."
rpm_import "https://packages.microsoft.com/keys/microsoft.asc"
sudo_tee_repo "/etc/yum.repos.d/vscode.repo" \
"[code]
name=Visual Studio Code
baseurl=https://packages.microsoft.com/yumrepos/vscode
enabled=1
gpgcheck=1
gpgkey=https://packages.microsoft.com/keys/microsoft.asc"

dnf_install code
success "VS Code installed — launch with: code"

# ── Windsurf ──────────────────────────────────────────────────────────────────
info "Adding Windsurf repository..."
rpm_import "https://windsurf-stable.codeiumdata.com/wVxpZuBSvCwhYjtp/windsurf.gpg"
sudo_tee_repo "/etc/yum.repos.d/windsurf.repo" \
"[windsurf]
name=Windsurf Editor
baseurl=https://windsurf-stable.codeiumdata.com/wVxpZuBSvCwhYjtp/rpm/stable/x86_64
enabled=1
gpgcheck=1
gpgkey=https://windsurf-stable.codeiumdata.com/wVxpZuBSvCwhYjtp/windsurf.gpg"

dnf_install windsurf
success "Windsurf installed — launch with: windsurf"
