---
entry: neovim/src/nvim/strings.c (12 of 74 functions so far: upper-case copies, xstrnsave, concat_str, has_non_ascii*, del_trailing_spaces, vim_strnicmp_asc; plus ascii_iswhite)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
fixed_fork: none needed so far
toolchain: Frama-C 33.0 WP, Why3, Z3, CVC5 with --full-saturate-quant (tools/install.sh, tools/bin/cvc5-fsq)
container: ubuntu:24.04@sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac (CI)
strength: candidate   # becomes full-correctness after the review and the owner's spec sign-off
tools: Frama-C WP (deductive, unbounded: every length, every input), Typed+Cast memory model, -wp-rte
platform: Linux x86_64 (machdep x86_64); signed and unsigned char (differential test runs both)
---

# Claim card: Neovim strings.c string helpers (work in progress)

strings.c has 74 functions. This card covers the 12 below; the other 62 are open (list at the end).
Same method as `charset/`: `wp/build.py` copies the exact upstream text (sha256 pinned) and
adds ACSL as comments only (contracts, loop annotations, assertions, ghost statements, ghost
length parameters); removing them gives back the upstream text (checked). No admits, no axioms.

## What is proved, for every input

"up(c)" = c - 32 for 'a'..'z', else c. "low(c)" = c + 32 for 'A'..'Z', else c (on char values).

| Function | Property |
|---|---|
| `xstrnsave(s, len)` | new block of `len + 1` bytes: the bytes of `s` before its NUL (at most `len`), then NUL up to and including `[len]`; one allocation |
| `vim_strup(p)` | every byte becomes `up(byte)`, in place |
| `vim_strcpy_up(dst, src)` | `dst` = `up` of each byte of `src`, then NUL |
| `vim_strncpy_up(dst, src, n)` | `up` of the bytes of `src` before its NUL (at most `n`), then one NUL; writes nothing else |
| `vim_memcpy_up(dst, src, n)` | `dst[i] = up(src[i])` for `i < n`; no NUL written |
| `vim_strsave_up(s)` | new block holding `up` of each byte of `s` and the NUL |
| `vim_strnsave_up(s, len)` | new block of `len + 1` bytes holding `up` of the bytes before NUL/len, then NUL |
| `del_trailing_spaces(ptr)` | trailing spaces/TABs become NUL, stopping at one preceded by a backslash or Ctrl-V; the first byte is never removed |
| `vim_strnicmp_asc(s1, s2, len)` | `low(s1[k]) - low(s2[k])` at the first `k < len` where they differ before a shared NUL, else 0 |
| `has_non_ascii(s)` | true iff `s` is not NULL and has a byte >= 128 before its NUL |
| `has_non_ascii_len(s, len)` | true iff `s` is not NULL and has a byte >= 128 in `s[0..len-1]` |
| `concat_str(a, b)` | new block holding `a` then `b` then NUL |

All: no undefined behavior (`-wp-rte`), termination (loop variants), and for the allocating
ones exactly one allocation (ghost counter `vp_live`).

## What the proof relies on

1. **Frama-C WP, Why3 and the provers are sound** (Z3, CVC5).
2. **The C library meets** `wp/stubs/vp_string.h` (strlen; copied from memory/) and
   `wp/stubs/vp_string_more.h` (strncpy, strcpy, strstr, from C11 7.24), no axioms.
3. **xmalloc / xmallocz meet `wp/stubs/nvim/memory.h`**: base64's xmalloc stub plus spelled-out
   freshness for up to two live objects the caller names (ghost arguments): the new block is
   a different object. xmallocz(size) excludes `size == SIZE_MAX` (it exits there).
4. **Preconditions**: strings NUL-terminated (`FUNC_ATTR_NONNULL_ALL`), buffers large enough
   as the comments say (`dst` of `n + 1` for `vim_strncpy_up`), no overlap where `restrict`
   says so, objects smaller than `PTRDIFF_MAX`.
5. **`del_trailing_spaces` on an empty string** computes `ptr - 1` (only compared, never read).
   That is undefined behavior unless `ptr` is inside a larger array; the contract requires it
   (`\offset(ptr) >= 1` when the string is empty). True at the only caller (`ex_docmd.c`,
   `eap->arg` points into the command line). Recorded, not filed as a bug.

## Not covered yet (62 functions, open)

Everything else in strings.c, notably: `vim_strsave_escaped`, `vim_strsave_escaped_ext`,
`vim_strnsave_unquoted`, `vim_strsave_shellescape`, `mb_strup_buf`, `strcase_save`,
`vim_stricmp` and `vim_strnicmp` (not compiled on Linux: glibc has strcasecmp), `striequal`,
`vim_strchr`, `sort_compare`, `sort_strings`, `strrep` (precondition needed: `what` non-empty,
else it never returns; the only caller passes `"$*"`), `reverse_text`, the printf family
(`vim_snprintf*`, `vim_vsnprintf*`, `tv_*`, `format_*`, `parse_fmt_types`, `skip_to_arg`,
`kv_do_printf`, `arena_printf`, ...), and the Vimscript builtins (`f_*`, `byteidx_common`,
`strchar_common`, `cmp_keyvalue_value*`).
Independent review and planted bugs: pending. Owner sign-off: pending.

## Evidence

| Check | Command | Result |
|---|---|---|
| WP, upstream | `bash wp/run_wp.sh <nvim> 60` | every goal proved, 12 functions + ascii_iswhite, one run each (270 goals) |
| Differential test (gcc -O2, glibc, ASan/UBSan, signed and unsigned char) | `bash difftest/run_difftest.sh <nvim> 1000000` | 12,000,000 checks each, 0 mismatches |
| Independent review | | pending |
| Planted bugs | | pending |
| CI, pinned container | `.github/workflows/verify.yml` | pending |
