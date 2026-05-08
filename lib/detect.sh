#!/usr/bin/env bash
# Environment detection helpers.
# All functions respect override env vars so tests can mock without touching real system files.

is_wsl() {
    # Allow tests/containers to force a value
    if [[ -n "${IS_WSL:-}" ]]; then
        [[ "$IS_WSL" == "1" || "$IS_WSL" == "true" ]]
        return
    fi
    [[ -n "${WSL_DISTRO_NAME:-}" ]] && return 0
    grep -qi microsoft "${PROC_VERSION_OVERRIDE:-/proc/version}" 2>/dev/null
}

has_nvidia() {
    if [[ -n "${HAS_NVIDIA:-}" ]]; then
        [[ "$HAS_NVIDIA" == "1" || "$HAS_NVIDIA" == "true" ]]
        return
    fi
    lspci 2>/dev/null | grep -qi nvidia
}

has_systemd() {
    [[ -d "${SYSTEMD_DIR_OVERRIDE:-/run/systemd/system}" ]]
}

is_interactive() { [[ -t 0 ]]; }
