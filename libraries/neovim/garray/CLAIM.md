---
entry: neovim/src/nvim/garray.c (all 11 functions)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
fixed_fork: https://github.com/blooddimmedtide/verified_neovim (branch claude/project-thread-aslfna: ga_grow 850a906, ga_concat_strings dec9b23; PR #5 into verified)
toolchain: Frama-C 33.0 WP, Why3, Z3 5.1.0, CVC5 1.4.0 with --full-saturate-quant (tools/install.sh); CBMC 6.4.1 for the tool patch; gcc for the differential test
container: ubuntu:24.04@sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac (CI)
strength: candidate   # becomes full-correctness after the review, planted bugs and the owner's spec sign-off
tools: Frama-C WP (deductive, unbounded: every length, every input), Typed+Cast memory model, -wp-rte
platform: x86_64 (machdep x86_64, char signed: what WP proves); unsigned char is covered by the differential test and the CBMC tool-patch check, not by WP
---

# Claim card: Neovim garray.c

`wp/build.py` copies the exact pinned text of each function (sha256 checked; the fixed
fork's text for `ga_grow` and `ga_concat_strings` in mode `fixed`), expands the two garray.h
macros the file uses from the header's own pinned text, applies one declared tool patch, and adds
ACSL as comments only. It checks that removing the comments gives back that text exactly.
Nothing is admitted; no axioms. Every function, both ghost lemma functions and the lemma are
proved in their own WP run, upstream and fixed.

"A well-formed array" (`ga_ok`): `0 <= ga_len <= ga_maxlen`, `ga_itemsize >= 1`, `ga_data`
valid for `ga_itemsize * ga_maxlen` bytes and not inside the `garray_T` itself. `ga_init` creates
one, every function below keeps it.

## What is proved, for every input

| Function | Property |
|---|---|
| `ga_init(gap, itemsize, growsize)` | empty array (`ga_data` NULL, lengths 0), `ga_itemsize = itemsize`, `ga_growsize = max(growsize, 1)` |
| `ga_set_growsize(gap, g)` | `ga_growsize = g` if `g >= 1`, else 1; nothing else changes |
| `ga_clear(gap)` | frees `ga_data` (exactly one `xfree` call, with that pointer), then `ga_data` NULL and both lengths 0; item size and growsize kept |
| `ga_clear_strings(gap)` | if `ga_data` is not NULL, frees `ga_data[0 .. ga_len-1]` in order and then the array (`ga_len + 1` frees, nothing else); otherwise one `xfree(NULL)`; then as `ga_clear` |
| `ga_grow(gap, n)` | if `ga_maxlen - ga_len >= n`: nothing changes. Otherwise `ga_maxlen` becomes `ga_len + max(n, growsize, ga_len / 2)` (fixed: `growsize` and `ga_len / 2` capped at `INT_MAX - ga_len`), so there is room for `n` more items; the old bytes are kept, the new bytes are zero; the array is the same block or a new one (never another live object); fixed only: if `n > INT_MAX - ga_len`, Nvim exits (`preserve_exit`) |
| `ga_concat_len(gap, s, len)` | (byte arrays) `len == 0`: nothing; `len > INT_MAX - ga_len`: `emsg(E1240)`, nothing changes; else the bytes `s[0 .. len-1]` are appended, earlier bytes kept, the bytes after the new end are the old ones (or zero where the array grew), `ga_maxlen` as `ga_grow(gap, len)` |
| `ga_concat(gap, s)` | `s == NULL`: nothing; else as `ga_concat_len(gap, s, strlen(s))` (the NUL is not copied) |
| `ga_append(gap, c)` | (byte arrays) one more byte `(char)c`, earlier bytes kept, later bytes as for `ga_concat_len`, `ga_maxlen` as `ga_grow(gap, 1)`; fixed: exits instead of overflowing at `INT_MAX` bytes |
| `ga_append_via_ptr(gap, size)` | (`size == ga_itemsize`) one more item; returns `ga_data + size * old ga_len`, valid for `size` bytes; old bytes kept, new bytes zero |
| `ga_concat_strings(gap, sep)` | a new string: `""` for no items, else item 0, `sep`, item 1, ..., item n-1, NUL (every byte at its position stated); exits (`preserve_exit`) when that length does not fit in `size_t` (upstream: only proved when the sum does not wrap, see findings) |
| `ga_remove_duplicate_strings(gap)` | with S the order `sort_strings` gives: keeps S[0] and every S[k] not `path_equal` (literal) to S[k-1], in order; frees exactly the dropped ones (last first); `ga_len` is the number kept |

All functions: no undefined behavior (`-wp-rte -warn-signed-downcast`: every memory access
valid, no signed overflow, every signed narrowing conversion in range), and they terminate
(loop variants). The exact allocation counter (`vp_live`) change and the exact list of freed
pointers are part of each contract.

**When a function may exit.** Allocation can run out of memory, and then memory.c calls
`preserve_exit()`. The stubs model this with a ghost flag `vp_oom` (never set): every `exits`
clause reads "`vp_oom` or <condition>". So, apart from running out of memory, the functions
never exit, except fixed `ga_grow` (and `ga_append`, `ga_append_via_ptr` through it) when
more than `INT_MAX` items would be needed, and `ga_concat_strings` when the result length does
not fit in a `size_t`; there they exit and never return.

## Findings (see ../findings/)

1. `ga_grow` (`ga-grow-int-overflow.md`): `int` overflow once an array holds more than about
   1.43e9 items. Reproduced in released Nvim 0.9.5: `join([repeat('a', 1500000000), 'x'], '')`
   exits with "E41: Out of memory!". Upstream is proved under the condition
   `ga_len + max(n, growsize, ga_len / 2) <= INT_MAX`, which is exactly where it is correct;
   the fixed version is proved without it. `ga_concat_len`, `ga_concat`, `ga_append`,
   `ga_append_via_ptr` inherit the same condition upstream and none in the fixed code.
2. `ga_concat_strings` (`ga-concat-strings-wrap.md`): the length sum can wrap (needs a true
   length of 2^64 bytes). Upstream proved when it does not wrap; fixed proved for every input.

## What the proof relies on

1. **Frama-C WP, Why3 and the provers are sound** (Z3, CVC5), in the Typed+Cast model
   (memory of different C types does not overlap; garray.c never reinterprets memory except
   the one store covered by the tool patch).
2. **The callee contracts in `wp/stubs/vp_garray.h` and `memory/wp/stubs/vp_string.h`**:
   - `xrealloc` never returns NULL (memory.c exits on failure), returns a block valid for the
     new size whose first bytes are the old ones, and that is either the old block or not part of
     any object live before the call. `xmallocz`, `xstrdup`: a new block (string) as memory.c
     defines them. `xfree`: only logs the pointer (ghost `vp_freelog`).
   - `xstpcpy`: the contract proved in `../memory` (not re-proved here).
   - `strlen`, `strcpy`, `memcpy`, `memset`: C11 7.24.
   - `preserve_exit` never returns. `WLOG` logging (replaced by `vp_wlog()` in the prelude) only
     writes the log file. `emsg` changes no growing array except `capture_ga` (message.c appends
     captured output to it during `execute()` / `nvim_exec2`), so `ga_concat_len` and `ga_concat`
     require `gap != capture_ga` (found by the review).
   - `sort_strings` (strings.c) reorders the pointers into some order (uninterpreted
     `vp_sorted`) and keeps them strings; `path_equal(.., kPathCmpLiteral)` (path.c) has no
     side effects and its answer depends only on the two strings and 'fileignorecase'
     (uninterpreted `vp_path_eq`). Neither is proved here; their own proofs belong to
     strings.c and path.c. The `sort_strings` contract does not say the new order is a
     permutation of the old one, so "frees exactly the dropped ones" is relative to the sorted
     array: that no string is lost or duplicated by the sort is `sort_strings`'s (qsort's) job.
3. **Preconditions** (each function's `requires`):
   - a well-formed array (`ga_ok`) where the function reads the array's layout;
   - `ga_concat_len`, `ga_concat`, `ga_append`: byte arrays (`ga_itemsize == 1`), as their doc
     comments say ("a growarray which contains characters/bytes");
   - `ga_concat_len`, `ga_concat`: the source is not inside the array's block (doc: "may not
     overlap with the growing array");
   - `ga_append_via_ptr`: `item_size == ga_itemsize` (the function logs a wrong size as an error);
   - string functions: every item and `sep` are strings, each shorter than `PTRDIFF_MAX`;
   - ghost counters stay in range (`vp_live`, `vp_nfree`: at most 2^32 logged frees).
4. **One tool patch** (`wp/tool_patches.py`): `GA_APPEND`'s store
   `((uint8_t *)(gap)->ga_data)[(gap)->ga_len] = (c);` is read as
   `((char *)(gap)->ga_data)[(gap)->ga_len] = (char)((c) - ((c) > 127 ? 256 : 0));` (WP keeps
   `uint8_t` and `char` views apart; the subtraction keeps the `char` conversion in range, so
   `-warn-signed-downcast` has nothing to assume). `equiv/append_store.c` proves with CBMC, no assumptions, signed and unsigned char,
   that both stores leave identical bytes for every value and index (the signed run also checks that
   no conversion overflows).
5. **Macro expansion** of `GA_DEEP_CLEAR_PTR` / `GA_DEEP_CLEAR` / `GA_APPEND` is done by
   `build.py` from the pinned header text (substituting the arguments, as cpp does), so that loop
   annotations can be placed inside the macro's loop.

## Not covered / notes

- `ga_remove_duplicate_strings` on an array that was never grown calls
  `sort_strings(NULL, 0)`, i.e. `qsort(NULL, 0, ...)`, which C11 leaves undefined (glibc
  accepts it). That call is in strings.c; noted for its proof.
- The contracts of `vp_sorted`'s order (sortedness by `strcmp`) are not stated: the result is
  described for whatever order `sort_strings` produces.
- The differential test does not reach the `INT_MAX` / `SIZE_MAX` boundaries or the exit paths;
  those are covered by the proof only.

## Evidence

| Check | Upstream | Fixed |
|---|---|---|
| WP, every function, lemma and ghost lemma function (`bash wp/run_wp.sh <tree> upstream\|fixed 60`) | 428 / 428 goals | 463 / 463 goals |
| Tool patch (`bash equiv/run_equiv.sh`) | 2/2 (signed, unsigned char) | same |
| Differential test (`bash difftest/run_difftest.sh <tree> <mode> 20000`), ASan/UBSan, gcc -O2 | 6,206,577 checks, 0 mismatches, both char signs | same |
| Reviewer's planted bugs (`python3 -I run_mutants.py <up> <fixed>`, `mutants.toml`) | 24 / 24 caught (`mutants_result.tsv`) | (both trees in one run) |

Note on the planted bugs: `fix-concat-strings-exit-at-boundary` (exit when the partial sum is
exactly `SIZE_MAX`) was predicted equivalent. It is caught, but only by a helper `assert` inside
the proof (`sumL(Ls, i + 1) > SIZE_MAX`), not by the contract: the contract's exit condition
(total length `>= SIZE_MAX`) allows that mutant. With respect to the stated contract it is
equivalent, as the reviewer said.
