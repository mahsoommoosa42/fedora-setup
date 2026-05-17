"""Module 13 · Shell quality of life (zoxide, fzf, eza, bat, history)."""

from __future__ import annotations

from .. import colors, shell_init
from ..context import Context


def run(ctx: Context) -> None:
    colors.section("13 · Shell Quality of Life")

    for marker in (
        "zoxide init",
        "fzf keybindings",
        "eza aliases",
        "bat alias",
        "HISTSIZE settings",
    ):
        shell_init.clean_shell_init(ctx, marker)

    shell_init.append_to_shell_init(
        ctx,
        "zoxide init",
        '# zoxide — smarter cd\n'
        'eval "$(zoxide init bash)"',
    )

    shell_init.append_to_shell_init(
        ctx,
        "fzf keybindings",
        '# fzf\n'
        '[ -f /usr/share/fzf/shell/key-bindings.bash ] '
        '&& source /usr/share/fzf/shell/key-bindings.bash\n'
        'export FZF_DEFAULT_COMMAND="fd --type f --hidden --follow --exclude .git"\n'
        'export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"',
    )

    shell_init.append_to_shell_init(
        ctx,
        "eza aliases",
        '# eza — modern ls\n'
        'alias ls="eza --icons --group-directories-first"\n'
        'alias ll="eza -lah --icons --git --group-directories-first"\n'
        'alias lt="eza --tree --icons --level=2"',
    )

    shell_init.append_to_shell_init(
        ctx,
        "bat alias",
        '# bat — better cat\n'
        'alias cat="bat --paging=never"',
    )

    shell_init.append_to_shell_init(
        ctx,
        "HISTSIZE settings",
        '# Shell history\n'
        'export HISTSIZE=100000\n'
        'export HISTFILESIZE=100000\n'
        'export HISTCONTROL=ignoredups:erasedups\n'
        'shopt -s histappend',
    )

    colors.success("Shell aliases and history configured")
