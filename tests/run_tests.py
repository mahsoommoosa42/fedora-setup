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
    uv run python tests/run_tests.py -i              # start interactive SSH environment
"""
from __future__ import annotations

import argparse
import socket
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


def _interactive_env(dry_run: bool = False) -> int:
    """Run fedora-setup in a Fedora container, then open an SSH session to explore."""
    try:
        import docker
        import docker.errors
    except ImportError:
        print("  'docker' package not installed. Run: uv pip install docker")
        return 1

    try:
        client = docker.from_env()
        client.ping()
    except Exception as exc:
        print(f"  Docker not available: {exc}")
        print("  Make sure Docker Desktop is running, then retry.")
        return 1

    # Build (or reuse) the test image.
    image_name = "fedora-setup-test:44"
    try:
        client.images.get(image_name)
        print(f"  Using cached image {image_name}")
    except docker.errors.ImageNotFound:
        print(f"  Building {image_name} (first run, this takes ~1 min) ...")
        client.images.build(
            path=str(REPO_ROOT),
            dockerfile=str(TESTS_DIR / "Dockerfile.fedora"),
            buildargs={"FEDORA_VERSION": "44"},
            tag=image_name,
            rm=True,
        )

    # Grab a free ephemeral port on the host.
    with socket.socket() as _s:
        _s.bind(("", 0))
        host_port: int = _s.getsockname()[1]

    # Run as the 'dev' user (defined in the Dockerfile) — setup.sh rejects root.
    print("  Starting container ...")
    env = {"IS_WSL": "0", "HAS_NVIDIA": "0"}
    if dry_run:
        env["DRY_RUN"] = "1"
    container = client.containers.run(
        image_name,
        command="sleep infinity",
        detach=True,
        ports={"22/tcp": ("127.0.0.1", host_port)},
        volumes={str(REPO_ROOT): {"bind": "/setup", "mode": "ro"}},
        environment=env,
    )

    try:
        # ── Run fedora-setup ──────────────────────────────────────────────────
        label = "DRY_RUN preview" if dry_run else "full install — this may take a while"
        print(f"  Running fedora-setup ({label}) ...")
        print("  " + "─" * 56)
        setup_result = container.exec_run(
            ["/bin/bash", "/setup/setup.sh"],
            stream=True,
            user="dev",
            environment=env,
        )
        for chunk in setup_result.output:
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
        print("  " + "─" * 56)

        # ── Install SSH server (run as root via exec) ─────────────────────────
        print("  Installing SSH server ...")
        # exec_run splits strings with shlex — shell builtins, pipes, and
        # redirects only work when we invoke bash explicitly.
        ssh_cmds = [
            "dnf install -y openssh-server --quiet --setopt=install_weak_deps=False",
            "ssh-keygen -A",
            "echo 'dev:fedora' | chpasswd",
            # Drop-in overrides the base sshd_config (Fedora's Include is at the
            # top, so drop-ins take precedence). UsePAM no avoids PAM failures in
            # a minimal container without a full PAM stack.
            "mkdir -p /etc/ssh/sshd_config.d",
            "printf 'PasswordAuthentication yes\\nUsePAM no\\n'"
            " > /etc/ssh/sshd_config.d/99-interactive.conf",
            "/usr/sbin/sshd",
        ]
        for cmd in ssh_cmds:
            result = container.exec_run(["/bin/bash", "-c", cmd], user="root")
            if result.exit_code != 0:
                print(f"  Warning: command exited {result.exit_code}: {cmd}")

        print()
        print(f"  Connecting → ssh dev@localhost -p {host_port}  (password: fedora)")
        print( "  Exit the shell to stop and remove the container.\n")
        subprocess.run(
            [
                "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "-o", "LogLevel=ERROR",
                "-p", str(host_port),
                "dev@localhost",
            ]
        )
    except KeyboardInterrupt:
        print()
    finally:
        print("  Stopping container ...")
        container.stop(timeout=5)
        container.remove()

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run fedora-setup test suite")
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run fedora-setup in a Fedora container, then open an SSH session",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="With -i: run fedora-setup in DRY_RUN mode (fast preview, no packages installed)",
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
        return _interactive_env(dry_run=args.dry_run)

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
