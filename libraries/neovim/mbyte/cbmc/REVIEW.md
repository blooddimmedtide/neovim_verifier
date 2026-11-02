# Independent review: CBMC proof of the UTF-8 helpers in src/nvim/mbyte.c

Reviewer: fresh adversarial reviewer (did not write the proof). Neovim commit 7b87ce8, CBMC 6.4.1.

## Verdict: ACCEPT WITH CHANGES

I found no soundness hole in the proofs. All 8 harnesses pass in about 1.3 s, and every harness end is reachable, so no assumption makes a harness vacuous. 24 of 27 planted bugs are caught. The 3 that survive are equivalent mutants.
The required changes are to the **wording of the claim**. "Full functional correctness for every input" is true only together with the preconditions and the accepted non-RFC-3629 forms listed under B1. Script hardening is recommended but optional.

## What I ran
- `build.py` on the pinned checkout. All 7 sha256 hashes match, and the output is the verbatim upstream text.
- `run_cbmc.sh`: all 8 harnesses proved.
- Vacuity check: I added `assert(0)` at the end of every harness. CBMC reports it as reachable in each harness, so the `__CPROVER_assume`s are satisfiable.
- Robustness reruns:
  - `--unsigned-char`: all proved.
  - `--arch arm64`: all proved.
  - `--pointer-overflow-check --pointer-primitive-check`: all proved.
  - `--conversion-check`: flags only implementation-defined int→`char` conversions in `utf_char2bytes` and the harness's own casts (see N2).
- `difftest.c` built with `gcc -O2 -fsigned-char`: 4,341,614,208 cases, 0 mismatches, 22 s.

## Blocking findings
None against the proofs.

**B1 (claim wording, required before admission).** The claim card must state these conditions. Without them, "every input" overstates the result.
1. **`utf_byte2len(b)`:** proved only for `0 <= b <= 255`, which is the documented domain. Outside it, the function reads outside `utf8len_tab` (UB).
   - Caller note: `fileio.c:1228` calls `utf_byte2len(*tail)` with `char *tail`. Neovim builds with `-fsigned-char`, so a lead byte ≥ 0x80 would give a negative index.
   - As far as I can tell this path is unreachable in Neovim: `fio_flags == FIO_UTF8` needs a conversion *from* UTF-8, and `need_conversion()` returns false for UTF-8 files because 'encoding' is always utf-8. It is still a latent precondition violation and worth an upstream `(uint8_t)` cast.
2. **Accepted forms:** the functions accept, and the spec deliberately requires, things RFC 3629 does not allow:
   - 5- and 6-byte forms, and values up to 0x7FFFFFFF (above U+10FFFF)
   - overlongs (`C0 80` decodes to 0, as documented)
   - surrogates (`ED A0 80` decodes to U+D800)

   `utf_char2bytes` also produces surrogates and values above U+10FFFF. "Correct" here means "matches RFC 2279 1–6 byte UTF-8 without the overlong, surrogate or range checks", not "valid RFC 3629 UTF-8".
3. **Negative `c`:**
   - `utf_char2len(c < 0)` returns 1.
   - `utf_char2bytes(c < 0)` writes one byte, the low 8 bits of c, which is not valid UTF-8 when it is ≥ 0x80.

   This is proved behaviour, not documented intent.
4. **`utf_ptr2len_len`:**
   - It always reads `p[0]`, even when `size <= 0`, so `p[0]` must be readable.
   - It does not stop at NUL.
   - Its exact meaning is the one in `ref_ptr2len_len`: it checks only the continuation bytes that fit in `size`. Upstream's doc comment is self-contradictory on incomplete sequences ("returns 1 … also in incomplete byte seq." vs "returns number > size"). The reference follows the code's reading, which is the one the callers rely on (`l > todo` in fileio.c, `len > size` in `utfc_ptr2len_len`).
5. **Memory safety:**
   - The string functions are proved only for non-NULL pointers to NUL-terminated strings (`NONNULL_ALL`).
   - `utf_char2bytes` writes exactly `buf[0..r-1]`, with r ≤ 6, and nothing else.

## Non-blocking findings
- **N1: char signedness and arch are not pinned in `run_cbmc.sh`.** CBMC takes them from the host, and the default char is unsigned on an aarch64 host. The proofs hold under both settings (checked), but the script should pass `--arch x86_64` or run both `--signed-char`/`--unsigned-char` so the result does not depend on the machine. `difftest.c` should also be built with `-fsigned-char` to match Neovim's `src/nvim/CMakeLists.txt`.
- **N2: implementation-defined behaviour.** `utf_char2bytes` converts out-of-range values to a signed `char`, e.g. `(char)(0xc0 + …)` and `(char)c` for negative c. C11 6.3.1.3p3 makes this implementation-defined. GCC, Clang and MSVC all reduce modulo 2^8, and CBMC models the same, so the claim holds for every compiler Neovim supports. The claim card should say it relies on this.
- **N3: the prelude differs slightly from the real build. All differences are harmless.**
  - `EXPECT(c,v)` is `(c)` here, but `__builtin_expect` in GNU/Clang builds. The truth value is the same. CBMC supports `__builtin_expect`, so the real definition could be used instead.
  - `FUNC_ATTR_PURE/CONST/NONNULL` are empty here. They only permit optimisations, and none of these functions has a null check that `nonnull` could remove.
  - `PRELUDE_CHECKS` checks that each line exists, not which `#if` branch is active.
  - `difftest.c` therefore tests code compiled *without* the real attributes.
  - Earlier in `mbyte.c` (line 531) there is another `CHECK` macro. It is `#undef`'d before `utf_ptr2char`, so it has no effect.
- **N4: the references follow the code's structure for `ptr2char` and `ptr2len_len`.** Both return the first byte / 1 on failure, and `ptr2len_len` uses min(L, size). The *values*, though, come from independent definitions:
  - lead length from counting leading ones, not from the table
  - payload from masking and shifting, not from subtracting constants
  - encoding length from bit counts

  So table, mask, shift and constant bugs are caught (see mutants). A wrong *policy* that mirrored the reference's choices would not be caught, which is why B1.4 needs to state the semantics.
- **N5: harness arguments checked and found sound.**
  - Exact-size `malloc` objects plus `--pointer-check` show that nothing is read past the NUL, or past `size`.
  - For long strings, the 6-byte object proves that no index ≥ 6 is read. The functions are deterministic, so the result carries over to every longer string.
  - For `size > 6`, `L ≤ 6` gives `m ≤ 6`, so a 6-byte object is enough.
  - `malloc` contents and `int`s are fully nondeterministic.
  - `--no-malloc-may-fail` only affects the harness's own `malloc`.
  - `--unwind 10` is backed by `--unwinding-assertions`; the deepest loop needs 9 unwindings.
  - The `h_char2bytes` comment "pointer checks show only buf[0..5] can be touched" is inaccurate, because `buf` has 8 bytes. That property actually comes from the "bytes past the result untouched" assertion; the `char2bytes-nul-term` mutant confirms it. Fix the comment.

## Mutant results (mutants.toml, 27 mutants, run with `bash run_cbmc.sh <checkout> <mutated file>`)

All mutants compile (`gcc -fsyntax-only`). In the "Caught by" column, `ptr2len`, `ptr2char` and `ptr2len_len` refer to both the short and the `_long` harness where both are listed.

| id | function | result | caught by / reason |
|---|---|---|---|
| tab-c0-invalid | utf8len_tab | caught | byte2len, ptr2len, ptr2char, ptr2len_len |
| tab-fb-six | utf8len_tab | caught | same |
| tab-fe-six | utf8len_tab | caught | same |
| tab-short | utf8len_tab | caught | array bounds check (index 0xFF) |
| byte2len-uint8-cast | utf_byte2len | survived, **equivalent** | identical for b in 0..255, the documented domain |
| ptr2char-ascii-le | utf_ptr2char | survived, **equivalent** | 0x80 has table length 1, so the original also returns v0 |
| ptr2char-cont-mask | utf_ptr2char | caught | ptr2char, ptr2char_long |
| ptr2char-len2-const | utf_ptr2char | caught | ptr2char, ptr2char_long |
| ptr2char-len3-shift | utf_ptr2char | caught | ptr2char, ptr2char_long |
| ptr2char-no-check-v5 | utf_ptr2char | caught | ptr2char, ptr2char_long |
| ptr2char-drop-lead30 | utf_ptr2char | caught | ptr2char, ptr2char_long |
| ptr2char-prefetch | utf_ptr2char | caught | pointer check: p[2] read past NUL (safety only) |
| ptr2len-nul-one | utf_ptr2len | caught | ptr2len |
| ptr2len-loop-le | utf_ptr2len | caught | ptr2len, ptr2len_long |
| ptr2len-mask | utf_ptr2len | caught | ptr2len, ptr2len_long |
| ptr2len-len-no-cast | utf_ptr2len_len | caught | array lower bound (signed char index) |
| ptr2len-len-ge | utf_ptr2len_len | survived, **equivalent** | when len == size both branches set m = len |
| ptr2len-len-ignore-size | utf_ptr2len_len | caught | pointer check: read past p[size-1] |
| ptr2len-len-loop-le | utf_ptr2len_len | caught | pointer check and functional assertion |
| ptr2len-len-incomplete-1 | utf_ptr2len_len | caught | functional assertion |
| char2len-16bit-le | utf_char2len | caught | char2len |
| char2len-26bit | utf_char2len | caught | char2len |
| char2bytes-11bit-le | utf_char2bytes | caught | char2bytes |
| char2bytes-lead3 | utf_char2bytes | caught | char2bytes |
| char2bytes-mask7f | utf_char2bytes | caught | char2bytes |
| char2bytes-nul-term | utf_char2bytes | caught | "bytes past the result untouched" |
| char2bytes-ret5 | utf_char2bytes | caught | char2bytes |

**Score: 24/24 non-equivalent mutants caught. The 3 survivors are equivalent and were predicted as such beforehand. No spec gap.**

The reviewer's scripts and mutated files are in
`/tmp/claude-0/-home-claude/6d24df0b-9d65-5d89-84cb-9e71c7c76de6/scratchpad/rev-mbyte/`
(`run_mutants.py`, `mut/*.c`, `harness_reach.c`).
