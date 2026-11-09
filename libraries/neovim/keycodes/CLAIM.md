---
entry: neovim/src/nvim/keycodes.c (key-notation helpers)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
fixed_fork: https://github.com/blooddimmedtide/verified_neovim (branch claude/project-thread-vh5tc9, commit 4c94621)
toolchain: Frama-C 33 WP with Z3 + CVC5 (pipeline toolchain, Nix)
strength: candidate (partial file: 4 of 17 functions proved, see below)
platform: x86_64, char signed (Neovim's build) and unsigned (machdep_x86_64_uchar.yaml)
---

# Claim card: Neovim keycodes.c

Work stopped at the 09:00 UTC deadline on 2026-11-09. **The file is not finished.**

## Proved (Frama-C WP, every goal, RTE guards on, no admits/axioms)

| Function | Property |
|---|---|
| `name_to_mod_mask(c)` | the documented modifier bit for the letter (case-insensitive): M/A Alt, T Meta, C Ctrl, S Shift, 2/3/4 click, D Cmd; 0 for anything else |
| `handle_x_keys(key)` | each of the 16 xterm keys maps to its plain key (`<xUp>` to `<Up>`, `<zHome>` to `<Home>`, `<S-xF1>` to `<S-F1>`...); every other key unchanged |
| `get_mouse_button(code, ...)` | for a code in the mouse table, the first entry's button and click/drag flags; otherwise 0 and the flags untouched |
| `extract_modifiers(key, ...)` | Shift on a letter gives the upper-case letter (Shift kept only with Ctrl); Ctrl on a letter uses the upper-case letter; with `simplify`, Ctrl on `?`..`_` or a letter gives the control character (Ctrl-@ is K_ZERO), Ctrl removed and `*did_simplify` set |

Table lookups are specified as "the first matching table entry, else unchanged", not by
restating the tables. The tables and functions are copied verbatim (sha256 pinned in
`wp/build.py`); the prelude's macros are each checked against the pinned headers.
Preconditions: valid, separated pointers; table well-formedness predicate `mt_ok`
(terminator at index 17, the tables are never written).

## Not proved yet (blocks completion)

| Function | State |
|---|---|
| `simplify_key`, `unsimplify_key` | contracts written; 56/61 and 42/47 goals; open: `TERMCAP2KEY` shift overflow goals and the table postcondition (solver timeouts). Needs `key != INT_MIN` (finding below) |
| `vim_unescape_ks` | full functional contract written (recursive `outlen`/`outbyte`); WP times out on the `char *` / `uint8_t *` casts |
| `special_to_buf`, `add_char2buf` | contracts drafted, not run; depend on `utf_char2bytes` (CBMC candidate in mbyte/) |
| `find_special_key`, `trans_special`, `replace_termcodes`, `get_special_key`, `get_special_key_name`, `find_special_key_in_table`, `get_special_key_code`, `vim_strsave_escape_ks` | not started (depend on generated `key_names_table`, `vim_str2nr`, `utfc_ptr2len*`, `transchar`, `get_var_value`, `xmalloc`) |

## Finding

`findings/keycodes-char-int-min.md`: `<Char-N>` with N >= 2^31 becomes a negative (special)
key code, and N = 0x80000000 makes `special_to_buf` / `simplify_key` negate INT_MIN (UBSan
confirmed on the extracted lines). Fix pushed to the fork; its proof needs
`find_special_key`, so it is a `fixed-candidate`, not a verified fix.
