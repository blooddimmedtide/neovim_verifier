---
entry: neovim/src/nvim/charset.c (25 of 57 functions so far: skip/scan helpers, hex helpers, backslash halving, the getdigits family, vim_str2nr; plus the 5 ascii_defs.h helpers they call)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
fixed_fork: https://github.com/blooddimmedtide/verified_neovim branch claude/project-thread-yx7abl (vim_str2nr, commit 213eb11)
toolchain: Frama-C 33.0 WP, Why3, Z3, CVC5 with --full-saturate-quant (tools/install.sh, tools/bin/cvc5-fsq); CBMC 6.4.1 for the tool-patch check; z3-solver for bit lemmas
container: ubuntu:24.04@sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac (CI)
strength: candidate   # becomes full-correctness after the review and the owner's spec sign-off
tools: Frama-C WP (deductive, unbounded: every length, every input), Typed+Cast memory model, -wp-rte
platform: Linux x86_64 (machdep x86_64, BACKSLASH_IN_FILENAME undefined); signed and unsigned char (differential test runs both)
---

# Claim card: Neovim charset.c string helpers (work in progress)

charset.c has 57 functions. This card covers the 25 below; the other 32 are open (list at the end).

`wp/build.py` copies the exact upstream text of each function (sha256 pinned) and adds ACSL
as comments only: contracts, loop invariants, assertions, ghost statements and, for 14
functions, a ghost parameter naming the length of a string argument. Two functions,
`backslash_halve` and `vim_str2nr`, also get declared tool patches (below). The build checks that removing
the comments gives back the upstream (or patched) text. Nothing is admitted; no axioms.

## What is proved, for every input

"String of length n" = n readable non-NUL bytes followed by a readable NUL (`str_len`).
"White" = space (32) or TAB (9). Classes use ASCII codes, not the code's own helpers.

| Function | Property |
|---|---|
| `ascii_iswhite/isdigit/isxdigit/isbdigit/isodigit(c)` (ascii_defs.h) | true exactly for space/TAB, `0`-`9`, hex digits, `0`/`1`, `0`-`7`; every int |
| `nr2hex(n)` | the lower-case hex digit of `n % 16`; every unsigned |
| `skipwhite(p)` | pointer past the leading run of white bytes |
| `skipwhite_len(p, len)` | pointer past the leading white run, at most `len` bytes; reads nothing past the first non-white byte or `p[len-1]` |
| `getwhitecols(p)` | length of the leading white run |
| `skipdigits` / `skipbin` / `skiphex(q)` | pointer past the leading run of decimal / binary / hex digits |
| `skiptodigit` / `skiptobin` / `skiptohex(q)` | pointer to the first decimal / binary / hex digit, else to the NUL |
| `skiptowhite(p)` | pointer to the first space, TAB or NUL |
| `skiptowhite_esc(p)` | walking from p, a backslash or Ctrl-V followed by a non-NUL byte is a 2-byte step, anything else 1; result is the first step position holding a space, TAB or NUL (`ewpos`) |
| `skip_to_newline(p)` | pointer to the first LF or NUL |
| `vim_isblankline(lbuf)` | true iff the first non-white byte is NUL, CR or LF |
| `hex2nr(c)` | the value of a hex digit (its documented domain); no undefined behavior for any `c >= INT_MIN + 48` (every char) |
| `hexhex2nr(p)` | `16 * hex(p[0]) + hex(p[1])` when both are hex digits, else -1; reads `p[1]` only if `p[0]` is one |
| `rem_backslash(str)` | true iff `str[0]` is a backslash and `str[1]` is not NUL (Unix build) |
| `backslash_halve(p)` | rewrites the string in place: a backslash followed by a non-NUL byte becomes that byte, everything else is kept, then NUL (`bpos`/`bchar` define output byte k); writes only `p[0..n]` |
| `backslash_halve_save(p)` | same output in a new allocation of `n + 1` bytes; input unchanged; exactly one allocation (ghost counter) |
| `try_getdigits(pp, nr)` | the C standard's `strtoimax(*pp, pp, 10)` subject sequence (leading white space, optional sign, decimal digits): with no digits `*nr = 0`, `*pp` unchanged, true; else `*pp` moves past the digits, `*nr` is the value clamped to `intmax_t`, and the result is false exactly when it was clamped |
| `getdigits(pp, strict, def)` | the number, 0 without digits, `def` when out of range; `*pp` as above |
| `getdigits_int` / `getdigits_long` / `getdigits_int32` | as `getdigits`, with `def` also when the value is outside `int` / `long` / `int32_t` |
| `vim_str2nr(start, prep, len, what, nptr, unptr, maxlen, strict, overflow)` | an optional `-`, then the base: forced by `what` (`STR2NR_FORCE`), else the first of `0x`/`0X` + hex digit, `0b`/`0B` + binary digit, `0o`/`0O` + octal digit, or `0` + an octal digit with no `8`/`9` in the following decimal run, that `what` allows (`cls`); then the longest run of digits of that base, where with `STR2NR_QUOTE` a `'` between two digits is skipped (`dp`, `ndig`); only bytes before `maxlen` are looked at (no limit when 0). Results: if `strict` and the next byte is a letter or digit, nothing is written except `*len = 0`; else `*len` = characters used, `*prep` = the prefix character (`x`, `X`, `b`, `B`, `o`, `O`, `0` for old octal, 0 otherwise), `*unptr` = the value saturated at 2^64-1 (also capped at 2^63-1 when `nptr` is given and there is no `-`), `*nptr` = the signed value saturated at the `varnumber_T` range, `*prep` is 0 when the base is forced, and `*overflow` is set to true when a saturation happened, else left unchanged. Upstream: proved for numbers shorter than 2^31-1 characters when `maxlen == 0` (the bug below); the fork's fix: for every input |

All functions: no undefined behavior (`-wp-rte`: every memory access valid, no signed
overflow, no invalid conversion) and they terminate (loop variants).

## What the proof relies on

1. **Frama-C WP, Why3 and the provers are sound** (Z3, CVC5); **CBMC** for the tool-patch check.
2. **The C library meets `wp/stubs/vp_string.h`** (copied from memory/; only `strlen` is used here).
3. **xmalloc meets `wp/stubs/nvim/memory.h`**: base64's stub plus one spelled-out freshness
   fact, because WP ignores `\fresh`: the new block does not overlap a readable object the
   caller names (a ghost argument; here the input string). True of every allocator.
4. **xstrchrnul meets its contract**: `skip_to_newline` calls it; that exact contract text is
   imported from `memory/wp/contracts.py` and proved there.
5. **Bit lemmas** (`wp/lemmas.py`): `x & 15 == x % 16` (0 <= x < 2^32), `x << 4 == 16 x`
   (0 <= x <= 15), `x & 0xFFFFFF0F == x & 15` (0 <= x <= 255), and for a, b in {0, 1}
   `a & b == a * b`, `a | b == a + b - a * b`; checked with Z3 bit-vectors by the same script
   that prints them.
6. **Tool patch `backslash_halve_goto`** (`wp/tool_patches.py`): WP rejects the upstream
   `goto start;` into the loop body (a non-natural loop). The patch replaces the goto with a
   copy of the two statements at the label; afterwards control reaches the loop condition in
   both versions. `equiv/run_equiv.sh` checks with CBMC (no assumptions) that both versions
   leave identical bytes for every buffer of 12 bytes plus NUL, i.e. every string of length
   <= 12, with signed and unsigned char. For longer strings the argument is the one above
   (the patch changes only where the first loop iteration starts), not a machine check.
6b. **Tool patches for `vim_str2nr`** (`wp/tool_patches.py`): WP copies the rest of the
   function for every way out of a condition that jumps, and C's `&&` / `||` become such
   conditions, so the goal for one postcondition was 17.8 million lines. The patch (a)
   expands the `PARSE_NUMBER` macro, (b) rewrites `&&` / `||` between side-effect-free
   comparisons to `&` / `|` (same value, both sides evaluated), and (c) moves each of the
   four digit loops into `vp_parse_<base>` and the result-writing tail into `vp_finish`,
   unchanged, passing the locals by pointer or value. `equiv/run_equiv.sh` checks with CBMC
   that patched and original store the same results (every output, including which are
   left unchanged) for every string of length <= 6, every
   `maxlen` from 0 to 6, every one of the 44 `what` values the precondition allows,
   both `strict` values, and every mix of NULL and non-NULL outputs; upstream and fixed,
   signed and unsigned char. For longer strings the argument is that the patch moves code
   without changing it (the digit loops and the tail) and swaps `&&` for `&` only where
   both sides are side-effect-free comparisons; that part is not a machine check.
7. **Preconditions**: documented in each contract. Strings must be NUL-terminated
   (`FUNC_ATTR_NONNULL_ALL` and the doc comments); `skipwhite_len` needs `p[0..len-1]`
   readable up to the first non-white byte; `hexhex2nr` / `rem_backslash` need `p[0]`, and
   `p[1]` when the first byte asks for it; `hex2nr`: `c >= INT_MIN + 48`;
   `backslash_halve_save`: `n < PTRDIFF_MAX` (no larger object exists on x86_64).
   getdigits family with `strict`: the number is in range (otherwise the code calls `abort()`,
   or `assert` for the narrow variants; see the observation below).
   `vim_str2nr`: `what` is a set of `STR2NR_*` flags (0..255, bits 32 and 64 clear; every
   caller), and with `STR2NR_FORCE` names one base (else the code calls `abort()`); the
   string is readable up to `maxlen` or NUL-terminated; outputs do not overlap each other or
   the string. Upstream only: with `maxlen == 0` the string is shorter than 2^31-1.
9. **strtoimax meets `wp/stubs/vp_strtoimax.h`** (base 10 only): the C standard's description,
   written as logic (`subj`, `sdigits`, `svalue`): `*endptr`, the clamped value and `ERANGE`.
   errno is modelled as one global (`vp_errno`).
8. **Ghost length parameters** (14 functions): notation for "for every string of length n"
   (a string has one length, `str_len_unique`); callers pass nothing.

## Not covered yet (37 functions, all open)

`buf_init_isk_chartab`, `init_isf_chartab`, `init_isi_chartab`, `check_isopt`, `parse_isopt`,
`trans_characters`, `transstr_len`, `transstr_buf`, `transstr`, `kv_transstr`, `str_foldcase`,
`transchar`, `transchar_buf`, `transchar_byte`, `transchar_byte_buf`, `transchar_nonprint`,
`transchar_hex`, `rl_mirror_ascii`, `char2cells`, `vim_strsize`, `vim_strnsize`, `vim_isIDc`,
`vim_iswordc`, `vim_iswordc_tab`, `vim_iswordc_buf`, `vim_iswordp`, `vim_iswordp_buf`,
`vim_isfilec`, `vim_is_fname_char`, `vim_isfilec_or_wc`, `vim_isprintc`,
`getwhitecols_curline`, plus the Windows variant of `rem_backslash`.
Independent review and planted bugs: pending. Owner sign-off: pending.

## Findings

- **Bug, `vim_str2nr`**: with no `maxlen`, a number of 2^31 characters or more gives a negative
  or too short `*len`, and the old-octal check overflows `int i` (undefined behavior).
  `eval_number` then moves the parse pointer backwards. Write-up and reproducer:
  `../findings/str2nr-over-2gib.md`. Fix on the fork (`verified_neovim`): with `maxlen == 0`
  the scan stops at `INT_MAX` characters; proved for every input (Evidence). Upstream issue:
  drafted, not filed.

Observations (behavior as written, not bugs):

- `getdigits_int` / `getdigits_int32` with `strict` and an out-of-range value: the range
  check is an `assert`, so in Release builds (`NDEBUG`) the value is silently truncated
  instead of aborting. The contract makes "in range" a precondition for `strict`.

## Evidence

| Check | Command | Result |
|---|---|---|
| Bit lemmas | `python3 -I wp/lemmas.py` | 5/5 proved (Z3 bit-vectors) |
| WP, upstream | `bash wp/run_wp.sh <nvim> 60` | every goal proved, 25 functions + 5 ascii_defs.h helpers + 5 vim_str2nr tool-patch helpers, one run each (vim_str2nr 419/419) |
| WP, fixed fork | `bash wp/run_wp.sh <fork> 60 --fixed vp_parse_bin vp_parse_oct vp_parse_dec vp_parse_hex vp_finish vim_str2nr` | every goal proved, no length limit (vim_str2nr 410/410, helpers 47/55/55/57/33) |
| Tool patch equivalence | `bash equiv/run_equiv.sh <nvim> 12` | backslash_halve: VERIFICATION SUCCESSFUL, signed and unsigned char; vim_str2nr: VERIFICATION SUCCESSFUL, upstream and fixed, signed and unsigned char (strings of length <= 6) |
| Differential test (gcc -O2, glibc, ASan/UBSan, signed and unsigned char) | `bash difftest/run_difftest.sh <nvim> 2000000` | 34,012,119 checks each, 0 mismatches |
| Independent review | | pending |
| Planted bugs | | pending (reviewer's choice) |
| CI, pinned container | `.github/workflows/verify.yml` | pending |
