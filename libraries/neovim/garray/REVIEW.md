# Adversarial review: proof of Neovim `src/nvim/garray.c`

Reviewer: independent review agent (did not write the proof). Date: 2026-11-02.
Subject: upstream `7b87ce822e6fd45a4d9993599c2854afdb0dc4dd` and the fixed fork
(`verified_neovim` branch `claude/project-thread-aslfna`, fixes 850a906 and dec9b23).
Reviewed: `CLAIM.md`, `wp/build.py`, `wp/contracts.py` (including the later edit that wraps the
`exits` clauses in `\old`), `wp/tool_patches.py`, `wp/stubs/vp_garray.h`,
`../memory/wp/stubs/vp_string.h`, `equiv/`, `difftest/`, `run_mutants.py`, and both findings.
`/home/user/w/{up,fix}` did not exist, so I exported both trees from
`/home/user/verified_neovim` with `git archive` (7b87ce8 and HEAD fd8d324). `build.py`
accepted both, so every function's sha256 matches the pins. I did not run Frama-C (the
author runs the proofs and the mutants).

## Verdict

**Accept with changes.** The contracts are real functional specs and the build/strip pipeline
is faithful. Both findings are real. One runner bug (R1) and two stub-honesty problems (H1,
H2) must be fixed before the mutant run and the sign-off mean anything. One spec gap (S1)
should be closed. The rest is wording.

## What I checked and found sound

- **Macro expansion = the C preprocessor.** I put each original function, plus the
  `GA_APPEND` / `GA_DEEP_CLEAR` / `GA_DEEP_CLEAR_PTR` / `FREE_PTR_PTR` definitions taken from
  the pinned `garray.h`, through `gcc -E -P`. I did the same with the built file after
  stripping the ACSL and compared the two token streams. All 11 functions are token-identical
  in both trees, except `ga_append`, where the only difference is the declared tool patch
  (`uint8_t` becomes `char` plus the `(char)` cast). `expand()`'s `\b` substitution cannot
  hit `_gap`/`_item`, since `_` is a word character. No argument contains a macro that cpp
  would pre-expand.
- **Strip check.** `strip(annotated) == code` makes sure every insertion is a `/*@ */`
  comment. Ghost code (`concat_facts`, `dedup_facts`, ghost parameters) can only write ghost
  state, and the ghost functions are `assigns \nothing` and proved.
- **Tool patch.** Storing `(char)c` and storing the `uint8_t` `c` write the same byte (gcc
  and CBMC, both char signs). The harness is trivial but correct.
- **The contracts are functional, not "no crash".**
  - `ga_grow` pins the exact growth policy (`grown_up` / `grown_fix` match the code term for
    term), old bytes kept, new bytes zero, block identity (`vp_new_or_same`) and the
    allocation count.
  - `ga_concat_strings` states every byte of the result: string bytes at `off(k)`, separator
    bytes after each string but the last, and the NUL at `total`. Together these cover
    `[0, total]` completely.
  - `ga_remove_duplicate_strings` is exact for this code. `kept(k)` compares *sorted
    neighbours* `S[k-1], S[k]`, and that is what the loop does, because positions `< i`
    never move. It does not need `path_equal` to be transitive. Order, count and free order
    (last first) are all stated.
  - `ga_clear` and `ga_clear_strings` state the exact free log.
  - No precondition is unsatisfiable that I can see. The ghost `Ls`/`m` and `n` can always be
    built. All behaviors are reachable, and `complete`/`disjoint` is stated where there is
    more than one.
- **WP really checks `exits` clauses** (Frama-C 33 `cfgCalculus.ml` `do_exit` / `bhv_exits`,
  for any function with calls). So the fixed-tree exit conditions are proof obligations, not
  comments. Mutants `fix-grow-exit-off-by-one` and `fix-concat-strings-sep-check-one-more`
  are there to confirm this. Their normal-return ensures are vacuous on the exit path, so
  only the `exits` clause can catch them.
- **Differential test**: 624,339 checks, 0 mismatches, both trees, both char signs, ASan and
  UBSan (2000 iterations).
- **The fixes are correct and minimal.**
  - `ga_grow`: after the `n > INT_MAX - len` exit, each `MIN(…, room)` keeps
    `len + n <= INT_MAX`. When the cap does not apply, the code behaves exactly as upstream.
    A negative `ga_growsize` is still harmless.
  - `ga_concat_strings`: `slen > SIZE_MAX - len` is the exact no-wrap test.
    `nelem - 1 > (SIZE_MAX - len) / seplen` is exactly
    `(nelem-1)*seplen > SIZE_MAX - len`. `len == SIZE_MAX` is still left to `xmallocz`'s
    exit, as the contract's `T >= SIZE_MAX` says.

## Issues

### Must fix

**R1. `run_mutants.py` looks at the wrong text for 4 of the 11 functions.**
`function_span()` uses the regex `^[A-Za-z_][\w \*]*\bNAME\(` with no check for a definition.
For `ga_clear`, `ga_set_growsize`, `ga_grow` and `ga_concat_len` it first matches the PRELUDE
prototypes (`void ga_grow(garray_T *gap, int n);`). The span then runs to the first
`\n}\n`, which is the end of `ga_clear`'s body. I checked this on the built file: the spans
are 5,155 to 5,272 characters long and start at the prototype. So every `ga_grow` /
`ga_concat_len` / `ga_set_growsize` mutant reports "occurs 0 times" (ERROR). Worse, a mutant
whose `original` also appears in LOGIC or `ga_clear` would be applied to the wrong place.
*Fix:* skip prototype lines, for example
`r"^[A-Za-z_][\w \*]*\b" + re.escape(fn) + r"\((?![^\n]*\);\s*$)"`. I used exactly this regex
to confirm that every `original` in `mutants.toml` occurs once.

**H1. The default `exits \false` makes the stubs claim allocation never exits.**
Frama-C 33's `populate_spec.ml` gives every function without an `exits` clause the default
`exits \false`. `xrealloc` and `xstrdup` have no `exits` clause. `xmallocz` says
`exits size == SIZE_MAX`. Real `xrealloc`/`xmalloc` call `preserve_exit()` on out-of-memory,
so these trusted clauses are false in real Nvim. Normal-return ensures are not affected,
because a false `exits` only removes an exit path. But every proved `exits` clause is only
true *assuming no allocation runs out of memory*:
- fixed `ga_grow`, "exits only if `n > INT_MAX - ga_len`";
- `ga_concat_strings`, "exits only if total ≥ SIZE_MAX";
- the implicit `exits \false` of `ga_concat_len`, `ga_concat`, `ga_clear_strings` and the
  rest.

*Fix:* either give `xrealloc`/`xmallocz`/`xstrdup` an `exits \true` ("may exit on OOM") and
state each function's exit as "OOM, or …", or say plainly in CLAIM.md §2 that the exits
properties hold for runs where every allocation succeeds. The xmallocz comment ("preserve_exit()
if size + 1 wraps") also needs "or out of memory".

**H2. "`emsg` touches no growarray" is false for `capture_ga`.**
`ga_concat_len(capture_ga, str, len)` is how message.c (`redir_write`) records output for
`execute()`, `nvim_exec2(…, {output=true})` and `nvim_command_output`. If that call takes the
`too_long` branch, `emsg(E1240)` itself goes through `redir_write` and does
`ga_concat_len(capture_ga, " ", 1)` and `ga_concat_len(capture_ga, msg, …)`. Those appends
succeed whenever there are still a few bytes of room. So the proved `too_long: nothing
changes` (`ga_concat_len`, `ga_concat`) does not hold when `gap == capture_ga`. It is not
exploitable, but it is a trusted clause that is wrong about real Nvim.
*Fix:* either add a `requires` (or a CLAIM caveat) that `gap` is not the message-capture
array, or weaken the `too_long` postcondition to "ga_len does not shrink / the old bytes are
kept".

### Should fix

**S1. The tail of the array after `ga_concat_len` / `ga_concat` / `ga_append` is
unspecified.** `ga_grow` and `ga_append_via_ptr` state that the new bytes are zero.
`append_post` only covers `[0, new ga_len)`. A version that writes junk into the spare room
(`[new ga_len, ga_maxlen)`) proves. Gap probe `G-concat-len-dirty-tail` is predicted to
SURVIVE. *Fix:* add, for example,
`\forall integer i; \old(gap->ga_len) + n <= i < ga_bytes(gap) ==> data[i] == (i < \old(ga_bytes(gap)) ? \old(data[i]) : 0)`.

**S2. `sort_strings` is not stated to be a permutation.** The stub only says the result is
`vp_sorted` and consists of strings. "Frees exactly the dropped ones" is relative to `S`, and
CLAIM's "no leak" for `ga_remove_duplicate_strings` silently relies on `S` being a
permutation of the input. The stub is sound (weaker than the truth), but the claim is
stronger than what is proved. Add a permutation ensures to the stub (qsort guarantees it) or
qualify the sentence.

**S3. Not registered.** `garray` is in neither `vpipe.toml` nor `status.tsv`. The tool patch
is not declared as `[[framac.tool_patch]]`, although `tool_patches.py` says it is. CLAIM's
evidence table says "see PR" for WP: there is no proof log or count in the directory yet.

### Findings

**F1 `ga-grow-int-overflow.md`: real, severity right, two details wrong.**
- The threshold is off by one. `len + len/2` overflows only for `len >= 1,431,655,766`.
  `(INT_MAX-1)*2/3 = 1,431,655,764` is the bound written, and `len = 1,431,655,765` gives
  exactly `INT_MAX`. "The array is full" should read "less than n free".
- The Nvim reproducer does not overflow where the text suggests. `list_join_inner`
  pre-sizes with `ga_grow(gap, (int)sumlen + 2)`, so join's own array never regrows. The
  crash comes from `encode_tv2echo()`, which runs `ga_concat` on the 1.5e9-byte item (`len ==
  maxlen`) and then `ga_append(&ga, NUL)`. So the `'x'` is irrelevant, and simply echoing or
  stringifying any ≥1.43e9-byte string ends Nvim. That widens the reachability; say so.
- Out of scope but nearby: `list_join_inner`'s `(int)sumlen + 2` overflows `int` for
  `sumlen ∈ {INT_MAX-1, INT_MAX}` (UB) and truncates for larger sums. Note it for typval.c.

**F2 `ga-concat-strings-wrap.md`: real but latent, and the examples are wrong.**
- `(2^31-1) × 8 GiB = 2^64 − 2^33`, which does *not* wrap. `ga_len ≤ INT_MAX`, so
  "2^31 elements" is impossible, and `(2^31−2) × 2^33` does not wrap either.
- Upstream, F1 also stops a normally grown pointer array at about 1.43e9 items, so you need
  strings of about 12 GiB.
- Every current caller uses `sep` of length ≤ 1 ("\n", ",", "") and distinct heap strings.
  Each string then occupies `L+1` bytes, so `total < size of the address space` and the wrap
  is unreachable today, on any platform.
- Rewrite as "latent: needs one pointer stored many times, or a long separator". Fix the
  arithmetic, for example `2^31−1` copies of an 8 GiB + 8 byte string.

**Other bugs in garray.c:** none found. Upstream's `ga_append_via_ptr` `(int)item_size` and
the `GA_EMPTY_INIT_VALUE` array (itemsize 0) are caller contracts, and the preconditions
cover them.

### CLAIM.md wording (overstated)

- "no invalid conversion": `-wp-rte` does not check signed downcasts by default
  (`-warn-signed-downcast` is off). `(int)len` and `(int)item_size` happen to be in range
  under the preconditions, so the claim is true, but it is not what the tool checked.
- "results hold for signed and unsigned char": WP ran only on the x86_64 machdep (signed
  char). The unsigned case is argued and difftested, not proved.
- `ga_concat_strings` "exits when that length does not fit", fixed `ga_grow` "Nvim exits"
  only when …: these hold only without OOM (H1).
- §2 "emsg … change no growing array": see H2.
- `ga_remove_duplicate_strings` "no leak": see S2.
- The differential test never reaches the fixed/upstream difference (near `INT_MAX`) or any
  exit path. It is evidence for normal sizes only; say so in the evidence table.
- `x86_64` only. On 32-bit targets `new_size = itemsize * new_maxlen` can wrap `size_t`. That
  is not reachable in a 32-bit address space, but the platform line should keep saying
  x86_64.

## Planted bugs (`mutants.toml`)

There are 24 entries: 14 on upstream, 9 on the fixed tree (7 in `ga_grow` /
`ga_concat_strings`), and 1 gap probe. They cover all 11 functions. Each `original` occurs
exactly once in its function's definition in the built file (checked with the corrected span
regex), and every mutated file passes `gcc -fsyntax-only`.

- `fix-concat-strings-exit-at-boundary` is marked **equivalent**. It changes behaviour only
  when the partial sum is exactly SIZE_MAX, where the original exits too, so it may survive.
- `G-concat-len-dirty-tail` is predicted to **survive** until S1 is fixed.
- `fix-grow-exit-off-by-one` and `fix-concat-strings-sep-check-one-more` test that `exits`
  is enforced.
- `concat-strings-one-sep-too-many` tests that the upstream proof really covers the boundary
  near `SIZE_MAX`.

Fix R1 before running them.
