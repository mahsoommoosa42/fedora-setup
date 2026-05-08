#!/usr/bin/env bats
# Module-level dry-run tests.
# Each test runs a module via run_module.sh with DRY_RUN=1 and
# env-variable overrides, then inspects stdout for expected patterns.
#
# Run: bats tests/unit/test_modules.bats

load helpers

RUNNER="$UNIT_DIR/run_module.sh"

setup() {
    make_temp_home
    setup_mock_path          # stubs/dnf, stubs/sudo, etc. take precedence in PATH
    export DRY_RUN=1
    export HAS_NVIDIA=0
    export FEDORA_VER_STUB=41
}

teardown() {
    cleanup_temp_home
}

run_module() {
    local mod="$1"
    # Inherit all exported env vars; run_module.sh sources libs + the module.
    bash "$RUNNER" "$mod"
}

# ── 01-base ───────────────────────────────────────────────────────────────────

@test "01-base: exits 0 in DRY_RUN" {
    IS_WSL=0 run run_module "01-base"
    [ "$status" -eq 0 ]
}

@test "01-base: emits DRY_RUN dnf lines" {
    IS_WSL=0 run run_module "01-base"
    [[ "$output" == *"DRY_RUN: sudo dnf"* ]]
}

# ── 04-kernel ─────────────────────────────────────────────────────────────────

@test "04-kernel: skips entirely when IS_WSL=1" {
    IS_WSL=1 run run_module "04-kernel"
    [ "$status" -eq 0 ]
    [[ "$output" == *"WSL: skipping kernel module"* ]]
}

@test "04-kernel: kernel-devel NOT in output when IS_WSL=1" {
    IS_WSL=1 run run_module "04-kernel"
    ! echo "$output" | grep -q "dnf install.*kernel-devel"
}

@test "04-kernel: kernel-devel IS in output when IS_WSL=0" {
    IS_WSL=0 run run_module "04-kernel"
    echo "$output" | grep -q "dnf install.*kernel-devel"
}

@test "04-kernel: systemctl_enable IS in output when IS_WSL=0" {
    IS_WSL=0 run run_module "04-kernel"
    [[ "$output" == *"systemctl enable"* ]]
}

# ── 08-fonts ──────────────────────────────────────────────────────────────────

@test "08-fonts: skips kwriteconfig6 when IS_WSL=1" {
    IS_WSL=1 run run_module "08-fonts"
    [ "$status" -eq 0 ]
    [[ "$output" == *"WSL: skipping KDE"* ]]
    [[ "$output" != *"kwriteconfig6"* ]]
}

@test "08-fonts: exits 0 in native DRY_RUN" {
    IS_WSL=0 run run_module "08-fonts"
    [ "$status" -eq 0 ]
}

# ── 10-gpu ────────────────────────────────────────────────────────────────────

@test "10-gpu: akmod-nvidia NOT in output when IS_WSL=1 with NVIDIA" {
    IS_WSL=1 HAS_NVIDIA=1 run run_module "10-gpu"
    [ "$status" -eq 0 ]
    [[ "$output" == *"WSL: skipping akmod"* ]]
    ! echo "$output" | grep -q "dnf install.*akmod-nvidia"
}

@test "10-gpu: wsl/lib in output when IS_WSL=1 with NVIDIA" {
    IS_WSL=1 HAS_NVIDIA=1 run run_module "10-gpu"
    [[ "$output" == *"wsl/lib"* ]]
}

@test "10-gpu: akmod-nvidia IS in output when IS_WSL=0 with NVIDIA" {
    IS_WSL=0 HAS_NVIDIA=1 run run_module "10-gpu"
    echo "$output" | grep -q "dnf install.*akmod-nvidia"
}

@test "10-gpu: wsl/lib NOT in output when IS_WSL=0" {
    IS_WSL=0 HAS_NVIDIA=1 run run_module "10-gpu"
    [[ "$output" != *"wsl/lib"* ]]
}

# ── 11-editors ────────────────────────────────────────────────────────────────

@test "11-editors: skips VS Code and Windsurf when IS_WSL=1" {
    IS_WSL=1 run run_module "11-editors"
    [ "$status" -eq 0 ]
    [[ "$output" == *"WSL: skipping VS Code"* ]]
    [[ "$output" != *"vscode.repo"* ]]
    [[ "$output" != *"windsurf.repo"* ]]
}

@test "11-editors: includes vscode.repo when IS_WSL=0" {
    IS_WSL=0 run run_module "11-editors"
    [[ "$output" == *"vscode.repo"* ]]
}

# ── 13-shell ──────────────────────────────────────────────────────────────────

@test "13-shell: writes zoxide, fzf, eza, bat markers to BASHRC" {
    IS_WSL=0 run run_module "13-shell"
    [ "$status" -eq 0 ]
    grep -q "zoxide" "$BASHRC"
    grep -q "fzf" "$BASHRC"
    grep -q "eza" "$BASHRC"
    grep -q "bat" "$BASHRC"
}

@test "13-shell: is idempotent (markers written only once)" {
    IS_WSL=0 run run_module "13-shell"
    IS_WSL=0 run run_module "13-shell"
    [ "$(grep -c 'zoxide init' "$BASHRC")" -eq 1 ]
}
