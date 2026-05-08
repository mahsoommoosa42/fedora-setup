"""pytest fixtures: Fedora container lifecycle for integration tests.

docker.from_env() auto-connects to whichever Docker daemon is available:
  - Docker Desktop on Windows  → named pipe
  - Docker Desktop via WSL2    → Unix socket exposed to WSL
  - Native Linux Docker daemon → /var/run/docker.sock

No manual configuration is needed; Docker Desktop just needs to be running.
"""
from __future__ import annotations

from pathlib import Path

import docker
import pytest

# fedora-setup/ directory (parent of tests/)
PROJECT_ROOT = Path(__file__).parent.parent.parent

IMAGE_NAME = "fedora-setup-test"


def _get_or_build_image(client: docker.DockerClient) -> None:
    """Build the test image if it isn't already cached locally."""
    try:
        client.images.get(IMAGE_NAME)
    except docker.errors.ImageNotFound:
        dockerfile_path = Path(__file__).parent.parent / "Dockerfile.fedora"
        client.images.build(
            path=str(PROJECT_ROOT),
            dockerfile=str(dockerfile_path),
            tag=IMAGE_NAME,
            rm=True,
        )


def _start_container(
    client: docker.DockerClient,
    env: dict[str, str],
) -> docker.models.containers.Container:
    _get_or_build_image(client)
    return client.containers.run(
        IMAGE_NAME,
        command="sleep infinity",
        detach=True,
        tty=False,
        environment=env,
        volumes={str(PROJECT_ROOT): {"bind": "/setup", "mode": "ro"}},
    )


# ── Docker client ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def docker_client():
    """Session-scoped Docker client. Skips the session if Docker is unavailable."""
    try:
        client = docker.from_env()
        client.ping()
        return client
    except Exception as exc:
        pytest.skip(f"Docker not available ({exc}). Start Docker Desktop and retry.")


# ── Per-environment containers ────────────────────────────────────────────────

@pytest.fixture(scope="session")
def fedora_native(docker_client):
    """Fedora container simulating a native (non-WSL) install with DRY_RUN=1."""
    container = _start_container(docker_client, {
        "IS_WSL": "0",
        "HAS_NVIDIA": "0",
        "DRY_RUN": "1",
    })
    yield container
    container.remove(force=True)


@pytest.fixture(scope="session")
def fedora_wsl(docker_client):
    """Fedora container simulating WSL2 Fedora with DRY_RUN=1."""
    container = _start_container(docker_client, {
        "IS_WSL": "1",
        "WSL_DISTRO_NAME": "fedora",
        "HAS_NVIDIA": "0",
        "DRY_RUN": "1",
    })
    yield container
    container.remove(force=True)


@pytest.fixture(scope="session")
def fedora_wsl_nvidia(docker_client):
    """Fedora container simulating WSL2 Fedora with an NVIDIA GPU and DRY_RUN=1."""
    container = _start_container(docker_client, {
        "IS_WSL": "1",
        "WSL_DISTRO_NAME": "fedora",
        "HAS_NVIDIA": "1",
        "DRY_RUN": "1",
    })
    yield container
    container.remove(force=True)
