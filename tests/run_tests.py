#!/usr/bin/env python3
"""
Unified test runner for the fedora-setup suite.

Runs the pytest unit tests and the pytest Docker integration tests, then
prints a colour-coded summary table.

Usage (from the fedora-setup/ directory):
    uv run python tests/run_tests.py                 # all fast tests
    uv run python tests/run_tests.py --unit          # unit tests only
    uv run python tests/run_tests.py --integration   # Docker only
    uv run python tests/run_tests.py --slow          # include real-install tests
    uv run python tests/run_tests.py --no-docker     # skip Docker entirely
    uv run python tests/run_tests.py -i              # interactive menu
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).parent
REPO_ROOT = TESTS_DIR.parent

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text

    _console = Console()

    def _print_table(results: list[tuple[str, int]]) -> None:
        table = Table(title="Test Results", show_lines=True)
        table.add_column("Suite", style="bold")
        table.add_column("Status", justify="center")
        for name, code in results:
            status = "[green]PASS[/green]" if code == 0 else "[red]FAIL[/red]"
            table.add_row(name, status)
        _console.print(table)

    def _print_menu(title: str, options: list[str]) -> None:
        body = Text()
        for i, opt in enumerate(options, 1):
            body.append(f"  {i}) ", style="bold cyan")
            body.append(f"{opt}\n")
        body.append("\n  q) ", style="bold cyan")
        body.append("Quit")
        _console.print(Panel(body, title=f"[bold]{title}[/bold]", expand=False))

except ImportError:
    _console = None  # type: ignore[assignment]

    def _print_table(results: list[tuple[str, int]]) -> None:
        width = max(len(n) for n, _ in results) + 4
        print("\n" + "=" * (width + 10))
        for name, code in results:
            status = "PASS" if code == 0 else "FAIL"
            print(f"  {status}  {name}")
        print("=" * (width + 10))

    def _print_menu(title: str, options: list[str]) -> None:
        print(f"\n{'─' * 50}")
        print(f"  {title}")
        print(f"{'─' * 50}")
        for i, opt in enumerate(options, 1):
            print(f"  {i}) {opt}")
        print("  q) Quit")
        print(f"{'─' * 50}")


def _run(cmd: list[str], cwd: Path | None = None) -> int:
    """Run a command, stream its output, and return the exit code."""
    result = subprocess.run(cmd, cwd=str(cwd or REPO_ROOT))
    return result.returncode


def _ask(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return "q"


def _pick_unit_file() -> Path | None:
    """Let the user pick a single unit-test file, or all of them."""
    files = sorted((TESTS_DIR / "unit").glob("test_*.py"))
    options = ["All unit test files"] + [f.name for f in files]
    _print_menu("Pick a unit-test file", options)
    choice = _ask("Enter number (or q): ")
    if choice == "q":
        return None
    try:
        idx = int(choice)
    except ValueError:
        print("  Invalid choice.")
        return None
    if idx == 1:
        return TESTS_DIR / "unit"
    if 2 <= idx <= len(options):
        return files[idx - 2]
    print("  Invalid choice.")
    return None


def _interactive(slow: bool) -> int:
    """Present a menu and run the selected suite(s). Returns overall exit code."""
    options = [
        "All fast tests  (unit + integration)",
        "Unit tests only",
        "Integration tests only  (Docker)",
        "Single unit-test file",
    ]

    results: list[tuple[str, int]] = []

    while True:
        _print_menu("fedora-setup test runner", options)
        choice = _ask("Enter number (or q): ")

        if choice == "q":
            break

        try:
            idx = int(choice)
        except ValueError:
            print("  Invalid choice — enter a number or q.")
            continue

        if idx not in range(1, len(options) + 1):
            print("  Invalid choice — enter a number or q.")
            continue

        results.clear()

        if idx in (1, 2):
            print("\n" + "═" * 50)
            print("  Unit Tests  (pytest)")
            print("═" * 50)
            code = _run(
                ["uv", "run", "pytest", str(TESTS_DIR / "unit"), "-v", "--timeout=60"],
                cwd=TESTS_DIR,
            )
            results.append(("Unit tests (pytest)", code))

        if idx in (1, 3):
            print("\n" + "═" * 50)
            print("  Integration Tests  (pytest + Docker)")
            print("═" * 50)
            pytest_cmd = [
                "uv", "run", "pytest",
                str(TESTS_DIR / "integration"),
                "-v",
                "--timeout=120",
            ]
            if not slow:
                pytest_cmd += ["-m", "not slow"]
            code = _run(pytest_cmd, cwd=TESTS_DIR)
            results.append(("Integration tests (pytest + Docker)", code))

        if idx == 4:
            target = _pick_unit_file()
            if target is None:
                continue
            print(f"\n  Running: {target.name if target.is_file() else 'all unit files'}")
            code = _run(
                ["uv", "run", "pytest", str(target), "-v", "--timeout=60"],
                cwd=TESTS_DIR,
            )
            label = target.name if target.is_file() else "Unit tests (pytest)"
            results.append((label, code))

        print()
        _print_table(results)

        overall = 0 if all(c == 0 for _, c in results) else 1
        if overall == 0:
            print("\n  All tests passed.\n")
        else:
            print("\n  Some tests FAILED — see output above.\n")

        again = _ask("Run another suite? [y/N]: ")
        if again.lower() != "y":
            break

    return 0 if not results or all(c == 0 for _, c in results) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run fedora-setup test suite")
    parser.add_argument(
        "-i", "--interactive", action="store_true",
        help="Interactive menu to pick which suite to run",
    )
    parser.add_argument("--unit", action="store_true", help="Run pytest unit tests only")
    parser.add_argument(
        "--integration", action="store_true",
        help="Run pytest+Docker integration tests only",
    )
    parser.add_argument(
        "--slow", action="store_true",
        help="Include slow real-install tests (requires network, ~30 min)",
    )
    parser.add_argument(
        "--no-docker", action="store_true",
        help="Skip Docker integration tests (unit tests still run)",
    )
    args = parser.parse_args()

    if args.interactive:
        return _interactive(slow=args.slow)

    # Determine which suites to run
    run_unit = args.unit or (not args.integration)
    run_integration = (args.integration or (not args.unit)) and not args.no_docker

    results: list[tuple[str, int]] = []

    # ── pytest unit tests ─────────────────────────────────────────────────────
    if run_unit:
        print("\n" + "═" * 50)
        print("  Unit Tests  (pytest)")
        print("═" * 50)
        code = _run(
            [
                "uv", "run", "pytest",
                str(TESTS_DIR / "unit"),
                "-v",
                "--timeout=60",
            ],
            cwd=TESTS_DIR,
        )
        results.append(("Unit tests (pytest)", code))

    # ── pytest integration tests ──────────────────────────────────────────────
    if run_integration:
        print("\n" + "═" * 50)
        print("  Integration Tests  (pytest + Docker)")
        print("═" * 50)
        pytest_cmd = [
            "uv", "run", "pytest",
            str(TESTS_DIR / "integration"),
            "-v",
            "--timeout=120",
        ]
        if not args.slow:
            pytest_cmd += ["-m", "not slow"]
        code = _run(pytest_cmd, cwd=TESTS_DIR)
        results.append(("Integration tests (pytest + Docker)", code))

    # ── summary ───────────────────────────────────────────────────────────────
    print()
    _print_table(results)

    overall = 0 if all(c == 0 for _, c in results) else 1
    if overall == 0:
        print("\n  All tests passed.\n")
    else:
        print("\n  Some tests FAILED — see output above.\n")
    return overall


if __name__ == "__main__":
    sys.exit(main())
