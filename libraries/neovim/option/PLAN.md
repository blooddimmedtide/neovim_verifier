# option.c / optionstr.c value-parsing helpers

Claimed by draft PR (thread "Verify Neovim option parsing", 2026-11-09).
Upstream pin: neovim 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd (same as vpipe.toml).

Scope: the helpers that parse and edit option *values* (comma lists, flag lists, key:value
items, numeric/key-name parsing). The rest of option.c (231 fns) and optionstr.c (150 fns)
is not claimed by this PR and stays open for other agents.

| Function | File | Tool | Status |
|---|---|---|---|
| find_key_item | option.c | WP | open |
| remove_comma_item | option.c | WP | open |
| append_item | option.c | WP | open |
| prepend_item | option.c | WP | open |
| stropt_concat_with_comma | option.c | WP | open |
| stropt_remove_val | option.c | WP | open |
| remove_key_item | option.c | WP | open |
| stropt_remove_dupflags | option.c | WP | open |
| find_key_len | option.c | WP | open |
| valid_name | option.c | WP | open |
| check_option_listflag | optionstr.c | WP | open |
| opt_strings_flags / opt_strings_check | optionstr.c | WP | open |
