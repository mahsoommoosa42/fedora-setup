"""Unit tests for ``fedora_setup.shell_init``."""

from __future__ import annotations

from pathlib import Path

import pytest

from fedora_setup import shell_init
from fedora_setup.context import Context


@pytest.fixture
def ctx(tmp_path: Path) -> Context:
    """Context rooted at a temp directory so tests don't touch the real HOME."""
    return Context(home=tmp_path)


def test_append_if_missing_adds_when_marker_absent(ctx: Context) -> None:
    target = ctx.home / ".bashrc"
    target.write_text("")
    shell_init.append_if_missing(
        ctx,
        "# zoxide-marker",
        '# zoxide-marker\neval "$(zoxide init bash)"',
        target,
    )
    text = target.read_text()
    assert text.count("# zoxide-marker") == 1
    assert "zoxide init bash" in text


def test_append_if_missing_is_idempotent(ctx: Context) -> None:
    target = ctx.home / ".bashrc"
    target.write_text("")
    for _ in range(3):
        shell_init.append_if_missing(
            ctx,
            "# test-idem",
            "# test-idem\nexport X=1",
            target,
        )
    assert target.read_text().count("# test-idem") == 1


def test_append_if_missing_dry_run(
    ctx: Context, capsys: pytest.CaptureFixture[str]
) -> None:
    ctx.dry_run = True
    target = ctx.home / ".bashrc"
    target.write_text("")
    shell_init.append_if_missing(ctx, "# foo", "# foo\nexport Y=1", target)
    assert target.read_text() == ""
    assert "DRY_RUN" in capsys.readouterr().out


def test_append_to_shell_init_creates_file(ctx: Context) -> None:
    shell_init.append_to_shell_init(ctx, "starship init", 'eval "$(starship init bash)"')
    assert ctx.shell_init_path.is_file()
    text = ctx.shell_init_path.read_text()
    assert "# >>> fedora-setup: starship init >>>" in text
    assert "starship init bash" in text
    assert "# <<< fedora-setup: starship init <<<" in text


def test_append_to_shell_init_idempotent(ctx: Context) -> None:
    for _ in range(3):
        shell_init.append_to_shell_init(
            ctx, "starship init", 'eval "$(starship init bash)"'
        )
    text = ctx.shell_init_path.read_text()
    assert text.count("# >>> fedora-setup: starship init >>>") == 1


def test_clean_shell_init_removes_block(ctx: Context) -> None:
    shell_init.append_to_shell_init(ctx, "tmp marker", "echo hi")
    assert "tmp marker" in ctx.shell_init_path.read_text()

    ctx.clean_install = True
    shell_init.clean_shell_init(ctx, "tmp marker")
    assert "tmp marker" not in ctx.shell_init_path.read_text()


def test_clean_shell_init_noop_when_clean_install_false(ctx: Context) -> None:
    shell_init.append_to_shell_init(ctx, "keep me", "echo keep")
    shell_init.clean_shell_init(ctx, "keep me")  # clean_install defaults to False
    assert "keep me" in ctx.shell_init_path.read_text()


def test_ensure_shell_init_adds_source_line(ctx: Context) -> None:
    bashrc = ctx.home / ".bashrc"
    bashrc.write_text("")
    shell_init.ensure_shell_init(ctx, bashrc)
    text = bashrc.read_text()
    assert str(ctx.shell_init_path) in text
    assert "fedora-setup managed shell init" in text


def test_ensure_shell_init_idempotent(ctx: Context) -> None:
    bashrc = ctx.home / ".bashrc"
    bashrc.write_text("")
    for _ in range(3):
        shell_init.ensure_shell_init(ctx, bashrc)
    assert bashrc.read_text().count("fedora-setup managed shell init") == 1


def test_remove_file_handles_missing_file(ctx: Context) -> None:
    shell_init.remove_file(ctx, ctx.home / "does-not-exist")  # must not raise


def test_remove_file_dry_run(
    ctx: Context, capsys: pytest.CaptureFixture[str]
) -> None:
    ctx.dry_run = True
    target = ctx.home / "tmp.txt"
    target.write_text("hello")
    shell_init.remove_file(ctx, target)
    assert target.is_file()
    assert "DRY_RUN" in capsys.readouterr().out
