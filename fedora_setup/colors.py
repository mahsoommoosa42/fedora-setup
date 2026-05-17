"""ANSI colors and logging helpers (port of ``lib/colors.sh``).

Output format is preserved verbatim so existing integration tests that grep
for ``info``/``success``/``section`` markers keep passing.
"""

from __future__ import annotations

import sys

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
BOLD = "\033[1m"
RESET = "\033[0m"


def info(message: str) -> None:
    print(f"{BLUE}  \u2022{RESET} {message}")


def success(message: str) -> None:
    print(f"{GREEN}  \u2713{RESET} {message}")


def warn(message: str) -> None:
    print(f"{YELLOW}  \u26a0{RESET} {message}")


def die(message: str) -> None:
    print(f"{RED}  \u2717 ERROR:{RESET} {message}", file=sys.stderr)
    sys.exit(1)


_SECTION_RULE = "\u2550" * 42


def section(title: str) -> None:
    print()
    print(f"{BOLD}{BLUE}{_SECTION_RULE}{RESET}")
    print(f"{BOLD}  {title}{RESET}")
    print(f"{BOLD}{BLUE}{_SECTION_RULE}{RESET}")
