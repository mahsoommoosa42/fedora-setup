#!/usr/bin/env bash
# Helper script: sources a module inside a clean bash subprocess.
# Environment variables (DRY_RUN, IS_WSL, HAS_NVIDIA, HOME, BASHRC, …) are
# inherited from the caller, so tests can export them before invoking this.
#
# Usage:
#   DRY_RUN=1 IS_WSL=1 bash run_module.sh 04-kernel

set -euo pipefail

SCRIPT="$1"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# shellcheck source=/dev/null
source "$REPO_ROOT/lib/colors.sh"
source "$REPO_ROOT/lib/detect.sh"
source "$REPO_ROOT/lib/utils.sh"
source "$REPO_ROOT/modules/${SCRIPT}.sh"
