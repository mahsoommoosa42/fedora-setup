"""Module registry — defines the canonical run order."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType

# Order matches the original numbered shell modules (01-base … 13-shell).
_MODULE_NAMES: tuple[tuple[str, str], ...] = (
    ("01-base", "fedora_setup.modules.base"),
    ("02-cli", "fedora_setup.modules.cli_tools"),
    ("03-cpp", "fedora_setup.modules.cpp"),
    ("04-kernel", "fedora_setup.modules.kernel"),
    ("05-python", "fedora_setup.modules.python_setup"),
    ("06-js", "fedora_setup.modules.js"),
    ("07-claude", "fedora_setup.modules.claude"),
    ("08-fonts", "fedora_setup.modules.fonts"),
    ("09-rust", "fedora_setup.modules.rust"),
    ("10-gpu", "fedora_setup.modules.gpu"),
    ("11-editors", "fedora_setup.modules.editors"),
    ("12-git", "fedora_setup.modules.git_config"),
    ("13-shell", "fedora_setup.modules.shell_qol"),
)


def _load(name: str) -> ModuleType:
    return import_module(name)


MODULE_ORDER: list[tuple[str, ModuleType]] = [
    (display, _load(target)) for display, target in _MODULE_NAMES
]
