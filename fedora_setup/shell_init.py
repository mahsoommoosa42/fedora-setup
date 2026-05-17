"""Shell-init management (port of the shell-init helpers in ``lib/utils.sh``).

The shell-init file lives at ``~/.config/fedora-setup/shell-init.sh`` and is
sourced by ``~/.bashrc`` / ``~/.zshrc`` / ``~/.bash_profile``. All
tool-specific PATH/alias/init blocks are appended here wrapped in marker
fences so that re-running setup is a no-op and ``CLEAN_INSTALL=1`` can
strip a single block precisely.
"""

from __future__ import annotations

from pathlib import Path

from . import colors
from .context import Context

SHELL_INIT_HEADER = (
    "# =============================================================================\n"
    "# Shell initialization for fedora-setup\n"
    "# This file is sourced by ~/.bashrc, ~/.zshrc, and ~/.bash_profile\n"
    "# All tool-specific configurations (PATH, aliases, init functions) go here\n"
    "# =============================================================================\n"
)

_SOURCE_HEADER_COMMENT = "# fedora-setup managed shell init (do not edit)"


def _begin_fence(marker: str) -> str:
    return f"# >>> fedora-setup: {marker} >>>"


def _end_fence(marker: str) -> str:
    return f"# <<< fedora-setup: {marker} <<<"


def _file_contains(path: Path, marker: str) -> bool:
    if not path.is_file():
        return False
    try:
        return marker in path.read_text(errors="ignore")
    except OSError:
        return False


def _append(path: Path, content: str) -> None:
    """Append a blank line + ``content`` (newline-terminated) to ``path``."""
    text = "\n" + content
    if not text.endswith("\n"):
        text += "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(text)


def ensure_shell_init(ctx: Context, shell_config: Path) -> None:
    """Ensure ``shell_init_path`` exists and is sourced from ``shell_config``.

    The block written to the user's shell config is preceded by a comment
    so it is easy to spot and easy to remove again on cleanup.
    """
    init_path = ctx.shell_init_path
    init_path.parent.mkdir(parents=True, exist_ok=True)

    if not init_path.exists():
        init_path.write_text(SHELL_INIT_HEADER, encoding="utf-8")

    if not shell_config.is_file():
        return
    if _file_contains(shell_config, _SOURCE_HEADER_COMMENT):
        return

    block = f'{_SOURCE_HEADER_COMMENT}\nsource "{init_path}"'
    _append(shell_config, block)
    colors.success(f"Added source line to {shell_config}")


def append_to_shell_init(ctx: Context, marker: str, content: str) -> None:
    """Append ``content`` (wrapped in marker fences) to the shell-init file.

    Idempotent: if the begin-fence for ``marker`` is already present the
    function is a no-op.
    """
    init_path = ctx.shell_init_path
    begin = _begin_fence(marker)
    end = _end_fence(marker)

    if _file_contains(init_path, begin):
        colors.info(f"Already in shell-init: {marker} (skipping)")
        return

    if ctx.dry_run:
        print(f"DRY_RUN: Would append {marker} block to {init_path}")
        return

    init_path.parent.mkdir(parents=True, exist_ok=True)
    if not init_path.exists():
        init_path.write_text(SHELL_INIT_HEADER, encoding="utf-8")

    block = f"{begin}\n{content}\n{end}"
    _append(init_path, block)
    colors.success(f"Added to shell-init: {marker}")


def clean_shell_init(ctx: Context, marker: str) -> None:
    """If ``CLEAN_INSTALL=1``, remove the marker block from the shell-init file."""
    if not ctx.clean_install:
        return
    init_path = ctx.shell_init_path
    begin = _begin_fence(marker)
    end = _end_fence(marker)
    if not _file_contains(init_path, begin):
        return

    colors.info(f"CLEAN_INSTALL: Removing {marker} from shell-init")
    if ctx.dry_run:
        print(f"DRY_RUN: Would strip {marker} block from {init_path}")
        return

    lines = init_path.read_text(encoding="utf-8").splitlines(keepends=True)
    out: list[str] = []
    skipping = False
    for line in lines:
        if not skipping and begin in line:
            skipping = True
            continue
        if skipping and end in line:
            skipping = False
            continue
        if skipping:
            continue
        out.append(line)
    init_path.write_text("".join(out), encoding="utf-8")


def append_if_missing(
    ctx: Context,
    marker: str,
    content: str,
    file: Path | None = None,
) -> None:
    """Append ``content`` to ``file`` (defaults to ``BASHRC``) if marker absent."""
    target = Path(file) if file is not None else ctx.bashrc
    if _file_contains(target, marker):
        colors.info(f"Already in {target}: {marker} (skipping)")
        return
    if ctx.dry_run:
        print(f"DRY_RUN: Would append {marker} to {target}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    _append(target, content)
    colors.success(f"Added to {target}: {marker}")


def clean_config(
    ctx: Context,
    marker: str,
    file: Path | None = None,
) -> None:
    """If ``CLEAN_INSTALL=1`` remove lines containing ``marker`` from ``file``."""
    if not ctx.clean_install:
        return
    target = Path(file) if file is not None else ctx.bashrc
    if not _file_contains(target, marker):
        return
    colors.info(f"CLEAN_INSTALL: Removing {marker} from {target}")
    if ctx.dry_run:
        print(f"DRY_RUN: Would strip lines containing {marker} from {target}")
        return
    lines = target.read_text(encoding="utf-8").splitlines(keepends=True)
    target.write_text(
        "".join(line for line in lines if marker not in line),
        encoding="utf-8",
    )


def remove_file(ctx: Context, path: Path | str) -> None:
    """Delete ``path`` (DRY_RUN-aware; only acts when ``CLEAN_INSTALL=1``)."""
    p = Path(path)
    if not p.is_file():
        return
    if ctx.dry_run:
        print(f"DRY_RUN: Would remove {p}")
        return
    if not ctx.clean_install:
        return
    colors.info(f"CLEAN_INSTALL: Removing {p}")
    p.unlink()
