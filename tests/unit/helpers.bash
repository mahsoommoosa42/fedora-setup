#!/usr/bin/env bash
# Shared helpers loaded by every bats test file via: load helpers

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UNIT_DIR="$REPO_ROOT/tests/unit"
STUBS_DIR="$REPO_ROOT/tests/stubs"

# Prepend stub executables to PATH so dnf/sudo/systemctl etc. are intercepted.
setup_mock_path() {
    export PATH="$STUBS_DIR:$PATH"
}

# Redirect HOME to a temp dir so .bashrc writes are isolated from the real system.
make_temp_home() {
    export HOME
    HOME="$(mktemp -d)"
    export BASHRC="$HOME/.bashrc"
    touch "$BASHRC"
}

cleanup_temp_home() {
    [[ -n "${HOME:-}" && "$HOME" == /tmp/* ]] && rm -rf "$HOME"
}

# Force WSL detection to return true.
mock_wsl() {
    export WSL_DISTRO_NAME="fedora"
    export IS_WSL="1"
    unset PROC_VERSION_OVERRIDE
}

# Force WSL detection to return false.
mock_native() {
    unset WSL_DISTRO_NAME 2>/dev/null || true
    export IS_WSL="0"
    unset PROC_VERSION_OVERRIDE
}

# Force lspci to report an NVIDIA card.
mock_nvidia() {
    export HAS_NVIDIA="1"
    export LSPCI_STUB_OUTPUT="NVIDIA Corporation GP104 [GeForce GTX 1080]"
}

mock_no_nvidia() {
    export HAS_NVIDIA="0"
    export LSPCI_STUB_OUTPUT="Intel Corporation HD Graphics 620"
}

# Create/remove a temp dir to fake the systemd socket path.
mock_systemd() {
    export SYSTEMD_DIR_OVERRIDE
    SYSTEMD_DIR_OVERRIDE="$(mktemp -d)"
}

mock_no_systemd() {
    export SYSTEMD_DIR_OVERRIDE="/nonexistent/systemd/path"
}

cleanup_systemd_mock() {
    [[ -n "${SYSTEMD_DIR_OVERRIDE:-}" && "$SYSTEMD_DIR_OVERRIDE" == /tmp/* ]] \
        && rmdir "$SYSTEMD_DIR_OVERRIDE" 2>/dev/null || true
    unset SYSTEMD_DIR_OVERRIDE
}

# Source all three lib files into the current shell.
source_libs() {
    # shellcheck source=/dev/null
    source "$REPO_ROOT/lib/colors.sh"
    source "$REPO_ROOT/lib/detect.sh"
    source "$REPO_ROOT/lib/utils.sh"
}
