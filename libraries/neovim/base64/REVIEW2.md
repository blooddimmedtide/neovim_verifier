# Second adversarial review: proof of Neovim `src/nvim/base64.c`

Reviewer: fresh independent review agent (did not write the proof or REVIEW.md). Date: 2026-10-24.
Measured against "verified-libs admission standards" (rev 8). Subject: `CLAIM.md`,
`wp/`, `equiv/`, `bridge/`, `difftest/`, `mutants.*`, `run_mutants.py`, `../vpipe.toml`,
upstream `7b87ce822e`, and the fork `verified_neovim` (branch `fix-base64-decode-over-2gib`).
Frama-C was not run (CPU in use elsewhere). Everything else below was re-run or re-derived.

## Verdict

**Not admissible as `full-correctness` yet.**

The mathematical core holds up. I found no way for wrong code to satisfy the
postconditions, no false hypothesis, and no vacuity. Both blockers from REVIEW.md
(B1 spec tables, B2 allocation) are closed in substance. What still blocks admission:
gates the standard makes mandatory that are not met yet (pinned CI run twice, maintainer
review, automated trusted-base check, targets), plus one contract gap that is cheap to fix.
In Neovim's default build, that gap lets a "proved" input crash the program.

## What I re-checked and found sound

- **The proved files are the current ones.** I ran `annotate.py` on pristine upstream and on
  the fork (enc, dec). The outputs are byte-identical to `wp2/b64_enc.c`, `b64_dec.c` and
  `b64_dec_fixed.c`, and to the inputs of the two `run_wp.sh` runs in
  `/tmp/tmp.CEexrDMHgL` (upstream: 259/259, 118/118) and `/tmp/tmp.wsfxF35QVN` (fork:
  259/259, 116/116). The stubs, `annotate.py`, `lemmas.py` and `tool_patches.py` in `wp2/`
  match the repo copies. No unproved goals appear in those logs.
- **After patching, `src` is never read as `char`.** I stripped the annotations and listed every
  code line that touches `src`. All reads go through `const uint8_t *`, which is the view the
  spec quantifies over.
- **The spec is RFC 4648 and independent of the code's tables.** `rfc_char`/`rfc_index` are
  written out in ACSL. The encoder's `encodes` postcondition uses `rfc_char` directly, and
  `enc_table` forces WP to derive `alphabet[k] == rfc_char(k)` from the brace initialiser.
  The decoder's `V`/`valid_b64` use `rfc_index`, and the code's `char_to_index` is linked in
  both directions (the `V == d-1` asserts and the `!valid_b64` asserts at each `goto invalid`).
  I transliterated every ACSL logic function into Python (`rfc_char`, `sextet`, `enc_char`,
  `rfc_index`, `V`, `dec_byte`, `pad`, `valid_b64`) and compared it with Python's `base64`,
  using `validate=True` plus a re-encode check for canonical form, on:
  - all 1- and 2-byte encoder inputs, plus random inputs of 0 to 6 bytes;
  - all 4-character strings over a 16-symbol edge alphabet (bit edges, `=`, `-`, NUL, 0xFF, space);
  - every `xyz=` and `QUJDxyz=` with xyz drawn from the 65 symbols;
  - 100k corrupted valid strings of length 4, 8 and 12.
  There were **0 mismatches**. Acceptance, length and every byte match canonical strict
  RFC 4648 decoding.
- **The bit lemmas are sound.** `python3 -I wp/lemmas.py` reports 44/44 PROVED. Every lemma
  carries its own range hypotheses, and every expression is parenthesised, so C and Python
  precedence agree. Signed bit-vector `/ % >> <` agree with ACSL on the bounded non-negative
  domain. The cast translations (`U64`, `U8(S8(x))`) match WP's `to_uint64`/`to_sint8`.
  The lemmas are true over the integers, so they cannot make the hypothesis set inconsistent.
- **The tool-patch equivalence harnesses are complete.** `run_equiv.sh` reports 10/10 on
  upstream and 10/10 on the fork, in under 2 s:
  - The harnesses contain no `__CPROVER_assume`, take fully nondeterministic inputs, and run
    with `--unwinding-assertions`.
  - Each harness `#include`s the real `base64.c` and runs under both htobe builds.
  - The committed harnesses are regenerated from `tool_patches.py` and compared before use.
  - Sanity check: I changed one shift in the load64 rewrite, and CBMC reported FAILED in both
    configurations.
  - `apply()` requires each original text to occur exactly once, so the alphabet harness's
    copy of the original is the file's text.
- **The htobe bridge holds.** `run_bridge.sh` reports VERIFICATION SUCCESSFUL (0 of 434
  checks failed).
- **The ghost allocation model works.** The stub has two `assigns` clauses. These must be
  merged as a union: an intersection would make every goal after `xmalloc` vacuous, and the
  30 WP-caught mutants that fail goals after `xmalloc` show that it is not. The ghost model
  catches:
  - a leak (`G-leak-on-invalid`, via `no_leak`);
  - returning a freed buffer (`G-use-after-free`, via `allocation`);
  - a double free or a free of the wrong pointer (the `xfree` precondition);
  - returning static memory (`vp_last == \result`). This was REVIEW.md M2.
- **The mutant runner is sound.** It mutates the annotated file, so a planted bug is judged by
  WP and not by an anchor mismatch (REVIEW.md H1). Only goals that pass at the same
  `--timeout` in the baseline count. Stopping at the first new failure is sound, because one
  new failing goal decides the verdict. 35/35 are reported caught, of which 30 by WP, 2 by
  equivalence and 3 by tool-patch text pinning.
- **The caller-facing preconditions are honest.** The only callers are `nlua_base64_encode`
  and `nlua_base64_decode` (`src/nvim/lua/base64.c`). They pass `lua_tolstring` data and a
  local `&out_len`. `\separated(out_lenp, src)`, `\valid_read`, the 4 EiB bound and the
  ghost `vp_live` range all hold for them. The finding's impact note (LuaJIT caps strings
  just under 2 GiB) is accurate.

## Blocking issues, ranked

**X1. Gate 9 (reproducible from scratch) is not met.** `.github/workflows/verify.yml` has these
gaps:
- It installs provers through Nix (`tools/install.sh`), not from a container pinned by digest.
- It runs once, not twice.
- It never fetches the fork, which is the only decoder that can be admitted.
- It uses `actions/checkout@v4`, which is not pinned to a SHA.

The `N / N` logs exist only in `/tmp/tmp.*` and are not committed. `CLAIM.md` also lacks the
upstream archive SHA-256, the fork's commit hash (only a branch name is given) and a toolchain
digest. The claim-card template and the supply-chain rules require all three.

**X2. Gates 5 and 10 (spec reviewed, two reviews) are not met.** The spec was changed after
the first review (`rfc_char`/`rfc_index`, the ghost allocation clauses), so it needs a fresh
maintainer reading. The owner review (Yerin) is still pending. This report covers only the
adversarial half.

**X3. Gates 2 and 4: in Neovim's default build, a crash on an input the contract accepts.**
The proof is built with `-DNDEBUG`. Neovim's `CMakeLists.txt:161-163` strips `-DNDEBUG` from
RelWithDebInfo (the usual distro build), so `assert(src != NULL)` is live. Neither contract
requires `src != \null`, and with `src_len == 0`, `\valid_read(src + (0 .. -1))` is vacuous.
So `base64_encode(NULL, 0)` and `base64_decode(NULL, 0, &n)` satisfy the proved contracts
but abort in the default build. The stub also defines `FUNC_ATTR_NONNULL_ALL` as empty, while
the real attribute makes a NULL argument undefined behaviour in GCC. Two fixes are needed:
- Add `requires src != \null;` to both functions. This matches the real nonnull attribute,
  so it is honest for every caller.
- Prove the assert-enabled build: drop `-DNDEBUG`, or add a run without it, so Frama-C's
  `assert` contract becomes a goal.
REVIEW.md L2 called this harmless. It is not, because asserts are enabled in the default build.

**X4. Gate 7 (clean trusted base): the check is not automated and the list is incomplete.**
- `run_wp.sh` still greps the source text. It never reads WP's own report of what each goal
  depends on, which the CI rule requires. This was REVIEW.md B4(c).
- `CLAIM.md` leaves out the memory-model assumptions WP itself prints:
  - The `wp_typed_cast` hypotheses: `\separated(src, alphabet)`, `\separated(src, char_to_index)`,
    `\separated(out_lenp, char_to_index)`, and `\result` separated from the tables.
  - The Typed+Cast fact (REVIEW.md H2, not addressed) that `char` and `uint8_t` cells live in
    separate memories, so writes to `dest` never change the `uint8_t` view of `src`. This
    matches reality only because `xmalloc` returns fresh memory, and WP drops `\fresh` (see
    the log warning).
  - The `xmalloc` contract's frame: it modifies no memory reachable from `src` or `out_lenp`,
    although the real function calls `try_to_free_memory()` on OOM. This was REVIEW.md M1.
- There is no `functions.toml` (one label and one theorem per function), and `CLAIM.md` does
  not follow the template's sections (Status / Entry strength / Trusted base / Review).

**X5. Gate 2 (every target and build option): the claim covers x86_64 only.** `CLAIM.md` says
so honestly. Still open:
- aarch64, where `char` is unsigned;
- 32-bit targets, where `((src_len + 2) / 3) * 4` can overflow;
- big-endian builds, including the `ORDER_BIG_ENDIAN` branches of `vim_htobe*`;
- the asserts-on build (X3).

The standard admits no partial targets. Separately, the library is Neovim, and only
`base64.c` is covered. These can be per-function `full-correctness` labels, but the entry
"Neovim" cannot be admitted (gate 2: "a library with any open function is not admitted").
`CLAIM.md` should name its entry as the file.

**X6. Lifecycle rule on tool soundness bugs: a maintainer ruling is needed.** The standard says
an entry that uses a tool with an announced soundness bug is `broken` until it is re-checked
on a fixed version, and it allows no waivers. The proof uses Frama-C 33 WP, which has the
known string-initialiser bug (also present in 32.1). The workaround is sound: the tool patch
removes the only string-initialised const array, and the patch is proved equivalent. But by
the letter, the entry cannot be admitted until the maintainer either records that a proved
workaround satisfies the rule, or a fixed Frama-C is used.

## Non-blocking notes

- **N1. Three "caught" verdicts are weak.** `G-alphabet-urlsafe`, `enc-load64-offset` and
  `dec-pad2-index` are caught only because `annotate.py` refuses text that a tool patch pins.
  So the encoder-side B1 fix (`enc_table`/`rfc_char`) is not exercised by any planted bug
  through WP. `CLAIM.md`'s statement "all 4 gap probes now caught" overstates this for the
  alphabet. I argue above that the spec is sound regardless, but the evidence should be
  direct. Add mutants that alter the patched text after annotation, for example swap `'+'`
  and `'-'` in the brace list, or change a byte offset in `BE64`. 32 genuine catches remain,
  so the "at least 10" bar is met either way.
- **N2. The runner does not record whether a newly failing goal was a Timeout or a Failed /
  Unknown.** It counts any new timeout at 120 s as caught. Every behavioural mutant is a real
  RFC violation (REVIEW.md checked them), so a sound proof of one is impossible and this does
  not create false catches. Still, record the kind of failure.
- **N3. No frame clause.** Neither function has `assigns` (WP warns). `-wp-rte` with
  read-only `src` and `const` tables rules out stray writes inside this file, but the
  guarantee "no other side effects" is not stated. Say so in `CLAIM.md`.
- **N4. `vim_htobe*` "no loops".** The wording is wrong: each has a constant-bound loop,
  fully unwound by `--unwind 10 --unwinding-assertions`. The input space is total, so this is
  complete, not bounded. The maintainer should confirm that this counts, given that the
  standard's strength table lists CBMC under `bounded`. These functions are not compiled in
  `HAVE_BE64TOH` builds.
- **N5. The differential test** compares compiled pristine code, compiled patched code and
  RFC. It does not test WP's internal translation (for example the Typed+Cast separation),
  and it builds without sanitizers. Add `-fsanitize=address,undefined`.
- **N6. One generated assertion is still silently dropped (REVIEW.md L1).** In
  `dec_inserts`, a second `//@ assert` follows the first on the same line, so it becomes a
  comment. Harmless, but fix it.
- **N7. Upstream decoder.** The 2 GiB cap means only the fork can be admitted (gate 3).
  `CLAIM.md`'s table should mark the upstream row "not admissible (size cap)" rather than
  "proved".

## Status of REVIEW.md blockers

| REVIEW.md | Status | Notes |
|---|---|---|
| B1 spec uses the code's tables | **Closed** | `rfc_char`/`rfc_index` in the spec, and tables proved equal. The encoder-side mutant evidence is only text pinning (N1). |
| B2 allocation not modelled | **Closed** (with a documented residue) | Ghost `vp_live`/`vp_last` catch leaks, double frees, wrong frees, returning freed memory and returning static memory. A stray write after `xfree` is not covered, and `CLAIM.md` says so. |
| B3 no complete run on record | **Partly closed** | Clean `run_wp.sh` N/N logs exist for the current inputs but only in `/tmp`. They are not committed, and gate 9 is not met (X1). |
| B4 upstream cap / paperwork / dependency check | **Partly closed** | `status.tsv` now says `candidate`, `CLAIM.md` exists, and the fork's remote is the GitHub URL. Still open: `functions.toml`, the template shape, the dependency-report check, and the memory-model assumptions (X4). |
| B5 targets / build options | **Open** | Documented honestly, but it blocks gate 2. Worsened by X3 (the asserts-on build). |
| H1 anchor-line mutants | **Closed** | Mutants are now applied after annotation. |
| H2 memory-model separation | **Open** | Not in `CLAIM.md` (X4). |
| M1 xmalloc stronger than real | **Open** | The frame assumption is still not stated (X4). |
| M2 result provenance | **Closed** | Via `vp_last == \result`. |
| M3 4 EiB cap | **Closed** | `CLAIM.md` assumption 6. |
| L1 dropped assert | **Open** | N6. |
| L2 stale comments / NULL src | Comments **closed**. NULL `src` **escalated** to X3. |
| L3 htobe WP annotations unchecked | Unchanged | Decoration only. |
