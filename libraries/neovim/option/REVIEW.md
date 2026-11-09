# Adversarial review: option.c / optionstr.c value helpers (WP)

Reviewer: independent agent (not the author), 2026-11-09. Read: AGENTS.md, CLAIM.md, PLAN.md,
`wp/contracts.py`, `wp/build.py`, `wp/stubs/vp_option.h`, `memory/wp/stubs/vp_string.h`, the C
in `verified_neovim` (fixed fork) and the callers in option.c / optionstr.c. Nothing in
contracts, stubs or sources was edited.

## Verdict: accept with changes

The contracts are functional and are written as comma-list predicates rather than by copying
the code. All planted bugs I ran were caught (table below). The main problem is one stub frame
clause that is false, plus a few gaps in what the claim states. None of them lets WP prove a
false functional result for these seven functions.

## Per function

### find_key_item
- Matches the doc comment: NULL iff no item start has the `keylen` bytes; otherwise the
  *first* match, `*itemlenp` up to `,`/NUL, and `assigns \nothing` when not found. Good.
- Preconditions are met by the callers. `stropt_handle_keymatch` uses `keylen = colon - item_start + 1`
  inside a NUL-free item of `newval_copy`. `remove_key_item` passes `next`, a suffix of `str`, and
  `itemlenp` is a local, so it is separate from `src`.
- Note (code, not contract): `find_key_item` and `remove_comma_item` treat every `,` as a
  separator. `find_dup_item` (used on the non-colon path of the same caller) skips
  backslash-escaped commas (`\,`). So a value such as `x\,a:1` gives different item boundaries
  on the two paths. Neither the doc nor the contract covers escaping. This should be listed in
  CLAIM.md as "escaping not modelled"; it may also be worth its own finding.

### remove_comma_item
- `inner`, `last` and `only` together give the whole new string (prefix kept, suffix shifted,
  NUL). Good.
- The precondition asks for `item_end` but not `item_start`. That is weaker than it needs to be,
  which is fine. The callers meet it: `find_key_item` ensures `item_end`, and `find_dup_item`
  with `kOptFlagComma` checks `s[len] == ','` or NUL on a NUL- and comma-free item.
- Weak spot: `only` also covers an item that does not start at an item boundary
  (`item > str && item[-1] != ','`). In that case the string is cut in the middle of an item.
  That is the code's real behaviour, but no caller needs it. Suggested: add
  `requires item_start(str, item - str)`, or note in CLAIM.md that the contract describes this case.
- `assigns str[0 .. n]` could be tighter (`item - 1 .. n`). The `\forall` prefix ensures already
  cover it.

### append_item / prepend_item
- These match the doc comments exactly, NUL included (prepend's `j <= n`).
- The room precondition asks for one byte more than the empty case writes (`n + 1 + item_len`).
  That is harmless. The caller (`stropt_handle_keymatch`) must meet
  `|result| + 1 + item_len < newlen = |origval| + |arg| + 2`, but that caller is still open, so
  this obligation is not proved anywhere yet. The claim card already lists it as a caller
  assumption. Keep it there until `stropt_handle_keymatch` is proved.

### stropt_concat_with_comma (fixed)
- The size precondition `newval[0 .. no + nn + 1]` is exactly the `stropt_get_newval` allocation
  (`strlen(s) + 1 + strlen(origval) + 1`). It is only called for `OP_ADDING` / `OP_PREPENDING`,
  so the `op != OP_ADDING` behaviour is the prepend case. Good.
- `kept_len` restates the code's trailing-comma condition (`o[no-2] != '\\'`) rather than an
  independent rule. An escaped backslash (`a\\,`) is therefore not stripped, and the spec agrees
  with the code. That is acceptable only because the doc comment is that same one-line rule. The
  claim should say so.

### valid_name
- Matches the doc ("only alphanumeric ASCII or characters in allowed"). `allowed` is ASCII at
  both callers (`".-_"` in optionstr.c, `".-_,@"` in spell.c). Bytes >= 0x80 are rejected both in
  the spec and in the code.

### check_option_listflag
- The NULL/non-NULL result matches the doc. All 6 callers pass ASCII `flags` (COCU_ALL, CPO_VI,
  FO_ALL, MOUSE_ALL, SHM_ALL, WW_ALL ",").
- **Wrong frame (required fix).** The `illegal_char` stub says `assigns errbuf->data[..]` only.
  The real function calls `transchar(c)`, which writes the static `transchar_charbuf[11]`
  (charset.c:433-467), and `opt_error` formats into `errbuf`. So the proved
  `assigns errbuf->data[0 .. size-1]` of `check_option_listflag` is false about memory. It is
  harmless for the result property, but a caller that relies on "writes nothing else" would be
  unsound. The stub (and the contract) need a ghost global for the transchar buffer, or must
  `assigns` it.

## Stubs
- `vim_strchr`: `requires 0 < c` is stronger than the real function, which returns NULL for
  `c <= 0`. That is conservative, so it is sound. For `c >= 0x80` the "not found in an ASCII
  string" argument is right: `utf_char2bytes` of 0x80..0xFF has lead byte 0xC2/0xC3, and
  `strstr` cannot match it in an ASCII string. The `found` case is C11 strchr (first
  occurrence, no NUL before it). OK.
- `illegal_char`: frame is incomplete (see above). "Never NULL" is right (`""` or
  `opt_error`'s buffer).
- `strncmp`/`memmove`/`strlen` (vp_string.h): C11 contracts. `key_prefix` bridges strncmp's
  NUL clause using the "key has no NUL" precondition. OK.

## Soundness risks (not defects, list them in CLAIM.md)
- `-wp-model Typed+Cast` handles pointer casts heuristically. Here the only pointer casts drop
  `const` (`(char *)str`) on same-type objects, which is safe. Keep the code free of `char` ↔
  `uint8_t` pointer casts for this target.
- The unsigned-char run is still missing. `(char)c` comparisons in the stubs depend on how
  `char` is signed.

## Required changes
1. Fix the `illegal_char` stub frame: add the `transchar_charbuf` write, using a ghost global if
   needed, and carry it into `check_option_listflag`'s `assigns`.
2. CLAIM.md: say that backslash-escaped commas are not modelled: `find_key_item` and
   `remove_comma_item` split on every `,`, unlike `find_dup_item`. Also say that `kept_len`
   mirrors the code's one-backslash rule.
3. CLAIM.md: list the buffer-room precondition of append/prepend as unproved until
   `stropt_handle_keymatch` is verified.
4. (Recommended) `remove_comma_item`: add `requires item_start(str, item - str)`, or document
   that the `only` case cuts mid-item.

## Planted bugs (mutants.toml, `run_mutants.py /home/user/verified_neovim 20`)

Before the WP runs, I built and Frama-C-parsed every mutant (`build.py` with VP_MUTANT=1, then
`frama-c opt.c`). All 23 build and parse, and no anchor line is touched. So a "caught" below is
a failed proof, not a build error.

Run on 2026-11-09, 08:21–08:33 UTC, in two batches, with one frama-c job at a time.
**Result: 23 of 23 caught, 0 missed.**

| Function | Mutants | Result |
|---|---|---|
| find_key_item | fki-1 (no item-start check), fki-2 (keylen-1), fki-3 (last-item len-1) | all caught |
| remove_comma_item | rci-1 (last: +1 past NUL), rci-2 (reads str[-1]), rci-3 (only: truncates after item) | all caught |
| append_item | ai-1 (comma on empty), ai-2 (item_len-1), ai-3 (`str[++len]`) | all caught |
| prepend_item | pi-1 (no NUL moved), pi-2 (comma one late), pi-3 (always comma) | all caught |
| stropt_concat_with_comma | sc-1 (escaped comma stripped), sc-2 (no NUL moved), sc-3 (gap on prepend), sc-4 (comma with empty newval), sc-5 (`len > 0`) | all caught |
| valid_name | vn-1 (digits rejected), vn-2 (inverted lookup), vn-3 (empty invalid) | all caught |
| check_option_listflag | col-1 (inverted), col-2 (skips first flag), col-3 (first byte unchecked) | all caught |

No mutant was missed, so these runs show no missing functional property. Changes 1–3 above are
about the trusted frame and what the claim states; the mutants cannot detect those.
