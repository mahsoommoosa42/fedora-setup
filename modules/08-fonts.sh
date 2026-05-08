#!/usr/bin/env bash
section "8 · Nerd Fonts"

FONTS_DIR="$HOME/.local/share/fonts"
mkdir -p "$FONTS_DIR"

NF_BASE="https://github.com/ryanoasis/nerd-fonts/releases/latest/download"

install_nerd_font() {
    local font_name="$1"
    local archive="${font_name}.tar.xz"
    local target_dir="$FONTS_DIR/$font_name"

    if ls "$FONTS_DIR"/*"${font_name}"* &>/dev/null 2>&1; then
        info "Font $font_name already installed, skipping"
        return
    fi

    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        echo "DRY_RUN: install Nerd Font $font_name"
        return
    fi

    info "Downloading $font_name Nerd Font..."
    local tmp
    tmp=$(mktemp -d)
    curl -fsSL "$NF_BASE/$archive" -o "$tmp/$archive"
    mkdir -p "$target_dir"
    tar -xf "$tmp/$archive" -C "$target_dir" --wildcards "*.ttf" 2>/dev/null || true
    rm -rf "$tmp"
    success "$font_name Nerd Font installed"
}

install_nerd_font "JetBrainsMono"
install_nerd_font "FiraCode"
install_nerd_font "CascadiaCode"
install_nerd_font "Meslo"

if [[ "${DRY_RUN:-0}" == "1" ]]; then
    echo "DRY_RUN: fc-cache -f $FONTS_DIR"
else
    info "Refreshing font cache..."
    fc-cache -f "$FONTS_DIR"
fi

# KDE Plasma configuration — skip on WSL (no display server)
if is_wsl; then
    info "WSL: skipping KDE font and Konsole profile configuration"
else
    if command_exists kwriteconfig6; then
        kwriteconfig6 --file kdeglobals \
            --group General \
            --key fixed \
            "JetBrainsMono Nerd Font Mono,11,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
        qdbus6 org.kde.KGlobalSettings /KGlobalSettings notifyChange 4 0 2>/dev/null || true
        success "KDE monospace font set to JetBrainsMono Nerd Font Mono 11pt"
    else
        warn "kwriteconfig6 not found — set font manually in System Settings → Fonts → Fixed width"
    fi

    KONSOLE_DIR="$HOME/.local/share/konsole"
    mkdir -p "$KONSOLE_DIR"
    if [[ ! -f "$KONSOLE_DIR/Dev.profile" ]]; then
        cat > "$KONSOLE_DIR/Dev.profile" <<'KONSOLE_PROFILE'
[Appearance]
ColorScheme=Dracula
Font=JetBrainsMono Nerd Font Mono,12,-1,5,400,0,0,0,0,0,0,0,0,0,0,1

[General]
Name=Dev
Parent=FALLBACK/
TerminalCenter=true
TerminalMargin=6

[Scrolling]
ScrollBarPosition=2
KONSOLE_PROFILE
        success "Konsole 'Dev' profile created"
    fi
fi
