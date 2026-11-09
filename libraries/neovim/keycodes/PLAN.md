# keycodes.c (claimed 2026-11-09)

Pinned upstream: neovim 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd, src/nvim/keycodes.c (17 functions).
Tool: Frama-C WP (loops over unbounded strings), CBMC for bounded byte helpers.

| function | status |
|---|---|
| name_to_mod_mask | open |
| simplify_key | open |
| unsimplify_key | open |
| handle_x_keys | open |
| get_special_key | open |
| get_special_key_name | open |
| trans_special | open |
| special_to_buf | open |
| find_special_key | open |
| extract_modifiers | open |
| find_special_key_in_table | open |
| get_special_key_code | open |
| get_mouse_button | open |
| replace_termcodes | open |
| add_char2buf | open |
| vim_strsave_escape_ks | open |
| vim_unescape_ks | open |
