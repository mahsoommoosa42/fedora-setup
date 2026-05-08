#!/usr/bin/env bats
# Unit tests for lib/utils.sh
# Run: bats tests/unit/test_utils.bats

load helpers

LIBS="$REPO_ROOT/lib/colors.sh $REPO_ROOT/lib/detect.sh $REPO_ROOT/lib/utils.sh"
SOURCE_LIBS="source $REPO_ROOT/lib/colors.sh; source $REPO_ROOT/lib/detect.sh; source $REPO_ROOT/lib/utils.sh"

setup() {
    make_temp_home
}

teardown() {
    cleanup_temp_home
}

# ── command_exists ────────────────────────────────────────────────────────────

@test "command_exists: finds bash" {
    run bash -c "$SOURCE_LIBS; command_exists bash && echo found || echo missing"
    [ "$output" = "found" ]
}

@test "command_exists: returns missing for nonexistent command" {
    run bash -c "$SOURCE_LIBS; command_exists __no_such_cmd_xyz__ && echo found || echo missing"
    [ "$output" = "missing" ]
}

# ── append_if_missing ─────────────────────────────────────────────────────────

@test "append_if_missing: adds content when marker is absent" {
    local rc="$HOME/.bashrc"
    run bash -c "
        $SOURCE_LIBS
        BASHRC='$rc'
        append_if_missing '# zoxide-marker' '# zoxide-marker
eval \"\$(zoxide init bash)\"'
        grep -c 'zoxide-marker' '$rc'
    "
    [ "$status" -eq 0 ]
    # Get the last line of output (the grep count)
    local count=$(echo "$output" | tail -n1)
    [ "$count" = "1" ]
}

@test "append_if_missing: is idempotent on second call" {
    local rc="$HOME/.bashrc"
    run bash -c "
        $SOURCE_LIBS
        BASHRC='$rc'
        append_if_missing '# test-idem' '# test-idem
export X=1'
        append_if_missing '# test-idem' '# test-idem
export X=1'
        grep -c 'test-idem' '$rc'
    "
    [ "$status" -eq 0 ]
    local count=$(echo "$output" | tail -n1)
    [ "$count" = "1" ]
}

@test "append_if_missing: writes to custom file path" {
    local custom="$HOME/custom_rc"
    touch "$custom"
    run bash -c "
        $SOURCE_LIBS
        append_if_missing '# custom-marker' '# custom-marker' '$custom'
        grep -c 'custom-marker' '$custom'
    "
    [ "$status" -eq 0 ]
    local count=$(echo "$output" | tail -n1)
    [ "$count" = "1" ]
}

# ── DRY_RUN wrappers ──────────────────────────────────────────────────────────

@test "dnf_install: DRY_RUN=1 echoes without calling sudo" {
    run bash -c "$SOURCE_LIBS; DRY_RUN=1 dnf_install curl wget git"
    [ "$status" -eq 0 ]
    [[ "$output" == *"DRY_RUN: sudo dnf install -y"* ]]
    [[ "$output" == *"curl"* ]]
}

@test "dnf_upgrade: DRY_RUN=1 echoes" {
    run bash -c "$SOURCE_LIBS; DRY_RUN=1 dnf_upgrade"
    [ "$status" -eq 0 ]
    [[ "$output" == *"DRY_RUN: sudo dnf upgrade"* ]]
}

@test "systemctl_enable: DRY_RUN=1 echoes and returns 0" {
    run bash -c "$SOURCE_LIBS; DRY_RUN=1 systemctl_enable libvirtd"
    [ "$status" -eq 0 ]
    [[ "$output" == *"DRY_RUN: sudo systemctl enable"* ]]
    [[ "$output" == *"libvirtd"* ]]
}

@test "cargo_install: DRY_RUN=1 echoes and returns 0" {
    run bash -c "$SOURCE_LIBS; DRY_RUN=1 cargo_install cargo-watch"
    [ "$status" -eq 0 ]
    [[ "$output" == *"DRY_RUN: cargo install --locked cargo-watch"* ]]
}

@test "run_installer: DRY_RUN=1 echoes URL without running curl" {
    run bash -c "$SOURCE_LIBS; DRY_RUN=1 run_installer 'https://example.com/install.sh' -y"
    [ "$status" -eq 0 ]
    [[ "$output" == *"DRY_RUN"* ]]
    [[ "$output" == *"example.com"* ]]
}

@test "usermod_groups: DRY_RUN=1 echoes" {
    run bash -c "$SOURCE_LIBS; DRY_RUN=1 usermod_groups kvm,libvirt testuser"
    [ "$status" -eq 0 ]
    [[ "$output" == *"DRY_RUN: sudo usermod -aG"* ]]
}
