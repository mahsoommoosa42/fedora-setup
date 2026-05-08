#!/usr/bin/env bash
section "13 · Shell Quality of Life"

# Clean existing shell configurations if CLEAN_INSTALL is set
clean_shell_init "zoxide init"
clean_shell_init "fzf keybindings"
clean_shell_init "eza aliases"
clean_shell_init "bat alias"
clean_shell_init "HISTSIZE settings"

append_to_shell_init "zoxide init" \
'# zoxide — smarter cd
eval "$(zoxide init bash)"'

append_to_shell_init "fzf keybindings" \
'# fzf
[ -f /usr/share/fzf/shell/key-bindings.bash ] && source /usr/share/fzf/shell/key-bindings.bash
export FZF_DEFAULT_COMMAND="fd --type f --hidden --follow --exclude .git"
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"'

append_to_shell_init "eza aliases" \
'# eza — modern ls
alias ls="eza --icons --group-directories-first"
alias ll="eza -lah --icons --git --group-directories-first"
alias lt="eza --tree --icons --level=2"'

append_to_shell_init "bat alias" \
'# bat — better cat
alias cat="bat --paging=never"'

append_to_shell_init "HISTSIZE settings" \
'# Shell history
export HISTSIZE=100000
export HISTFILESIZE=100000
export HISTCONTROL=ignoredups:erasedups
shopt -s histappend'

success "Shell aliases and history configured"
