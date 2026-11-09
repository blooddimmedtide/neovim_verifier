# src/nvim/ex_cmds.c: substitute helpers (partial, 4 of 59 functions)

Pinned upstream: neovim/neovim 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd (see `../vpipe.toml`).
Fix: blooddimmedtide/verified_neovim branch `fix-check-regexp-delim-signed-char` (42c2ba8, based on
the pinned commit). Tool: CBMC 6.4.1, x86_64, run with signed and with unsigned `char`.
Status: candidate / fixed-candidate. No independent review yet; the owner's sign-off is needed.

## What is proved

| Function | Property | Evidence |
|---|---|---|
| `sub_parse_flags` | For every NUL-terminated string up to 8 bytes in an exact-size buffer, every starting flag state, both `'gdefault'` values: the flags, `which_pat` and the returned end pointer equal the reference in `cbmc/spec.h`; no read past the NUL; count-only never asks. | `cbmc/run_cbmc.sh` (upstream and fork), `cbmc/run_difftest.sh` (308,915,712 compiled cases, 0 differences) |
| `check_regexp_delim` | For every `c` that is `EOF` or 0..255: returns `FAIL` and gives E146 exactly once iff `c` is an ASCII letter (C locale), else `OK` with no message. | `cbmc/run_delim.sh` |
| `sub_set_replacement`, `sub_get_replacement` | Over two sets from the initial state: get returns exactly the value set; the previous string is freed; previous ShaDa data is freed iff the new value has a different pointer; no double free, no free of live data, no leak (`--memory-leak-check`). Precondition from the `@warning`: each new `sub.sub` is a fresh allocation or NULL, and `additional_data` is fresh, NULL or the stored one. | `cbmc/run_repl.sh` |
| call sites in `do_sub`, `ex_global` | The argument passed is always `EOF` or 0..255 (C11 7.4p1). **Fails upstream with signed char**; proved on the fork. | `cbmc/run_delim.sh` `h_call_sites` |

The reference (`spec.h`) is written from `:help s_flags` and `:help E146`, not from the code.
It decides itself that `n` turns `c` off, as `:help s_n` says count-only does not substitute.

## What it relies on
- The string-length bound (8 bytes) for `sub_parse_flags`: the loop body is the same for every
  position, and the difftest covers lengths up to 5 over the full flag alphabet exhaustively. This is
  a bounded proof, not an unbounded one; a WP proof would remove the bound.
- `check_regexp_delim` runs in the C locale (CBMC's `isalpha` model, glibc's table macro disabled
  with `__NO_CTYPE`). Neovim calls `setlocale(LC_CTYPE, "")`, so in a Latin-1 locale a byte such as
  0xE9 can count as a letter; that is outside this proof.
- `emsg` is a stub that records the message; `_()` is the identity.

## Finding
`findings/check-regexp-delim-signed-char.md`: upstream passes a negative `int` to `isalpha()` for
delimiter bytes >= 0x80 on signed-char platforms (undefined behavior). Fixed and proved on the fork.

## Planted bugs
22/22 caught (`cbmc/run_mutants.sh`; lists `cbmc/mutants.txt`, `cbmc/mutants_delim.txt`, `cbmc/mutants_repl.txt`).
Written by the prover, not an independent reviewer, so the review gate is still open.

## Still unverified in this file (55 functions)
Everything else in ex_cmds.c, including `skip_substitute` (depends on `utfc_ptr2len`, not yet
proved), `sub_joining_lines`, `sub_grow_buf`, `do_sub`, `string_compare`, `sort_compare`, `ex_sort`, `ex_uniq`, `linelen`,
`find_pipe` (Windows only), `show_sub`, `do_sub_msg`, `global_exe_one`, `ex_global`, `global_exe`.
