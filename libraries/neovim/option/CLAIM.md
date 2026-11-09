---
entry: neovim/src/nvim/option.c + optionstr.c (option-value helpers: comma lists, flag lists, key names)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
fixed_fork: https://github.com/blooddimmedtide/verified_neovim (branch claude/project-thread-33fn39: 36f4ea6 size_t lengths, 61856f2 string_to_key)
toolchain: Frama-C 33.0 (Arsenic) WP, Z3 + CVC5 via Why3 (Nix, tools/install.sh)
strength: in progress   # not a candidate yet: no mutants, no review, no unsigned-char run
platform: x86_64, char signed (Neovim's build). Unsigned-char run not done yet.
---

# Claim card: option-value helpers (work in progress)

Status per function is in `PLAN.md`. This card says what the proofs that pass actually show.

## What is proved (Frama-C WP, `-wp-rte -warn-signed-downcast`, Typed+Cast, no admits)

| Function | Property |
|---|---|
| `find_key_item(src, key, keylen, &len)` | NULL iff no item of the comma list `src` (an item starts at 0 or after a `,`) begins with the `keylen` bytes of `key`; else the first such item, with `*itemlenp` its length up to the next `,` or NUL. Writes only `*itemlenp`, and only when found |
| `remove_comma_item(str, item, itemlen)` | removes the item and the comma after it (or, for the last item, the comma before it); the result is the old string with those bytes cut out; an only item leaves the prefix and a NUL |
| `append_item(str, item, len)` | `str` becomes old `str`, then `,` if `str` was not empty, then the item, then NUL |
| `prepend_item(str, item, len)` | `str` becomes the item, then `,` and old `str` if it was not empty |
| `stropt_concat_with_comma` (fixed fork) | `+=`: origval (minus a trailing unescaped `,` for one-comma options), `,` when both are non-empty comma-list values, then newval; `^=`: newval, `,`, origval. Any length |
| `valid_name(val, allowed)` | true iff every byte of `val` is an ASCII letter or digit or a byte of `allowed` (allowed all ASCII) |
| `check_option_listflag(val, flags, errbuf)` | NULL iff every byte of `val` is one of `flags` (flags all ASCII); else a non-NULL error message |
| `stropt_concat_with_comma` (upstream) | wrong from 2 GiB (finding below). The proof with lengths <= INT_MAX has one open goal (OP_ADDING ensures, timeout) |

The references are written from the doc comments (quoted in `wp/contracts.py`), as comma-list
predicates (`item_start`, `key_at`, `item_end`), not from the code.

Each run also passes `-wp-smoke-tests` (93/93: no stub or precondition set was found
contradictory). The stubs here are new; the garray allocation stubs are not used.

## What the proofs rely on (trusted, all in wp/stubs)

- C library: `strlen`, `strncmp`, `memmove` contracts from C11 (`memory/wp/stubs/vp_string.h`).
- `vim_strchr` (strings.c): strchr for ASCII c; for c >= 0x80, "not found" in an all-ASCII string
  (it searches for the UTF-8 encoding of c, whose lead byte is >= 0xC2). Not proved here.
- `illegal_char` (optionstr.c): returns non-NULL, writes only `errbuf->data`.
- Preconditions each caller meets: strings are NUL-terminated; `key` has no NUL in its first
  `keylen` bytes; the item passed to append/prepend does not overlap the target buffer (callers
  pass a copy, `newval_copy`); the buffer has room (stropt_get_newval allocates origval + arg).

## Findings

1. `findings/option-concat-over-2gib.md`: `:set opt+=x` with a value of 2 GiB or more corrupts
   memory (`int len = (int)strlen(origval)`); same class in `stropt_get_newval` and
   `stropt_expand_envvar` (uint32_t sum). Reproduced at function level; fix 36f4ea6, fixed
   `stropt_concat_with_comma` proved.
2. `findings/option-string-to-key-t-x.md`: `:set cedit=<t_x` reads one byte past the value
   (`find_key_len`). Reproduced at function level with ASan; fix 61856f2, not proved yet.

## Not done yet

Mutants, adversarial review, unsigned-char run, differential test, CI target, end-to-end
reproduction in a built nvim.
