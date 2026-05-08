#!/usr/bin/env bash
section "13 · Shell Quality of Life"

# Clean existing shell configurations if CLEAN_INSTALL is set
clean_config "zoxide init"
clean_config "fzf keybindings"
clean_config "eza aliases"
clean_config "bat alias"
clean_config "HISTSIZE settings"
clean_config "uv PATH"
clean_config "bun PATH"
clean_config "rustup PATH"
clean_config "starship init"

append_if_missing "zoxide init" \
'# zoxide — smarter cd
eval "$(zoxide init bash)"'

append_if_missing "fzf keybindings" \
'# fzf
[ -f /usr/share/fzf/shell/key-bindings.bash ] && source /usr/share/fzf/shell/key-bindings.bash
export FZF_DEFAULT_COMMAND="fd --type f --hidden --follow --exclude .git"
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"'

append_if_missing "eza aliases" \
'# eza — modern ls
alias ls="eza --icons --group-directories-first"
alias ll="eza -lah --icons --git --group-directories-first"
alias lt="eza --tree --icons --level=2"'

append_if_missing "bat alias" \
'# bat — better cat
alias cat="bat --paging=never"'

append_if_missing "HISTSIZE settings" \
'# Shell history
export HISTSIZE=100000
export HISTFILESIZE=100000
export HISTCONTROL=ignoredups:erasedups
shopt -s histappend'

success "Shell aliases and history configured"
