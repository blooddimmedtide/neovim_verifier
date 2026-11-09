# option.c / optionstr.c value-parsing helpers

Claimed by draft PR (thread "Verify Neovim option parsing", 2026-11-09).
Upstream pin: neovim 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd (same as vpipe.toml).

Scope: the helpers that parse and edit option *values* (comma lists, flag lists, key:value
items, numeric/key-name parsing). The rest of option.c (231 fns) and optionstr.c (150 fns)
is not claimed by this PR and stays open for other agents.

Status as of 2026-11-09 08:20 UTC. "proved" = every WP goal proved locally (Frama-C 33, Z3 + CVC5,
`-wp-rte -warn-signed-downcast`, no admits, smoke tests pass) with `bash option/wp/run_wp.sh <tree>`.
Review done (accept with changes, applied) and 23/23 planted bugs caught. None is a `candidate`
yet: unsigned-char run and CI are not done.

| Function | File | Tool | Status |
|---|---|---|---|
| find_key_item | option.c | WP | proved (54/54) |
| remove_comma_item | option.c | WP | proved (37/37) |
| append_item | option.c | WP | proved (31/31) |
| prepend_item | option.c | WP | proved (26/26) |
| stropt_concat_with_comma | option.c | WP | upstream wrong from 2 GiB (finding); fixed fork version proved (45/45); upstream under 2 GiB: 1 goal open |
| valid_name | option.c | WP | proved (34/34) |
| check_option_listflag | optionstr.c | WP | proved (33/33) |
| find_key_len / string_to_key | option.c | - | open: bug found (reads past "<t_x"), fix 61856f2 not proved (needs find_special_key contract) |
| stropt_get_newval, stropt_expand_envvar | option.c | - | open: length casts fixed in 36f4ea6, not proved |
| stropt_remove_val | option.c | WP | open (needs a strcpy contract; `int len` from caller) |
| remove_key_item | option.c | WP | open |
| stropt_remove_dupflags | option.c | WP | open |
| stropt_handle_keymatch | option.c | WP | open |
| opt_strings_flags / opt_strings_check | optionstr.c | WP | open |
