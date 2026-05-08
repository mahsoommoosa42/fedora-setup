#!/usr/bin/env bats
# Unit tests for lib/detect.sh
# Run: bats tests/unit/test_detect.bats

load helpers

DETECT="$REPO_ROOT/lib/detect.sh"

# ── is_wsl ────────────────────────────────────────────────────────────────────

@test "is_wsl: returns true when IS_WSL=1" {
    run bash -c "source '$DETECT'; IS_WSL=1; is_wsl && echo yes || echo no"
    [ "$status" -eq 0 ]
    [ "$output" = "yes" ]
}

@test "is_wsl: returns true when IS_WSL=true" {
    run bash -c "source '$DETECT'; IS_WSL=true; is_wsl && echo yes || echo no"
    [ "$status" -eq 0 ]
    [ "$output" = "yes" ]
}

@test "is_wsl: returns false when IS_WSL=0" {
    run bash -c "source '$DETECT'; IS_WSL=0; unset WSL_DISTRO_NAME; is_wsl && echo yes || echo no"
    [ "$status" -eq 0 ]
    [ "$output" = "no" ]
}

@test "is_wsl: returns true when WSL_DISTRO_NAME is set (no IS_WSL override)" {
    run bash -c "source '$DETECT'; unset IS_WSL; WSL_DISTRO_NAME=fedora; is_wsl && echo yes || echo no"
    [ "$status" -eq 0 ]
    [ "$output" = "yes" ]
}

@test "is_wsl: returns false when neither IS_WSL nor WSL_DISTRO_NAME set, and /proc/version is normal" {
    local tmpfile
    tmpfile="$(mktemp)"
    echo "Linux version 6.8.0-59-generic (gcc version 13)" > "$tmpfile"
    run bash -c "
        source '$DETECT'
        unset IS_WSL WSL_DISTRO_NAME
        PROC_VERSION_OVERRIDE='$tmpfile'
        is_wsl && echo yes || echo no
    "
    rm -f "$tmpfile"
    [ "$output" = "no" ]
}

@test "is_wsl: returns true via PROC_VERSION_OVERRIDE containing 'microsoft'" {
    local tmpfile
    tmpfile="$(mktemp)"
    echo "Linux version 5.15.167.4-microsoft-standard-WSL2" > "$tmpfile"
    run bash -c "
        source '$DETECT'
        unset IS_WSL WSL_DISTRO_NAME
        PROC_VERSION_OVERRIDE='$tmpfile'
        is_wsl && echo yes || echo no
    "
    rm -f "$tmpfile"
    [ "$output" = "yes" ]
}

# ── has_nvidia ────────────────────────────────────────────────────────────────

@test "has_nvidia: returns true when HAS_NVIDIA=1" {
    run bash -c "source '$DETECT'; HAS_NVIDIA=1; has_nvidia && echo yes || echo no"
    [ "$output" = "yes" ]
}

@test "has_nvidia: returns false when HAS_NVIDIA=0" {
    run bash -c "source '$DETECT'; HAS_NVIDIA=0; has_nvidia && echo yes || echo no"
    [ "$output" = "no" ]
}

@test "has_nvidia: returns true when HAS_NVIDIA=true" {
    run bash -c "source '$DETECT'; HAS_NVIDIA=true; has_nvidia && echo yes || echo no"
    [ "$output" = "yes" ]
}

# ── has_systemd ───────────────────────────────────────────────────────────────

@test "has_systemd: returns true when SYSTEMD_DIR_OVERRIDE points to an existing dir" {
    local tmpdir
    tmpdir="$(mktemp -d)"
    run bash -c "source '$DETECT'; SYSTEMD_DIR_OVERRIDE='$tmpdir'; has_systemd && echo yes || echo no"
    rmdir "$tmpdir"
    [ "$output" = "yes" ]
}

@test "has_systemd: returns false when SYSTEMD_DIR_OVERRIDE points to nonexistent path" {
    run bash -c "source '$DETECT'; SYSTEMD_DIR_OVERRIDE='/nonexistent/path/xyz'; has_systemd && echo yes || echo no"
    [ "$output" = "no" ]
}
