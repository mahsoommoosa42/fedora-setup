#!/usr/bin/env bash
# =============================================================================
# download-iso.sh — Thin shell wrapper around
# ``python3 -m fedora_setup.kickstart.download_iso``.
#
# All logic now lives in the Python module. See ``--help`` for options.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install with: sudo dnf install python3" >&2
    exit 1
fi

export FEDORA_SETUP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
exec python3 -m fedora_setup.kickstart.download_iso "$@"

BASE_URL="https://dl.fedoraproject.org/pub/fedora/linux/releases/"
DOWNLOAD_DIR="${DOWNLOAD_DIR:-$HOME/Downloads/Fedora-ISOs}"

# ── CLI ────────────────────────────────────────────────────────────────────────

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Interactively browse the Fedora mirror and download an ISO.

Options:
  --base-url URL   Mirror root to browse  (default: $BASE_URL)
  --dest DIR       Download destination   (default: \$HOME/Downloads/Fedora-ISOs)
  -h, --help       Show this help
EOF
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --base-url)   BASE_URL="$2";    shift 2 ;;
        --dest)       DOWNLOAD_DIR="$2"; shift 2 ;;
        --help|-h)    usage; exit 0 ;;
        *) warn "Unknown option: $1"; usage; exit 1 ;;
    esac
done

# ── Mirror listing helpers ─────────────────────────────────────────────────────

_fetch() {
    if command -v curl &>/dev/null; then
        curl -sL --max-time 15 "$1"
    else
        wget -qO- --timeout=15 "$1"
    fi
}

# Parse an Apache/Nginx directory listing: return plain filenames / dir/ entries.
# Filters out sort-query links (?C=…), the parent-dir link, and absolute paths.
list_entries() {
    local url="$1"
    _fetch "$url" \
        | grep -oP 'href="[^"]*"' \
        | sed 's/href="//;s/"//' \
        | grep -v '^[/?]' \
        | grep -v '^\.\.'
}

# ── Download + verify ──────────────────────────────────────────────────────────

# Find the CHECKSUM file sitting next to the ISO in the same directory.
find_checksum_url() {
    local dir_url="$1"
    list_entries "$dir_url" | grep -i 'CHECKSUM' | head -1 | \
        awk -v base="$dir_url" '{print base $1}'
}

verify_iso() {
    local iso_file="$1" checksum_url="$2"

    if ! command -v sha256sum &>/dev/null; then
        warn "sha256sum not found — skipping verification"
        return 0
    fi

    if [[ -z "$checksum_url" ]]; then
        warn "No CHECKSUM file found in this directory — skipping verification"
        return 0
    fi

    info "Downloading CHECKSUM file for verification..."
    local tmp_checksum
    tmp_checksum="$(mktemp)"
    _fetch "$checksum_url" > "$tmp_checksum"

    local iso_name expected actual
    iso_name="$(basename "$iso_file")"
    # Fedora CHECKSUM lines: SHA256 (filename) = hash
    expected=$(grep -F "($iso_name)" "$tmp_checksum" \
                | grep -oP '= \K[0-9a-f]{64}' | head -1)
    rm -f "$tmp_checksum"

    if [[ -z "$expected" ]]; then
        warn "Could not find SHA256 entry for $iso_name — skipping verification"
        return 0
    fi

    info "Verifying SHA-256..."
    actual=$(sha256sum "$iso_file" | awk '{print $1}')

    if [[ "$actual" == "$expected" ]]; then
        success "SHA-256 checksum verified"
    else
        warn "Checksum MISMATCH — ISO may be corrupted"
        warn "  Expected: $expected"
        warn "  Actual:   $actual"
        return 1
    fi
}

download_iso() {
    local iso_url="$1" dir_url="$2"
    local iso_name
    iso_name="$(basename "$iso_url")"

    mkdir -p "$DOWNLOAD_DIR"
    local dest="$DOWNLOAD_DIR/$iso_name"

    if [[ -f "$dest" ]]; then
        warn "File already exists: $dest"
        read -rp "Re-download? [y/N] " -n 1; echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            info "Keeping existing file"
        else
            rm -f "$dest"
        fi
    fi

    if [[ ! -f "$dest" ]]; then
        info "Downloading $iso_name..."
        echo ""
        if command -v wget &>/dev/null; then
            wget -c --progress=bar:force "$iso_url" -O "$dest"
        else
            curl -L -C - --progress-bar "$iso_url" -o "$dest"
        fi
        echo ""
        success "Download complete"
    fi

    local checksum_url
    checksum_url="$(find_checksum_url "$dir_url")"
    verify_iso "$dest" "$checksum_url" || die "Aborting due to checksum failure. Remove $dest and retry."

    echo ""
    success "Ready: $dest"
    echo ""
    info "Size        : $(du -h "$dest" | cut -f1)"
    info "Bootable USB: sudo dd if=\"$dest\" of=/dev/sdX bs=4M status=progress"
}

# ── Interactive browser ────────────────────────────────────────────────────────

browse() {
    # Stack of URLs navigated so far
    local -a stack=("$BASE_URL")

    while true; do
        local current="${stack[-1]}"

        info "Fetching directory listing..."
        local -a entries
        mapfile -t entries < <(list_entries "$current")

        if [[ ${#entries[@]} -eq 0 ]]; then
            warn "No entries found at: $current"
            warn "Check your network connection or try a different mirror."
            # pop and go back
            if [[ ${#stack[@]} -gt 1 ]]; then
                stack=("${stack[@]::$((${#stack[@]} - 1))}")
                continue
            else
                exit 1
            fi
        fi

        echo ""
        echo -e "  ${BOLD}Location:${RESET} $current"
        echo ""

        local i=1
        for entry in "${entries[@]}"; do
            if [[ "$entry" == *.iso ]]; then
                # Highlight ISO files
                echo -e "  ${GREEN}$i)${RESET} $entry"
            elif [[ "$entry" == *CHECKSUM* ]]; then
                # Dim CHECKSUM files (informational; not directly selectable)
                echo -e "  ${BOLD}$i)${RESET} $entry"
            else
                echo "  $i) $entry"
            fi
            ((i++))
        done

        echo ""
        if [[ ${#stack[@]} -gt 1 ]]; then
            echo "  0) ← Back"
        else
            echo "  0) Exit"
        fi
        echo ""

        local choice
        read -rp "Selection [0-${#entries[@]}]: " choice

        # Validate input
        if ! [[ "$choice" =~ ^[0-9]+$ ]]; then
            warn "Enter a number"
            continue
        fi

        if [[ "$choice" -eq 0 ]]; then
            if [[ ${#stack[@]} -gt 1 ]]; then
                stack=("${stack[@]::$((${#stack[@]} - 1))}")   # pop
            else
                info "Exiting."
                exit 0
            fi
            continue
        fi

        local idx=$(( choice - 1 ))
        if [[ $idx -ge ${#entries[@]} ]]; then
            warn "Enter a number between 0 and ${#entries[@]}"
            continue
        fi

        local selected="${entries[$idx]}"

        if [[ "$selected" == *.iso ]]; then
            echo ""
            info "Selected: $selected"
            read -rp "Download this ISO? [Y/n] " -n 1; echo
            if [[ $REPLY =~ ^[Nn]$ ]]; then
                continue
            fi
            download_iso "${current}${selected}" "$current"
            exit 0

        elif [[ "$selected" == */ ]]; then
            stack+=("${current}${selected}")

        else
            # Plain file that isn't an ISO (e.g. CHECKSUM, .torrent) — just inform
            info "Not downloadable via this tool: $selected"
            info "URL: ${current}${selected}"
        fi
    done
}

# ── Entry point ────────────────────────────────────────────────────────────────

echo ""
echo -e "${BOLD}  Fedora ISO Browser${RESET}"
echo -e "  Mirror: $BASE_URL"
echo ""

browse
