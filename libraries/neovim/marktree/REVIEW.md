# Adversarial review: marktree.c leaf-function proofs

Reviewed 2026-11-09, fixed mode (upstream 7b87ce8 plus the meta_has fix), tree `/home/user/verified_neovim`.
Files reviewed: `wp/build.py`, `wp/contracts.py`, `wp/run_wp.sh`, `wp/stubs/vp_marktree.h`, `cbmc/harness.c`, `cbmc/run_cbmc.sh`.

## Verdict

**The proofs hold, and the specifications are strong.** The baseline re-run passes: WP proves every goal (lemmas 7/7, all 14 WP functions), and CBMC verifies all 8 meta_* configurations.
Every contract is a full functional specification, not just a safety property. 20 of 20 non-equivalent mutants were caught, and every proved function caught at least one. That last point also shows that no function's preconditions are inconsistent, so no proof is vacuous: a proof under contradictory `requires` would pass every mutant.
The issues below concern the trusted base, meaning the guards that tie the proof file to the real source. They do not concern the specs. None of them makes a current result wrong.

## Issues (most severe first)

### 1. MEDIUM: the strip check does not guarantee verbatim code
`build.py` inserts each annotation as `/*@ {annot} */` and then checks that `strip(ann) == piece`. The first `strip` regex is `^[ \t]*/\*@.*?\*/\n` with `re.S`. Because a match must end in `*/\n`, it runs past an inner `*/` that is not followed by a newline.
So an annotation such as `loop variant x->size - i; */ if (id == 7) { return true; } /*@ assert \true;` passes the check, and real C code ends up in `mt.c`.
I confirmed this in a scratch copy: the build printed OK, and `mt.c` contained `if (id == 7) { return true; }` inside `intersection_has`.
The contract text `C[name]` and `LOGIC` are not checked at all. A `*/` inside either one would also inject code. Today nothing contains a stray `*/`: I checked every contract and annotation in both modes, and `LOGIC` contains only its closing one.
**Fix:** in `build.py`, reject any annotation, contract or LOGIC text that contains `*/` or `/*`. Better still, compare the token stream of `mt.c` after preprocessing with comments removed (`gcc -fpreprocessed -dD -E`) against the pinned pieces.

### 2. LOW–MEDIUM: the prelude check matches lines as a set, not in order
`check_prelude` only asks whether each prelude line appears *somewhere* in `marktree.h`, `marktree_defs.h` or `kvec.h`. So it accepts:
- reordered fields (I confirmed it accepts `id`/`ns` and `level`/`p_idx` swapped)
- a field line copied into another struct (for example `  int i;`, `};` and `  MTPos pos;` all appear in many places)
- duplicated lines
- headers that add a field the prelude lacks.

None of this matters for the current functions, which access fields by name. Still, the check is weaker than "copied as declared". The `EXEMPT` prefixes (`typedef struct { void`, `typedef struct { size_t size`, `  MTKey key[`, `// `, `/*@`) are not checked at all.
**Fix:** compare whole struct and enum blocks in order, for example by extracting each `typedef struct { ... } Name;` block from the header and diffing it.

### 3. LOW: the prelude layout differs from the real types
- `DecorInlineData` is an opaque `struct { void *opaque; }`, while the real type is a union.
- `struct mtnode_s` lacks the flexible member `struct mtnode_inner_s s[]`.
- `Intersection` is restated rather than expanded from `kvec_withinit_t`. The build does check that the field order matches, through the typedef line check plus a manual read of `kvec.h`.

`sizeof(MTKey)` and `sizeof(MTNode)` therefore differ from the real build. No proved function depends on size or offset: `itr_eq` compares addresses of `key[i]` in the same model. So the results are unaffected, but this would matter for any later function that does pointer arithmetic over nodes.

### 4. LOW: caller obligations are assumed, not proved
These preconditions are reasonable B-tree or buffer invariants, but nothing yet discharges them at the call sites:
- `keys_sorted(x)` for `marktree_getp_aux`
- `sorted_u64` for `intersection_has` and `intersect_item_pos`
- `pos_ok` (non-negative and ≤ INT_MAX) together with "the absolute position fits" for `relative`, `unrelative`, `compose` and `marktree_itr_pos`.

`intersection_has` really is wrong on an unsorted array: its early `>= id` exit returns false. Its spec states that dependence honestly.
Non-negative positions are an assumption about callers such as `marktree_splice` and `marktree_move`, which do delta arithmetic. That is worth checking when they are verified (PLAN step 4).

### 5. LOW: model and tool caveats
- `-wp-model Typed+Cast` is not sound for arbitrary heterogeneous casts. The WP-proved functions contain no casts, so it is harmless here.
- `-wp-rte` does not check unsigned wraparound. That is correct for these functions: `intersect_item_pos` uses `lo + (hi - lo) / 2`, and the meta counters wrap on purpose (their CBMC spec is mod 2^32).
- `assert` is mapped to a proof obligation, which is stronger than release builds where `NDEBUG` removes it. This is fine.

### 6. INFO: WP contracts for meta_* exist but WP never runs them
`contracts.py` has WP contracts for `meta_describe_key_inc`, `meta_describe_key` and `meta_has`. The default `FUNCS` in `run_wp.sh` leaves them out, and those functions are proved only by CBMC. That CBMC proof is complete: the loops are bounded at 5, `--unwinding-assertions` is on, and inputs are fully nondeterministic.
The WP contracts should either be marked "not run (CBMC is the proof)" or be run, so nobody cites them as proved.

### 7. INFO: notes on the specs (no weakness found)
- `marktree_getp_aux`: the postconditions fix the result uniquely: the first equal key if there is a match, otherwise the last smaller key, or -1. The contract also documents that the doc comment's "0 to x->n" is wrong.
- `key_cmp`: the spec is exact (`\result == kcmp`). The flag mask and flag values are checked against the source.
- `itr_eq`: address equality, plus a clause that reads it as "same node and same index" for separated nodes.
- `meta_has` (CBMC): exact for every filter, with and without the documented filter shape (`DOC_FILTER`).
- I found no inconsistent requires and no unsound lemma. The 7 lemmas are proved, not admitted, and `run_wp.sh` rejects `admit`, `axiom` and `check`.

## Mutation results

All 21 mutants are in `mutants.toml`. Each one edits one function in a scratch copy of `src/nvim`, and the sha256 is updated in a scratch copy of `wp/`.

| Result | Count |
|---|---|
| Non-equivalent mutants caught | **20 / 20** |
| Equivalent mutant (kept on purpose as a control) survived | 1 / 1 |

Caught, by function:
- `pos_leq` 1/1
- `pos_less` 1/1
- `relative` 1/1
- `unrelative` 1/1
- `compose` 1/1
- `key_cmp` 1/1
- `marktree_getp_aux` 3/3
- `intersection_has` 1/1
- `intersect_item_pos` 2/2
- `marktree_itr_node_done` 1/1
- `marktree_itr_pos` 1/1
- `itr_eq` 1/1
- `meta_describe_key_inc` 2/2 (CBMC)
- `meta_describe_key` 1/1 (CBMC)
- `meta_has` 2/2 (CBMC).

The survivor is mutant 11, `intersection_has` with `>= id` changed to `> id`. It is equivalent under the `sorted_u64` precondition, because an equal item has already returned true, so surviving is correct.

For mutant 20 (`meta_has` loop bound `- 1`), the build first rejected the mutant because the WP loop-annotation anchor no longer matched. That is a build-level catch, not a proof catch. With the anchor adjusted in the scratch `contracts.py`, CBMC caught it in all 4 configurations.
WP mutants show up as unproved (`Timeout`) goals, because WP gives no counterexamples. In every case the unproved goal was a function `ensures`, a loop invariant, or an overflow check that the mutant really breaks.
