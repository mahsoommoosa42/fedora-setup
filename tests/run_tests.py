#!/usr/bin/env python3
"""
Unified test runner for the fedora-setup suite.

Runs bats unit tests and pytest Docker integration tests, then prints a
colour-coded summary table.

Usage (from the fedora-setup/ directory):
    uv run python tests/run_tests.py                 # all fast tests
    uv run python tests/run_tests.py --unit          # bats only
    uv run python tests/run_tests.py --integration   # Docker only
    uv run python tests/run_tests.py --slow          # include real-install tests
    uv run python tests/run_tests.py --no-docker     # skip Docker entirely
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

    _console = Console()

    def _print_table(results: list[tuple[str, int]]) -> None:
        table = Table(title="Test Results", show_lines=True)
        table.add_column("Suite", style="bold")
        table.add_column("Status", justify="center")
        for name, code in results:
            status = "[green]PASS[/green]" if code == 0 else "[red]FAIL[/red]"
            table.add_row(name, status)
        _console.print(table)

except ImportError:
    def _print_table(results: list[tuple[str, int]]) -> None:
        width = max(len(n) for n, _ in results) + 4
        print("\n" + "=" * (width + 10))
        for name, code in results:
            status = "PASS" if code == 0 else "FAIL"
            print(f"  {status}  {name}")
        print("=" * (width + 10))


def _run(cmd: list[str], cwd: Path | None = None) -> int:
    """Run a command, stream its output, and return the exit code."""
    result = subprocess.run(cmd, cwd=str(cwd or REPO_ROOT))
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run fedora-setup test suite")
    parser.add_argument("--unit", action="store_true", help="Run bats unit tests only")
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
        help="Skip Docker integration tests (bats unit tests still run)",
    )
    args = parser.parse_args()

    # Determine which suites to run
    run_unit = args.unit or (not args.integration)
    run_integration = (args.integration or (not args.unit)) and not args.no_docker

    results: list[tuple[str, int]] = []

    # ── bats unit tests ───────────────────────────────────────────────────────
    if run_unit:
        print("\n" + "═" * 50)
        print("  Unit Tests  (bats)")
        print("═" * 50)
        code = _run(["bats", str(TESTS_DIR / "unit")], cwd=REPO_ROOT)
        results.append(("Unit tests (bats)", code))

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
