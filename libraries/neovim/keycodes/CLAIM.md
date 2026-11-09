---
entry: neovim/src/nvim/keycodes.c (key-notation helpers)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
fixed_fork: https://github.com/blooddimmedtide/verified_neovim (branch claude/project-thread-vh5tc9, commit 4c94621)
toolchain: Frama-C 33 WP with Z3 + CVC5, CBMC 6 (pipeline toolchain, Nix); LuaJIT for Neovim's gen_keycodes.lua
strength: candidate (partial file: 9 of 17 functions proved, see below)
platform: x86_64, char signed (Neovim's build) and unsigned (machdep_x86_64_uchar.yaml)
---

# Claim card: Neovim keycodes.c

Work stopped at the 09:00 UTC deadline on 2026-11-09. **The file is not finished.**

## Proved with Frama-C WP (every goal, RTE guards, smoke tests on, no admits/axioms)

`keycodes/wp/run_wp.sh`, signed and unsigned char.

| Function | Property |
|---|---|
| `name_to_mod_mask(c)` | the documented modifier bit for the letter (case-insensitive): M/A Alt, T Meta, C Ctrl, S Shift, 2/3/4 click, D Cmd; 0 for anything else |
| `handle_x_keys(key)` | each of the 16 xterm keys maps to its plain key (`<xUp>` to `<Up>`, `<zHome>` to `<Home>`, `<S-xF1>` to `<S-F1>`...); every other key unchanged |
| `get_mouse_button(code, ...)` | for a code in the mouse table, the first entry's button and click/drag flags; otherwise 0 and the flags untouched |
| `extract_modifiers(key, ...)` | Shift on a letter gives the upper-case letter (Shift kept only with Ctrl); Ctrl on a letter uses the upper-case letter; with `simplify`, Ctrl on `?`..`_` or a letter gives the control character (Ctrl-@ is K_ZERO), Ctrl removed and `*did_simplify` set |

Smoke tests: 4 statements in `extract_modifiers` are reported unreachable. They are branches of
`TOUPPER_ASC` (the `c > 'z'` / `c - 32` arms) where the key is already known to be a letter or
upper case; run_wp.sh allows exactly these 4 and nothing else. Preconditions: valid separated
pointers; `mt_ok` (mouse table terminator at index 17; the table is never written).

## Proved with CBMC (every int input; loops fully unwound with unwinding assertions)

`keycodes/cbmc/run_cbmc.sh` and `keycodes/table/run_cbmc.sh`, signed and unsigned char, with
bounds, pointer, signed-overflow and shift checks.

| Function | Property |
|---|---|
| `simplify_key(key, &m)` | no Shift/Ctrl: unchanged; Shift-Tab: K_S_TAB, Shift removed; else the first table entry whose unshifted code is the key and whose modifier meets m gives the shifted code with that modifier removed; else unchanged. Precondition `key != INT_MIN` (finding) |
| `unsimplify_key(c, &m)` | the inverse lookup: non-special keys unchanged; the first entry whose shifted code is c gives the unshifted code with its modifier added. Precondition `c != INT_MIN` |
| `add_char2buf(c, s)` | writes the UTF-8 bytes of c (verbatim `utf_char2bytes` linked in) with each K_SPECIAL byte as K_SPECIAL KS_SPECIAL KE_FILLER, at most 18 bytes, returns the end |
| `special_to_buf(key, mods, esc, dst)` | K_SPECIAL KS_MODIFIER mods when mods != 0, then K_SPECIAL + the two termcap bytes for a special key, else the (escaped if esc) UTF-8 bytes; returns the length; at most 21 bytes. Precondition `key != INT_MIN` (finding) |
| `find_special_key_in_table(c)` | the index of the first preferred (not alternative) entry of the generated `key_names_table` with key c, else -1 |

Table references share the table data with the code but not the search logic. Planted bugs:
WP 12/12 non-equivalent caught (2 equivalent mutants noted in wp/mutants.sh), CBMC 10/10.
No independent review yet.

## Not proved yet (blocks completion)

| Function | State |
|---|---|
| `get_special_key_code` | CBMC harness written (all names up to 17 bytes, `table/run_cbmc.sh <tree> 17`); a 25-minute run timed out |
| `vim_unescape_ks` | full functional WP contract written (recursive `outlen`/`outbyte`); WP times out on the `char *` / `uint8_t *` casts. Try CBMC on bounded strings plus a WP length argument |
| `find_special_key` | INT_MIN property only (never hands INT_MIN to simplify_key, never returns it), upstream vs fix: `fsk/run_cbmc.sh`, callees stubbed by over-approximation; runs still going at the deadline. Full functional spec not written |
| `trans_special`, `replace_termcodes`, `get_special_key`, `get_special_key_name`, `vim_strsave_escape_ks` | not started (depend on `vim_str2nr`, `utfc_ptr2len*`, `utf_ptr2char`, `transchar`, `get_var_value`, `xmalloc`, `vim_isprintc`) |

## Finding

`findings/keycodes-char-int-min.md`: `<Char-N>` with N >= 2^31 becomes a negative (special)
key code, and N = 0x80000000 makes `special_to_buf` / `simplify_key` negate INT_MIN (UBSan
confirmed on the extracted lines). Fix pushed to the fork; its proof needs
`find_special_key`, so it is a `fixed-candidate`, not a verified fix.
