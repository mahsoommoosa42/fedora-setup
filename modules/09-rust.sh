#!/usr/bin/env bash
section "9 · Rust via rustup"

if command_exists rustup; then
    info "rustup already installed, updating..."
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        echo "DRY_RUN: rustup update"
    else
        rustup update
    fi
else
    info "Installing Rust via rustup..."
    run_installer "https://sh.rustup.rs" -y \
        --default-toolchain stable \
        --profile default \
        --component rust-analyzer rust-src clippy rustfmt
fi

clean_config "rustup PATH"

append_if_missing "rustup PATH" \
'. "$HOME/.cargo/env"'

if [[ "${DRY_RUN:-0}" != "1" ]]; then
    # shellcheck source=/dev/null
    source "$HOME/.cargo/env" 2>/dev/null || true
fi

info "Adding Rust targets..."
if [[ "${DRY_RUN:-0}" == "1" ]]; then
    echo "DRY_RUN: rustup target add aarch64-unknown-linux-gnu thumbv7em-none-eabihf"
else
    rustup target add aarch64-unknown-linux-gnu
    rustup target add thumbv7em-none-eabihf
fi

info "Installing cargo tools..."
for crate in \
    cargo-watch \
    cargo-expand \
    cargo-nextest \
    cargo-audit \
    cargo-bloat \
    cargo-flamegraph
do
    cargo_install "$crate"
done

info "Installing extra CLI tools via cargo (not in Fedora repos)..."
for crate in bandwhich hexyl du-dust sd; do
    cargo_install "$crate"
done

success "Rust ready"
