---
entry: neovim/src/nvim/menu.c (menu name helpers)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
toolchain: CBMC 6.4.1 (.deb, see tools/install.sh)
strength: candidate, BOUNDED   # strings shorter than N bytes (default N = 12); not yet full-correctness
tools: CBMC 6.4.1 (every loop fully unwound, proved by unwinding assertions)
platform: x86_64, char signed and unsigned (both proved)
---

# Claim card: Neovim menu.c name helpers (work in progress, 8 of 43 functions)

Run: `bash menu/cbmc/run_cbmc.sh <neovim checkout>`. Code is extracted verbatim by
`menu/cbmc/build.py`, sha256 pinned per function (`pins.txt`). References are in `spec.h`.

## What is proved (every NUL-terminated string of length < N = 12, exact-size allocation, so any read past the NUL fails)

| Function | Property |
|---|---|
| `menu_is_winbar(s)` | true iff s starts with "WinBar" |
| `menu_is_popup(s)` | true iff s starts with "PopUp" |
| `menu_is_toolbar(s)` | true iff s starts with "ToolBar" |
| `menu_is_menubar(s)` | true iff s is not PopUp/ToolBar/WinBar-prefixed and does not start with `]` |
| `menu_is_separator(s)` | true iff s is non-empty and starts and ends with `-` (no read before s on "") |
| `menu_is_hidden(s)` | true iff s starts with `]`, or starts with "PopUp" and is longer than 5 bytes |
| `menu_namecmp(a, b)` | true iff the parts of a and b before the first NUL or TAB are equal |
| `menu_skip_part(p)` | returns p + the end of the first path element: stops at NUL, `.`, space or tab, where `\x` or `^Vx` (x not NUL) is one escaped unit |

No undefined behaviour, no out-of-bounds read, no overflow for these inputs.

## Limits (why this is not done)

- **Bounded**: strings are shorter than N = 12 bytes (at most 11 bytes). `menu_namecmp`, `menu_skip_part` and
  `menu_is_separator` loop over unbounded data; a WP proof (or a CBMC proof with a larger N
  plus an argument) is still needed for full correctness. The `ToolBar`/8 mutant shows the bound
  matters: it differs only on strings of 8+ bytes.
- Planted bugs: 10/10 caught at N = 12 (menu/cbmc/mutants_result.txt; self-written, not an independent review).
- No differential test and no independent adversarial review yet (stopped at the 09:00 UTC
  deadline on 2026-11-09).
- No bug found in these 8 functions.

## Still unverified (35 of 43)

ex_menu, add_menu_path, menu_enable_recurse, remove_menu, free_menu, free_menu_string,
menu_get_recursive, menu_get, find_menu, show_menus, show_menus_recursive,
set_context_in_menu_cmd, get_menu_name, get_menu_names, menu_name_skip, menu_name_equal,
get_menu_cmd_modes, get_menu_mode_str, popup_mode_name, menu_text, get_menu_mode,
get_menu_mode_flag, show_popupmenu, execute_menu, menu_getbyname, ex_emenu, menu_find,
ex_menutranslate, menutrans_lookup, menu_unescape_name, menu_translate_tab_and_shift,
menuitem_getinfo, f_menu_info, get_root_menu, is_menus_locked.
