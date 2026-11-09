# keycodes.c (claimed 2026-11-09)

Pinned upstream: neovim 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd, src/nvim/keycodes.c (17 functions).
Tool: Frama-C WP (loops over unbounded strings), CBMC for bounded byte helpers.

| function | status |
|---|---|
| name_to_mod_mask | proved (WP), signed+unsigned char |
| simplify_key | contract written, 56/61 goals; needs key != INT_MIN (finding) |
| unsimplify_key | contract written, 42/47 goals |
| handle_x_keys | proved (WP), signed+unsigned char |
| get_special_key | open |
| get_special_key_name | open |
| trans_special | open |
| special_to_buf | contract drafted, not run; INT_MIN finding |
| find_special_key | open; finding keycodes-char-int-min (fix on fork 4c94621, unproved) |
| extract_modifiers | proved (WP), signed+unsigned char |
| find_special_key_in_table | open |
| get_special_key_code | open |
| get_mouse_button | proved (WP), signed+unsigned char |
| replace_termcodes | open |
| add_char2buf | contract drafted, not run |
| vim_strsave_escape_ks | open |
| vim_unescape_ks | contract written; WP times out on pointer casts |
