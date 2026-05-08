#!/usr/bin/env bash
# =============================================================================
# fedora_releases.sh — Fedora release discovery
# Queries the Fedora Bodhi API for the last 3 stable releases.
# Falls back to known versions if the API is unreachable.
# =============================================================================

# Fallback if the Bodhi API is unreachable
FEDORA_VERSIONS_FALLBACK=(44 43 42)

# Queries the Bodhi API and populates FEDORA_VERSIONS with the last 3 stable
# Fedora release numbers in descending order (e.g. 44 43 42).
# Requires python3; falls back to FEDORA_VERSIONS_FALLBACK on any error.
get_fedora_versions() {
    local result
    if command -v python3 &>/dev/null; then
        result=$(python3 - <<'EOF'
import urllib.request, json, sys
try:
    url = "https://bodhi.fedoraproject.org/releases/?rows_per_page=50&state=current"
    with urllib.request.urlopen(url, timeout=5) as r:
        data = json.loads(r.read())
    versions = sorted(
        [int(r["version"]) for r in data["releases"]
         if r.get("id_prefix") == "FEDORA" and str(r["version"]).isdigit()],
        reverse=True,
    )
    print(" ".join(str(v) for v in versions[:3]))
except Exception:
    sys.exit(1)
EOF
        )
        if [[ $? -eq 0 && -n "$result" ]]; then
            read -ra FEDORA_VERSIONS <<< "$result"
            return 0
        fi
    fi

    # Fallback
    FEDORA_VERSIONS=("${FEDORA_VERSIONS_FALLBACK[@]}")
}
