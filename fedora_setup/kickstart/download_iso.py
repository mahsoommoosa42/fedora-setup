"""Interactive Fedora ISO browser & SHA-256 verifier.

Port of ``kickstart/download-iso.sh``. Run with::

    python3 -m fedora_setup.kickstart.download_iso

Options match the original shell script.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

from .. import colors

BASE_URL_DEFAULT = "https://dl.fedoraproject.org/pub/fedora/linux/releases/"
DEFAULT_DOWNLOAD_DIR = Path.home() / "Downloads" / "Fedora-ISOs"

_HREF_RE = re.compile(r'href="([^"]+)"', re.IGNORECASE)


def _fetch(url: str) -> str:
    """Fetch a URL as text. Mirrors the curl/wget logic in the shell version."""
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        colors.warn(f"Failed to fetch {url}: {exc}")
        return ""


def _list_entries(url: str) -> list[str]:
    """Parse an Apache/Nginx directory listing for plain filenames / dirs."""
    body = _fetch(url)
    entries: list[str] = []
    for match in _HREF_RE.finditer(body):
        target = match.group(1)
        if not target or target.startswith(("/", "?")) or target.startswith(".."):
            continue
        entries.append(target)
    # Dedup while preserving order.
    seen: set[str] = set()
    return [e for e in entries if not (e in seen or seen.add(e))]


def _find_checksum_url(dir_url: str) -> str:
    for entry in _list_entries(dir_url):
        if "CHECKSUM" in entry.upper():
            return f"{dir_url}{entry}"
    return ""


def _verify_iso(iso_file: Path, checksum_url: str) -> bool:
    if not checksum_url:
        colors.warn("No CHECKSUM file found in this directory — skipping verification")
        return True

    colors.info("Downloading CHECKSUM file for verification...")
    body = _fetch(checksum_url)
    if not body:
        colors.warn("Could not download CHECKSUM file — skipping verification")
        return True

    iso_name = iso_file.name
    expected = ""
    pattern = re.compile(rf"\({re.escape(iso_name)}\).*?=\s*([0-9a-f]{{64}})", re.IGNORECASE)
    match = pattern.search(body)
    if match:
        expected = match.group(1).lower()

    if not expected:
        colors.warn(f"Could not find SHA256 entry for {iso_name} — skipping verification")
        return True

    colors.info("Verifying SHA-256...")
    sha = hashlib.sha256()
    with iso_file.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(chunk)
    actual = sha.hexdigest().lower()

    if actual == expected:
        colors.success("SHA-256 checksum verified")
        return True

    colors.warn("Checksum MISMATCH — ISO may be corrupted")
    colors.warn(f"  Expected: {expected}")
    colors.warn(f"  Actual:   {actual}")
    return False


def _download(url: str, dest: Path) -> None:
    """Download ``url`` to ``dest`` using wget/curl when available, else stdlib."""
    if shutil.which("wget"):
        subprocess.run(
            ["wget", "-c", "--progress=bar:force", url, "-O", str(dest)],
            check=True,
        )
        return
    if shutil.which("curl"):
        subprocess.run(
            ["curl", "-L", "-C", "-", "--progress-bar", url, "-o", str(dest)],
            check=True,
        )
        return

    colors.info(f"Downloading {url} (stdlib)...")
    with urllib.request.urlopen(url, timeout=60) as response, dest.open("wb") as out:
        shutil.copyfileobj(response, out)


def _download_iso(iso_url: str, dir_url: str, download_dir: Path) -> None:
    iso_name = iso_url.rsplit("/", 1)[-1]
    download_dir.mkdir(parents=True, exist_ok=True)
    dest = download_dir / iso_name

    if dest.is_file():
        colors.warn(f"File already exists: {dest}")
        try:
            answer = input("Re-download? [y/N] ").strip().lower()
        except EOFError:
            answer = "n"
        if answer == "y":
            dest.unlink()
        else:
            colors.info("Keeping existing file")

    if not dest.is_file():
        colors.info(f"Downloading {iso_name}...")
        print()
        _download(iso_url, dest)
        print()
        colors.success("Download complete")

    if not _verify_iso(dest, _find_checksum_url(dir_url)):
        colors.die(f"Aborting due to checksum failure. Remove {dest} and retry.")

    print()
    colors.success(f"Ready: {dest}")
    print()
    colors.info(f"Size        : {_human_size(dest.stat().st_size)}")
    colors.info(f'Bootable USB: sudo dd if="{dest}" of=/dev/sdX bs=4M status=progress')


def _human_size(num_bytes: int) -> str:
    for unit in ("B", "K", "M", "G", "T"):
        if num_bytes < 1024 or unit == "T":
            return f"{num_bytes:.1f}{unit}"
        num_bytes //= 1024
    return f"{num_bytes}T"


def _browse(base_url: str, download_dir: Path) -> int:
    stack: list[str] = [base_url]

    while True:
        current = stack[-1]

        colors.info("Fetching directory listing...")
        entries = _list_entries(current)

        if not entries:
            colors.warn(f"No entries found at: {current}")
            colors.warn("Check your network connection or try a different mirror.")
            if len(stack) > 1:
                stack.pop()
                continue
            return 1

        print()
        print(f"  {colors.BOLD}Location:{colors.RESET} {current}")
        print()

        for idx, entry in enumerate(entries, start=1):
            if entry.endswith(".iso"):
                print(f"  {colors.GREEN}{idx}){colors.RESET} {entry}")
            elif "CHECKSUM" in entry.upper():
                print(f"  {colors.BOLD}{idx}){colors.RESET} {entry}")
            else:
                print(f"  {idx}) {entry}")

        print()
        print("  0) ← Back" if len(stack) > 1 else "  0) Exit")
        print()

        try:
            raw = input(f"Selection [0-{len(entries)}]: ").strip()
        except EOFError:
            return 0

        if not raw.isdigit():
            colors.warn("Enter a number")
            continue

        choice = int(raw)
        if choice == 0:
            if len(stack) > 1:
                stack.pop()
                continue
            colors.info("Exiting.")
            return 0

        if choice > len(entries):
            colors.warn(f"Enter a number between 0 and {len(entries)}")
            continue

        selected = entries[choice - 1]

        if selected.endswith(".iso"):
            print()
            colors.info(f"Selected: {selected}")
            try:
                confirm = input("Download this ISO? [Y/n] ").strip().lower()
            except EOFError:
                confirm = "n"
            if confirm == "n":
                continue
            _download_iso(f"{current}{selected}", current, download_dir)
            return 0

        if selected.endswith("/"):
            stack.append(f"{current}{selected}")
        else:
            colors.info(f"Not downloadable via this tool: {selected}")
            colors.info(f"URL: {current}{selected}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Interactively browse the Fedora mirror and download an ISO.",
    )
    parser.add_argument(
        "--base-url",
        default=BASE_URL_DEFAULT,
        help=f"Mirror root to browse (default: {BASE_URL_DEFAULT})",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=Path(os.environ.get("DOWNLOAD_DIR", str(DEFAULT_DOWNLOAD_DIR))),
        help=f"Download destination (default: {DEFAULT_DOWNLOAD_DIR})",
    )
    args = parser.parse_args(argv)

    print()
    print(f"{colors.BOLD}  Fedora ISO Browser{colors.RESET}")
    print(f"  Mirror: {args.base_url}")
    print()

    return _browse(args.base_url, args.dest)


if __name__ == "__main__":
    sys.exit(main())
