# Independent review: CBMC + Frama-C WP proofs of src/xdiff/xutils.c

The reviewer is a fresh adversarial agent with no context from the prover. Target: the FIXED code
(`/tmp/claude-0/xd/xutils_fixed.c`, the fork's `xdiff-fixed-local`). Scope: only the rows CLAIM.md
marks **proved**. `xdl_recmatch`, the hash functions, `xdl_num_out` and the hunk-header text path are
OPEN or running, so they are not reviewed here. Tools: CBMC 6.4.1 (cadical) and Frama-C 33 WP
(Typed+Cast, z3+cvc5). The CPU was shared, so the reviewer ran one prover process at a time.

## Verdict: MOSTLY SOUND FOR WHAT IS PROVED. The claim overstates in a few places.

- Every proved row re-runs green:
  - CBMC: 7 harnesses × 2 char signednesses, 20 s.
  - WP: `xdl_cha_init` 23/23, `xdl_cha_free` 24/24, `xdl_blankline` 26/26, `len_without_eol` 11/11 and `xdl_guess_lines` 58/58.
  - The global lemmas `cha_slots`, `shift_back`, `nl_char` and `cr_char` are proved: 4/4 with `-wp-prop`.
- Mutation testing planted 43 bugs: 37 real and 6 equivalent.
  - 35 of the 37 real bugs are caught.
  - All 6 equivalent mutants survive, as they should.
  - **The 2 survivors are both use-after-free bugs.** Neither memory model ends an object's lifetime (F1).
- The functional specs are strong. Each planted off-by-one, wrong-constant and wrong-field bug is caught.
- The weaknesses are about the scope of the claim: lifetime and memory safety, unlisted bounds and preconditions, and glue between the tools that is argued on paper rather than proved.

## What I ran
| Check | Result |
|---|---|
| `ONLY=... bash cbmc/run_cbmc.sh <nv> xutils_fixed.c` (the 7 proved harnesses) | 14/14 proved, 20 s |
| WP baseline per proved function (`build_wp.py`, CLAIM flags) | all goals proved, 2–15 s each |
| WP `-wp-prop cha_slots,shift_back,nl_char,cr_char` | 4/4 proved |
| `review/` (F1 fix, CBMC) | fixed code 14/14 proved; `fbd-free-before-copy` caught |
| `python3 -I run_mutants.py` | 35/37 real mutants caught, 6/6 equivalent mutants survive; `mutants_result.tsv` |

## Findings

### F1 (high): neither free model ends a lifetime, so use-after-free and double free are never checked
- **CBMC.** `cbmc/memory.h` `xfree` only records its argument and never deallocates. `harness.c` stubs
  `xdl_free_env` the same way: it records the rchg pointers and leaves them live. `--pointer-check`
  therefore never sees a dead object.
  - Mutant `fbd-free-before-copy` moves `xdl_free_env(&env)` before the two `memcpy`s that read
    `env.xdf*.rchg`. That is a real use-after-free, and it **survives**.
- **WP.** `free_log` (build_wp.py) only appends to a ghost log. `\valid(nth(head, k))` still holds after
  a block is "freed".
  - Mutant `cha-free-uaf` swaps the two loop statements to `xdl_free(tmp); cur = cur->next;`, which reads
    `cur->next` after freeing `cur` (tmp == cur). It **survives** 23/23.
- CLAIM.md's row for `xdl_cha_free` says it "frees every block of the list exactly once, in order, nothing
  else". That is true of the free calls. It says nothing about memory safety around them, and the
  "What the proofs rely on" section does not say that frees are not lifetime-ending.
- **Suggested fix:**
  - CBMC: make `xfree` call `__CPROVER_deallocate(p)` (or `free`) after recording, and the same in the
    `xdl_free_env` stub.
  - WP: give `free_log` `frees p;` or `ensures !\valid(p)` (or `\allocable{Post}(p)`).
  - The fixed code itself is fine on both points. Only the proofs miss this class of bug.
- **Checked for the CBMC side.** In `review/memory_review.h`, `xfree` deallocates. In `review/harness_review.c`, the
  `xdl_free_env` stub deallocates both rchg arrays and snapshots the one byte each assertion compares.
  - With these, all 7 proved harnesses still prove on the fixed code: 14/14 runs.
  - `fbd-free-before-copy` is then caught: `memcpy source region readable: FAILURE`.
  - To reproduce: copy `cbmc/run_cbmc.sh` next to them as `harness.c` / `memory.h` and run `ONLY='^h_fall_back_diff$'`.
  - The WP fix was not tried, for lack of time.

### F2 (medium): the `xdl_fall_back_diff` preconditions in the harness are not all in CLAIM.md
`range_file` assumes `line >= 1 && count >= 1` for both sides. CLAIM.md only says "the ranges are within
the files". A range of `count == 0` is within the file, but with it the code reads
`recs[line - 2]`, which is out of bounds for `line == 1`.
- The callers do guarantee `count >= 1`: xpatience.c:340 and xhistogram.c:331 handle `!count1` / `!count2` first.
- So the proof is fine, but `count1, count2 >= 1` and `line >= 1` must be listed as preconditions.

The model of `xdl_do_diff` is "fails, or gives >= count rchg bytes, and touches nothing on failure". It
does not model that the real `xdl_do_diff` frees `env` itself on failure. The harness does catch a
double free there (`fbd-free-on-failure`), but only through the `fe_calls == 0` assertion, not through
memory safety (see F1).

### F3 (medium): `xdl_cha_alloc` rests on an argument across the two tools that is not mechanised
The CBMC harness assumes a store shape:
- `ancur == tail`, `tail->next == NULL`;
- `head` is `tail` or one unrelated block whose `next` is never looked at;
- `SLOTS(icurr, nsize, isize)`;
- `nsize >= isize`.

The WP lemma `cha_slots` proves only the integer arithmetic (`j*isize`, `k*isize` give SLOTS and are kept).
Nothing mechanised proves that the sequence `xdl_cha_init`; `xdl_cha_alloc`* establishes and keeps that
shape. In particular nothing proves that the head..tail chain remains a `list(head, n)`, which is
exactly `xdl_cha_free`'s WP precondition. The pieces fit on paper:
- init gives head = tail = ancur = NULL;
- the harness checks that alloc appends with `next = NULL`.

CLAIM.md should state the shape invariant and say that composing the two proofs is a manual step.
- Two mutants that rely on this invariant are equivalent: `cha-alloc-ge` and `cha-alloc-tail` (ancur ↔ tail).

### F4 (low): bounds smaller than the claim, not listed in CLAIM.md
- `h_cha_alloc` requires `nsize + sizeof(chanode_t) <= 2^50`. CLAIM.md only says that `isize * icount`
  fits in a long. Also, `xmalloc` in memory.h returns NULL above 2^50, so a larger block is never modelled
  as allocated.
  - This is harmless, since Neovim's `xmalloc` aborts long before that.
  - It is still a bound to state.
- WP `xdl_cha_free` requires `nfreed + n < 1000000`, because of the ghost log size. So it is proved only
  for lists of fewer than 10^6 blocks, minus the earlier frees. CLAIM.md says "every block".
- `h_emit_hunk_hdr_cb` (the callback path, marked "proved") assumes `s1, s2 >= 1` and `c1, c2 >= 0`, the
  range xemit.c uses. The CLAIM row states no range. The text-path paragraph mentions it only for the
  upstream code.
- `h_emit_diffrec` limits `size` and `psize` to `[0, INT_MAX]`. This matches `mmbuffer_t.size`, which is
  `int`, and it is stated in the harness, though only implicitly in CLAIM.md.

### F5 (low): WP proofs run per function; the lemmas are proved by a separate run
With `-wp-fct f`, WP does not prove global lemmas. CLAIM.md says "All other ACSL lemmas are WP-proved".
I checked that the 4 global lemmas in the prelude do prove (`-wp-prop`, 4/4). CLAIM.md or the run script
should name the command that proves them, so that a rerun with only `-wp-fct` does not silently skip
them. This was not verified for the `xdl_recmatch` / hash lemmas, which are out of scope.

### F6 (info): WP stubs replace the real headers
The prelude matches the types I checked:
- `mmfile_t` is `{char*, int}`;
- `chastore_t` has the same field order;
- `XDL_ISSPACE` is `isspace((unsigned char)c)`, as in xmacros.h.

The CBMC side includes the real headers and pins their sha256. The WP side does not pin the headers it
replaces, so a header change upstream would not be noticed by `build_wp.py`.

### What looks right
- No harness is vacuous on the paths mutated: every non-equivalent mutant of a CBMC-proved function, apart from the use-after-free one, fails a functional assertion.
  - This covers both the one-record and multi-record cases of `xdl_fall_back_diff` (`fbd-size-first-rec` is caught).
  - It also covers both the new-block and same-block branches of `xdl_cha_alloc`.
- `xdl_bogosqrt` and `xdl_hashbits` are exhaustive over their whole input type.
- `xdl_blankline`'s WP spec catches the upstream bug (`blankline-upstream`) and a spec-lax variant (`blankline-skip-first`).
- `len_without_eol` catches both the "\r\n" off-by-one and the dropping of a lone CR on an incomplete line.

## Mutants
`mutants.toml` holds 43 mutants of proved functions, applied to the fixed file. `run_mutants.py` applies each one and runs the tool CLAIM.md lists:
- the CBMC harness via `run_cbmc.sh` with `ONLY=`, both signednesses;
- or `build_wp.py`, then `frama-c -wp-fct`.

A mutant is caught when the proof fails. For WP that includes a goal that times out under the
mutant. All 8 WP catches were 1 goal short (2 for `cha-init-sum`).

| id | tool | expected | result | verdict |
|---|---|---|---|---|
| `bogosqrt-n-gt-1` | cbmc:h_bogosqrt | caught | caught | ok |
| `bogosqrt-shift1` | cbmc:h_bogosqrt | caught | caught | ok |
| `bogosqrt-add` | cbmc:h_bogosqrt | equivalent | survived | ok |
| `hashbits-le` | cbmc:h_hashbits | caught | caught | ok |
| `hashbits-cap31` | cbmc:h_hashbits | caught | caught | ok |
| `hashbits-zero` | cbmc:h_hashbits | caught | caught | ok |
| `diffrec-cr` | cbmc:h_emit_diffrec | caught | caught | ok |
| `diffrec-size1` | cbmc:h_emit_diffrec | caught | caught | ok |
| `diffrec-marker-len` | cbmc:h_emit_diffrec | caught | caught | ok |
| `diffrec-marker-text` | cbmc:h_emit_diffrec | caught | caught | ok |
| `diffrec-ret-le0` | cbmc:h_emit_diffrec | caught | caught | ok |
| `diffrec-psize` | cbmc:h_emit_diffrec | caught | caught | ok |
| `mmfile-first-size` | cbmc:h_mmfile | caught | caught | ok |
| `mmfile-size` | cbmc:h_mmfile | caught | caught | ok |
| `cha-alloc-ge` | cbmc:h_cha_alloc | equivalent | survived | ok |
| `cha-alloc-tail` | cbmc:h_cha_alloc | equivalent | survived | ok |
| `cha-alloc-step1` | cbmc:h_cha_alloc | caught | caught | ok |
| `cha-alloc-head` | cbmc:h_cha_alloc | caught | caught | ok |
| `cha-alloc-nolink` | cbmc:h_cha_alloc | caught | caught | ok |
| `cha-alloc-nonext` | cbmc:h_cha_alloc | caught | caught | ok |
| `cha-alloc-nocheck` | cbmc:h_cha_alloc | caught | caught | ok |
| `cha-alloc-short-block` | cbmc:h_cha_alloc | caught | caught | ok |
| `hunk-cb-empty-start` | cbmc:h_emit_hunk_hdr_cb | caught | caught | ok |
| `hunk-cb-funclen` | cbmc:h_emit_hunk_hdr_cb | caught | caught | ok |
| `hunk-cb-gt0` | cbmc:h_emit_hunk_hdr_cb | equivalent | survived | ok |
| `fbd-count-short` | cbmc:h_fall_back_diff | caught | caught | ok |
| `fbd-offset` | cbmc:h_fall_back_diff | caught | caught | ok |
| `fbd-no-free` | cbmc:h_fall_back_diff | caught | caught | ok |
| `fbd-size-first-rec` | cbmc:h_fall_back_diff | caught | caught | ok |
| `fbd-ret-le0` | cbmc:h_fall_back_diff | caught | caught | ok |
| `fbd-free-before-copy` | cbmc:h_fall_back_diff | caught | survived | GAP |
| `fbd-free-on-failure` | cbmc:h_fall_back_diff | caught | caught | ok |
| `cha-init-sum` | wp:xdl_cha_init | caught | caught | ok |
| `cha-init-scurr` | wp:xdl_cha_init | caught | caught | ok |
| `cha-free-uaf` | wp:xdl_cha_free | caught | survived | GAP |
| `guess-lines-tsize` | wp:xdl_guess_lines | caught | caught | ok |
| `guess-lines-no-tsize-test` | wp:xdl_guess_lines | equivalent | survived | ok |
| `guess-lines-div1` | wp:xdl_guess_lines | caught | caught | ok |
| `blankline-upstream` | wp:xdl_blankline | caught | caught | ok |
| `blankline-ge` | wp:xdl_blankline | equivalent | survived | ok |
| `blankline-skip-first` | wp:xdl_blankline | caught | caught | ok |
| `eol-cr-gt1` | wp:len_without_eol | caught | caught | ok |
| `eol-lone-cr` | wp:len_without_eol | caught | caught | ok |

Survivors that should have been caught: `fbd-free-before-copy` and `cha-free-uaf`. Both are explained by F1.
