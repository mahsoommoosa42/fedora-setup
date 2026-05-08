"""The :class:`Context` carries shared state between modules.

A single ``Context`` instance is constructed by ``__main__`` (or the cleanup
entry point) and threaded through every module / runner call. It replaces the
ad-hoc global shell variables (``DRY_RUN``, ``CLEAN_INSTALL``, ``BASHRC``,
``FEDORA_SETUP_SHELL_INIT``) that the original Bash code relied on.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _default_script_dir() -> Path:
    env = os.environ.get("FEDORA_SETUP_DIR")
    if env:
        return Path(env)
    # Falls back to the parent of the package directory (the repo root).
    return Path(__file__).resolve().parent.parent


def _default_home() -> Path:
    return Path(os.environ.get("HOME", str(Path.home())))


def _default_bashrc(home: Path) -> Path:
    env = os.environ.get("BASHRC")
    if env:
        return Path(env)
    return home / ".bashrc"


def _default_shell_init(home: Path) -> Path:
    env = os.environ.get("FEDORA_SETUP_SHELL_INIT")
    if env:
        return Path(env)
    return home / ".config" / "fedora-setup" / "shell-init.sh"


@dataclass
class Context:
    """Runtime context shared by all modules and runner wrappers."""

    dry_run: bool = False
    clean_install: bool = False
    script_dir: Path = field(default_factory=_default_script_dir)
    home: Path = field(default_factory=_default_home)
    bashrc: Path = field(init=False)
    shell_init_path: Path = field(init=False)

    def __post_init__(self) -> None:
        self.bashrc = _default_bashrc(self.home)
        self.shell_init_path = _default_shell_init(self.home)

    @classmethod
    def from_env(cls, **overrides: object) -> "Context":
        """Build a Context honouring ``DRY_RUN`` / ``CLEAN_INSTALL`` env vars."""
        env_truthy = {"1", "true", "yes", "on"}
        kwargs: dict[str, object] = {
            "dry_run": os.environ.get("DRY_RUN", "0").lower() in env_truthy,
            "clean_install": os.environ.get("CLEAN_INSTALL", "0").lower() in env_truthy,
        }
        kwargs.update(overrides)
        return cls(**kwargs)  # type: ignore[arg-type]
