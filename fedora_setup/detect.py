"""Environment detection helpers (port of ``lib/detect.sh`` and
``lib/fedora_releases.sh``).

Every detector consults its override env var first so unit tests can mock
the result without touching the host system. The override semantics mirror
the original Bash exactly: a value of ``1`` / ``true`` / ``yes`` / ``on``
forces the predicate to return ``True``; any other defined value forces
``False``.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

_TRUTHY = {"1", "true", "yes", "on"}
_FEDORA_VERSIONS_FALLBACK: tuple[int, ...] = (44, 43, 42)


def _env_override(name: str) -> bool | None:
    """Return ``True``/``False`` if ``name`` is set, else ``None``."""
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return None
    return raw.lower() in _TRUTHY


def is_wsl() -> bool:
    override = _env_override("IS_WSL")
    if override is not None:
        return override
    if os.environ.get("WSL_DISTRO_NAME"):
        return True
    proc_version = Path(os.environ.get("PROC_VERSION_OVERRIDE", "/proc/version"))
    try:
        return "microsoft" in proc_version.read_text(errors="ignore").lower()
    except OSError:
        return False


def has_nvidia() -> bool:
    override = _env_override("HAS_NVIDIA")
    if override is not None:
        return override
    # lspci works on native systems
    lspci = shutil.which("lspci")
    if lspci is not None:
        try:
            result = subprocess.run(
                [lspci],
                capture_output=True,
                text=True,
                check=False,
            )
            if "nvidia" in result.stdout.lower():
                return True
        except OSError:
            pass
    # In WSL2, lspci doesn't show the host GPU but nvidia-smi does
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi is not None:
        try:
            result = subprocess.run(
                [nvidia_smi],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return True
        except OSError:
            pass
    return False


def has_systemd() -> bool:
    path = Path(os.environ.get("SYSTEMD_DIR_OVERRIDE", "/run/systemd/system"))
    return path.is_dir()


def is_interactive() -> bool:
    return sys.stdin.isatty()


def get_fedora_versions() -> list[int]:
    """Return the last 3 stable Fedora release numbers in descending order.

    Queries the Fedora Bodhi API. Falls back to a known-good list whenever
    the API is unreachable (e.g. in offline CI).
    """
    url = "https://bodhi.fedoraproject.org/releases/?rows_per_page=50&state=current"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read())
        versions = sorted(
            (
                int(release["version"])
                for release in data.get("releases", [])
                if release.get("id_prefix") == "FEDORA"
                and str(release.get("version", "")).isdigit()
            ),
            reverse=True,
        )
        if versions:
            return versions[:3]
    except Exception:
        pass
    return list(_FEDORA_VERSIONS_FALLBACK)
