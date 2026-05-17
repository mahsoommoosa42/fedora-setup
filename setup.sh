#!/usr/bin/env bash
# =============================================================================
# setup.sh — Thin shell wrapper for fedora-setup.
#
# All logic lives in the Python package ``fedora_setup``. This script just
# checks the basic preconditions (python3 available, not running as root)
# and execs ``python3 -m fedora_setup``.
#
# Usage:
#   ./setup.sh                     # real install
#   DRY_RUN=1 ./setup.sh           # safe preview (no changes made)
#   CLEAN_INSTALL=1 ./setup.sh     # remove existing configs before install
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install with: sudo dnf install python3" >&2
    exit 1
fi

if [[ "$(id -u)" -eq 0 ]]; then
    echo "ERROR: Do not run as root. sudo will be invoked when needed." >&2
    exit 1
fi

export FEDORA_SETUP_DIR="$SCRIPT_DIR"
exec python3 -m fedora_setup "$@"
