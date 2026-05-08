"""pytest fixtures: Fedora container lifecycle for integration tests.

docker.from_env() auto-connects to whichever Docker daemon is available:
  - Docker Desktop on Windows  → named pipe
  - Docker Desktop via WSL2    → Unix socket exposed to WSL
  - Native Linux Docker daemon → /var/run/docker.sock

No manual configuration is needed; Docker Desktop just needs to be running.
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import docker
import pytest

# fedora-setup/ directory (parent of tests/)
PROJECT_ROOT = Path(__file__).parent.parent.parent


def _get_fedora_versions() -> list[int]:
    """Return the last 3 stable Fedora release numbers in descending order.

    Queries the Fedora Bodhi API. Falls back to a known-good list when the API
    is unreachable (e.g. in an offline CI environment).
    """
    _FALLBACK = [44, 43, 42]
    try:
        url = "https://bodhi.fedoraproject.org/releases/?rows_per_page=50&state=current"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read())
        versions = sorted(
            [
                int(r["version"])
                for r in data["releases"]
                if r.get("id_prefix") == "FEDORA" and str(r["version"]).isdigit()
            ],
            reverse=True,
        )
        return versions[:3] if versions else _FALLBACK
    except Exception:
        return _FALLBACK


# Fedora versions to test (last 3 releases — resolved at import time)
FEDORA_VERSIONS: list[int] = _get_fedora_versions()
DEFAULT_FEDORA_VERSION: int = FEDORA_VERSIONS[0]


def _get_or_build_image(client: docker.DockerClient, version: int = DEFAULT_FEDORA_VERSION) -> str:
    """Build the test image if it isn't already cached locally."""
    image_name = f"fedora-setup-test:{version}"
    try:
        client.images.get(image_name)
    except docker.errors.ImageNotFound:
        dockerfile_path = Path(__file__).parent.parent / "Dockerfile.fedora"
        client.images.build(
            path=str(PROJECT_ROOT),
            dockerfile=str(dockerfile_path),
            buildargs={"FEDORA_VERSION": str(version)},
            tag=image_name,
            rm=True,
        )
    return image_name


def _start_container(
    client: docker.DockerClient,
    env: dict[str, str],
    version: int = DEFAULT_FEDORA_VERSION,
) -> docker.models.containers.Container:
    image_name = _get_or_build_image(client, version)
    return client.containers.run(
        image_name,
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


# ── Per-environment containers (parameterized by Fedora version) ───────────────

@pytest.fixture(scope="session")
def fedora_native(docker_client):
    """Fedora container simulating a native (non-WSL) install with DRY_RUN=1."""
    container = _start_container(docker_client, {
        "IS_WSL": "0",
        "HAS_NVIDIA": "0",
        "DRY_RUN": "1",
    }, DEFAULT_FEDORA_VERSION)
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
    }, DEFAULT_FEDORA_VERSION)
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
    }, DEFAULT_FEDORA_VERSION)
    yield container
    container.remove(force=True)


# ── Multi-version test fixtures ───────────────────────────────────────────────────

@pytest.fixture(scope="session", params=FEDORA_VERSIONS)
def fedora_native_multi(docker_client, request):
    """Fedora container for each version simulating native install with DRY_RUN=1."""
    version = request.param
    container = _start_container(docker_client, {
        "IS_WSL": "0",
        "HAS_NVIDIA": "0",
        "DRY_RUN": "1",
    }, version)
    yield container
    container.remove(force=True)


@pytest.fixture(scope="session", params=FEDORA_VERSIONS)
def fedora_wsl_multi(docker_client, request):
    """Fedora container for each version simulating WSL2 install with DRY_RUN=1."""
    version = request.param
    container = _start_container(docker_client, {
        "IS_WSL": "1",
        "WSL_DISTRO_NAME": "fedora",
        "HAS_NVIDIA": "0",
        "DRY_RUN": "1",
    }, version)
    yield container
    container.remove(force=True)
