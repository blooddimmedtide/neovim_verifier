#!/bin/sh
# Extract get_op, get_option_prefix, find_tty_option_end verbatim from the pinned option.c.
# usage: extract.sh <neovim tree>  -> writes extracted.c, checks sha256 pins
set -e
src="$1/src/nvim/option.c"
: > extracted.c
for fn in "static set_op_T get_op(" "static set_prefix_T get_option_prefix(" "static const char *find_tty_option_end(" "bool is_tty_option(" "const char *find_option_end("; do
  awk -v pat="$fn" 'index($0, pat) == 1 {on=1} on {print} on && /^}/ {exit}' "$src" >> extracted.c
done
sha256sum -c pins.sha256
