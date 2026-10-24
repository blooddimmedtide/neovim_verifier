# Adversarial review: proof of Neovim `src/nvim/base64.c`

Reviewer: independent review agent (did not write the proof). Date: 2026-10-24.
Subject: upstream commit `7b87ce822e6fd45a4d9993599c2854afdb0dc4dd`, the fixed fork
`/home/claude/verified_neovim/src/nvim/base64.c`, and everything under `base64/` and
`vpipe.toml` in this directory. Measured against the "verified-libs admission standards" doc.

## Verdict

**Not admissible yet.** The core functional proof is well built. The encoder and decoder
specs follow RFC 4648 closely, and the patch and strip steps are exact. Five problems
block admission (B1 to B5). B1 and B2 mean a planted bug of the kinds the standard names
can get past the WP proof today. Four of my gap-probe mutants are predicted to survive it.

## What I checked and found sound

- **Strip/patch relationship is exact.** I re-ran `annotate.py` on the pristine upstream
  file and on the fork. The output is byte-identical to `wp2/b64_enc.c`, `b64_dec.c` and
  `b64_dec_fixed.c`. I then removed every `/*@ */` and `//@` annotation from those files
  and diffed the result against `tool_patches.apply(pristine)`. The only differences are
  blank lines and indentation before annotation blocks, so no code line is added, dropped
  or changed. After patching, the code never reads `src` through a `char` lvalue, so every
  input read goes through the `uint8_t` view the spec uses.
- **Encoder spec = RFC 4648 §4 (given the alphabet, see B1).** `byte_at` (zero-extends
  past the end), `grp`, `sextet`, `data_len(n) = ceil(8n/6)` (2/3/4 data characters for
  1/2/3 bytes), `enc_len = 4*ceil(n/3)` and `enc_char` ('=' after `data_len`) all match the
  standard. The postconditions cover every output index and the NUL at `enc_len`, so a
  wrong length or a missing terminator fails them.
- **Decoder spec = canonical RFC 4648 decoding (given the table, see B1).** `valid_b64`
  requires length ≡ 0 mod 4, alphabet characters before the trailing '=' run, and at
  most two '='. It also requires zero unused bits: `V(n-2)%4==0` for one '=' and
  `V(n-3)%16==0` for two. I enumerated the edge cases "====", "A===", "AB=A", "A=B=",
  "QQ=A" and "QUFB====" by hand. All are rejected by `valid_b64` and by the code.
  Both directions are proved (`accepts_only_valid` and `accepts_all_valid`), as are
  `length` and per-byte `dec_byte`. The mismatch between `pad` (spec) and `eqs` (code) only
  affects inputs that are invalid anyway, and the annotations handle it.
- **Bit lemmas.** I ran `python3 -I wp/lemmas.py` and every lemma reports PROVED. The
  check uses 128-bit bit-vectors with every variable bounded far below 2^127. Z3's signed
  `/ % >> < <=` agree with ACSL integer semantics on non-negative values, so the transfer
  argument holds. Expressions are fully parenthesised, so C and Python precedence cannot
  diverge. With `-wp-fct`, WP generates no `Lemma` goals (none appear in `goals_e.txt`), so
  inside WP the lemmas act as unproved hypotheses justified only by `lemmas.py`. The
  standard allows this.
- **Tool-patch equivalence harnesses.** They are sound. Each one `#include`s the real
  `base64.c`, so a mutated `vim_htobe*` is seen. Inputs are fully nondeterministic with no
  `__CPROVER_assume`. They run with unwinding assertions, under both the `vim_htobe` and
  glibc `HAVE_BE64TOH` builds, and are regenerated and compared with the committed copies.
  Each rewritten statement reads exactly the bytes the original reads, so WP's
  `-wp-rte` bounds checks on the rewrite cover the original `memcpy` footprint.
- **`vim_htobe64/32`.** `bridge.c` checks `vim_htobe64(memcpy(p)) == be64(p)` for all 2^64
  values of `p`, and likewise for 32 bits. On a little-endian host `memcpy` is a bijection,
  so this fully specifies the functions. The loops have constant bounds, and `--unwind 10`
  with unwinding assertions makes it a complete proof, not a bounded one.
- **Upstream >= 2 GiB bug** (`findings/base64-decode-over-2gib.md`) is real, and the
  annotation bound `src_len <= 0x7fffffff` is exactly enough for `(int)src_i` to stay in range.

## Issues, by severity

### BLOCKING

**B1. The spec is not independent of the code's tables, so the RFC alphabet is never
proved by WP.** `enc_char` is defined as `alphabet[sextet(...)]`. `V` and `valid_b64` are
defined as `char_to_index[...]` (nonzero, minus 1). Both are the code's own `static const`
arrays, and WP reads their initialisers. If the tables change, the spec changes with them.
Mutants `G-alphabet-urlsafe` (encoder emits `-_`) and `G-index-urlsafe` (decoder accepts
`-_` and rejects `+/`) are predicted to pass `run_wp.sh`. The bounded CBMC `check` harnesses
(`spec.h` has its own `ref_alpha`) would catch them, but bounded results do not count
(gate 3). They are also not part of `prove`, and the chain "CBMC at length ≤ 24 pins every
table entry, so the WP spec equals RFC for all lengths" is not written down anywhere.
Nothing links `alphabet` and `char_to_index` to each other either.
*Fix (cheap):* add ACSL `rfc_char(v)` (`'A'+v`, `'a'+v-26`, `'0'+v-52`, `'+'`, `'/'`) and
`rfc_index(c)` written from the RFC. Then either define `enc_char`/`V`/`valid_b64` with
them and assert `\forall integer v; 0<=v<64 ==> alphabet[v] == rfc_char(v)` and the 256
`char_to_index` facts (WP discharges these from the const initialisers), or put those
facts in the postconditions. This violates gate 6 ("spec matches the governing standard;
planted bugs must fail").

**B2. Allocation and freeing are not modelled, so leaks, double frees and use-after-free
pass.** The `xfree` stub is `assigns \nothing;` with no `requires` and no effect on
validity. WP also drops `xmalloc`'s `\fresh` ensures ("Allocation, initialization and
danglingness not yet implemented" in every log). Consequences:
- `G-leak-on-invalid` (drop the `xfree` on the invalid path) is predicted to pass.
- `G-use-after-free` (`xfree(dest)` just before `return dest`) is predicted to pass.
  `\valid(\result + ...)` still holds after the "free". Every caller then frees the
  buffer a second time.
- Freeing a non-heap pointer, or the wrong pointer, is unconstrained.
`vpipe.toml` scope says "no ... other runtime error", and gate 4 requires no UB or crash.
*Fix:* a ghost allocation state in the stubs. For example, `xmalloc` ensures
`\result == g_last && g_live == 1`, and `xfree` requires `p == g_last && g_live == 1`
and ensures `g_live == 0`. Then `base64_decode` ensures
`\result != \null ==> g_live == 1 && \result == g_last` and
`\result == \null ==> g_live == \old(g_live)` (no leak, no double free). `base64_encode`
gets the same treatment. Alternatively, narrow the scope text and record this as "not
covered", but gate 4 then fails.

**B3. No complete proof run is on record.** The latest reports I could find show unproved
goals:
- `wp2/rep_enc.txt` (07:19) has 12 `Timeout` goals, among them `assert_load64`,
  `assert_load32`, the fast-path sextet assertions and `assert_rte_mem_access_11`.
- `wp2/rep_dec.txt` is at 108/109 (`assert_cast_mod256` timeout).
- `rep_e.txt` is at 203/204.
- `full_enc.txt` is still running, and there is no log for `dec_fixed`.

`status.tsv` already marks the encoder `verified`. Unproved goals are forbidden, and
gate 9 needs two clean runs in a pinned container. Admission needs the `Proved goals: N / N`
lines for enc, dec and dec_fixed from a clean `run_wp.sh`, plus `run_bridge.sh`, kept in
the repo.

**B4. Upstream decoder and paperwork gates.**
(a) The upstream decoder proof is capped at 2 GiB, and gate 3 says size caps do not count.
Only the fork can be admitted, so the fork must be published (gate 1) and
`status.tsv`'s `verified-upto-2GiB` must become `candidate`.
(b) There is no `CLAIM.md` or `functions.toml` (gate 7; the annotation comment in
`annotate.py` cites a CLAIM.md that does not exist).
(c) The forbidden-construct check is a source-text grep of `b64_*.c` only. It does not
cover the `#include`d stub headers, whose contracts are trusted, and it does not read the
tool's own dependency report, which gate 7 requires.

**B5. Targets and build options (gate 2).** Everything is proved for `-machdep x86_64`
only: little-endian, signed `char`, 64-bit `size_t`. Unproved cases:
- The `ORDER_BIG_ENDIAN` branches of `vim_htobe*`.
- Big-endian builds of the fast paths: the equivalence harnesses ran only on a
  little-endian model.
- aarch64, where `char` is unsigned. The lemmas happen to hold there too, but nothing
  checks that.
- 32-bit targets, where `((src_len + 2) / 3) * 4` overflows for `src_len` ≳ 3 GiB.
Either prove the other configurations or state the claim per target. Also, the entry can
only be "Neovim `base64.c`", not Neovim: every other function in the library is open.

### HIGH (not blocking if documented; needed before the gate-6 run is meaningful)

**H1. Mutants on anchor lines abort annotation and never reach WP.** `annotate.py` keys
insertions on whole code lines. Any planted bug on one of those lines makes `annotate.py`
exit non-zero, and the proof itself never runs. Examples are the canonical-bits line
`if (acc_len > 4 || ...)`, the accumulator line, both fast-loop headers,
`dest[out_len] = NUL;` and `dest[out_i] = (char)(acc >> acc_len);`. The same happens on
tool-patch text (load64, load32, pad_last, pad_second). That counts as caught only
because it is documented. In `mutants.toml`, 6 mutants carry `anchor_line = true` and 2
hit tool-patch text (`dec-pad2-index`, `enc-load64-offset`).
*R4 (recommended runner):* annotate the pristine file, then apply each mutant to the
annotated output and run WP. Every anchor-line mutant's `original` occurs exactly once in
the annotated files. I checked this, and only the two patch-text mutants do not apply
there; they are caught by the abort. That way the proof, not the anchor matcher, rejects
the bug.

**H2. The proof's no-aliasing argument comes from the memory model, not from a proof.**
WP warns "Cast with incompatible pointers types (sint8* -> uint8*)" at every
`(uint8_t *)src`. The Typed model keeps `char` and `uint8_t` cells in separate memories,
so writes to `dest` (char) can never change the `uint8_t` view of `src`. WP drops the
`\fresh` in the stub, so this separation is a property of the model. It happens to match
reality only because `xmalloc` returns fresh memory (assumption 1). It must appear in
CLAIM.md as a tool or memory-model assumption. Any future annotation that reads `src` as
`char` would silently see unrelated memory.

### MEDIUM

- **M1. The `xmalloc` stub is stronger than the real function.** It claims
  `assigns \result \from n`, but the real `xmalloc` → `try_malloc` calls
  `try_to_free_memory()` (`clear_sb_text`, `mf_release_all`) when `malloc` fails, and
  `preserve_exit` when that fails too. The only callers (`nlua_base64_*`) pass Lua
  strings, which those calls do not touch, so the result stands. Assumption 1 should say
  "does not modify memory reachable from `src` / `out_lenp`, and does not return on OOM".
  The `xfree` stub is not mentioned in the assumptions at all.
- **M2. The contracts say nothing about where the result comes from.** There is no
  `\fresh`/`allocates`/`assigns` on either function. For an empty decode result,
  `\valid(\result + (0 .. -1))` is vacuous, so returning a pointer to static data, which
  every caller then `xfree`s, would satisfy the contract. This is covered by the B2 fix.
- **M3. The 4 EiB encoder cap needs a stated assumption.** It relies on an
  address-space argument (x86_64 virtual addresses are at most 57 bits) that is not in
  `vpipe.toml` assumptions. Add it, or gate 3 treats it as a size cap.

### LOW

- **L1. One generated assertion is silently dropped.** `dec_inserts` concatenates two
  asserts on one line (`... + V(s, src_i);      //@ assert src_len >= 1 && ...`,
  `b64_dec.c:275`). Inside a `//@` annotation, the second `//` starts a comment, so that
  assert is never checked. This is harmless for soundness, but it shows the generated
  annotations were not proof-read.
- **L2. Stale comments.** `bridge.c` and `run_bridge.sh` say the WP proof "admits"
  load64/load32; these are now tool patches. The `-DNDEBUG` build drops
  `assert(src != NULL)`, and with `src_len == 0` the contract allows `src == NULL`.
  Both are harmless.
- **L3. `vim_htobe*` WP annotations are never checked.** The
  `/*@ assigns \nothing; */` annotations on `vim_htobe*` are never proved: `-wp-fct`
  excludes them, and the patched code no longer calls them. Their correctness rests
  entirely on `bridge.c` and the equivalence harnesses, which is fine, but the WP
  annotations are decoration.

## Mutants (`mutants.toml`)

There are 35 mutants: 31 expected to be caught by `prove` as it stands, plus 4 gap probes
(`G-*`) that I predict survive, documenting B1 and B2.

- **Coverage.** Encoder 64-bit path (4), encoder 32-bit path (2), encoder tail and
  padding (8, among them length, allocation size and NUL), decoder length and
  accumulator (5), padding and canonical bits (7, one via tool-patch abort), fixed
  decoder (2), `vim_htobe64/32` (2, caught by CBMC equivalence and bridge, not WP), and
  one load-patch mutant.
- **Uniqueness.** Every `original` occurs exactly once in the target file (checked with
  Python). `tree = "fixed"` mutants apply to the fork.
- **Behaviour check.** I compiled every mutant with gcc and ASan (no Frama-C or CBMC) and
  compared it against an independent RFC 4648 reference. Every mutant differs on some
  input, except `enc64-overread`, `enc32-overread` and `dec-len-mod`:
  - The two overread mutants have unchanged output: their only effect is an
    out-of-bounds read, which `-wp-rte` must catch.
  - `dec-len-mod` was not sampled; I traced it by hand: "QUFBQQ" makes it write 4 bytes
    into a 3-byte buffer.
  - The two `G-alphabet`/`G-index` and `G-leak`/`G-uaf` probes are confirmed real
    behaviour changes: wrong output, a leak on invalid input, and an ASan
    use-after-free respectively.
- **Absorbed by a tool patch / annotate abort (counts as caught only because it is
  documented):**
  - `dec-pad2-index` (pad_second text) and `enc-load64-offset` (load64 text) are caught
    by the abort.
  - `enc64-overread`, `enc32-overread`, `enc-nul`, `dec-emit-shift`,
    `dec-leftover-bits-len` and `dec-canonical-mask` sit on annotation anchor lines.
    Under the naive runner they abort `annotate.py`; under the H1/R4 runner they must
    fail WP.
- **Equivalent mutants I avoided** (do not plant them; they cannot be caught):
  - `padding_chars > padding_len`: fewer '=' than needed is unreachable once length ≡ 0 mod 4.
  - `*out_lenp = out_i`: `out_i == out_len` on every accepted input.
  - `int acc = 1`: the initial bits are masked out by `& 0xFFF` before they matter.
  - `src_i + 8 < src_len` in the 64-bit loop: the 32-bit loop produces the same output.
