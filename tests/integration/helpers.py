"""Shared utilities for Docker-based integration tests."""
from __future__ import annotations

import docker


def exec_in(container: docker.models.containers.Container, cmd: str) -> tuple[int, str]:
    """Run a shell command inside a running container.

    Returns (exit_code, combined_stdout_stderr).
    """
    result = container.exec_run(["bash", "-c", cmd], tty=False, demux=False)
    output = (result.output or b"").decode("utf-8", errors="replace").strip()
    return result.exit_code, output
