# Adversarial review: typval WP proofs (wp/)

Reviewer: Claude (adversarial review session), 2026-11-09. Pinned tree `/home/user/nv-upstream` (7b87ce8).
Specs were checked against the doc comments in `src/nvim/eval/typval.c` / `typval.h` and against the callers
(`eval.c` blob indexing, `funcs.c` repeat_*), not against the code.

## Verdict: **accept with changes**

The behavioural specs (return values, accepted types, message *count*, lock logic, index normalisation,
overflow guard) match the documented meaning and are strong: 20/20 behavioural mutants were caught, and smoke
tests show no vacuous preconditions. Two things must change before the claim is upgraded from `candidate`:
one real spec gap (issue 1: `*ret_error` is not framed on success) and an honest restatement of what
"one message" means (issue 2), plus a small CLAIM.md correction (issue 3).

## Issues

### 1. `tv_get_number_chk` / `tv_get_bool_chk`: `*ret_error` may be written on success — **medium (real gap)**
Doc (typval.c:4283): "If type error occurred then `true` will be written to this location. **Otherwise it is
not touched.**" The spec has `assigns vp_msgs, *ret_error;` and the `good` behavior says nothing about
`*ret_error`. Mutant R26 (set `*ret_error = true` before returning a valid Number) is **proved** (106/106).
Callers (e.g. `tv_get_number_chk(&argvars[1], &error)` chains in funcs.c) initialise `error = false` once and
call several times, so a spurious write would turn a valid call into a reported error.
**Change:** in behavior `good` add `ensures ret_error != \null ==> *ret_error == \old(*ret_error);`
(or split `assigns` per behavior: `good` → `assigns vp_msgs;`). Same for `tv_get_bool_chk`.

### 2. Messages are counted, never identified — **low/medium (abstraction; must be stated)**
`emsg`/`semsg` are a counter. So a wrong message text, wrong message for the case, or wrong
argument (blob index, argument number) is not detected: mutants R21–R24 all **proved** (wrong E-number in
`tv_check_str_or_nr`, `e_cannot_change_value` instead of `e_value_is_locked`, `n1` instead of `n2` in
`tv_blob_check_range`'s E979 message, `idx` instead of `idx + 1` in an argument-number message). These are
user-visible behaviours the docs describe ("Give an error ... unless args[idx] is ..." with "argument %d").
**Change (preferred):** make the stubs record the message: e.g. `//@ ghost const char *vp_last_msg; ghost long vp_last_arg;`,
`vp_emsg(const char *m)` with `ensures vp_last_msg == m`, `semsg` passing its first vararg as `vp_last_arg`
when it is an integer; then for the 21 `tv_check_for_*_arg` specs add
`ensures vp_last_msg == e_..._required_for_argument_nr && vp_last_arg == idx + 1` in `bad`, and the
expected message in `value_check_lock` (locked vs fixed, with/without name) and `tv_blob_check_range` (`n2`).
**Minimum:** state in CLAIM.md that the message identity and its arguments are not verified.

### 3. CLAIM.md says message "arguments are still evaluated" — true for `semsg`, false for `emsg` — **low**
`#define emsg(...) vp_emsg()` drops its argument, so e.g. `num_errors[tv->v_type]` (tv_check_num,
tv_get_number_chk) is never RTE-checked. It is in range here (v_type ≤ VAR_BLOB, array size VAR_BLOB+1 as
upstream), so no hidden bug, but the claim text is inaccurate. **Change:** `#define emsg(m) ((void)(m), vp_emsg())`
or fix the sentence. Note upstream `num_errors[VAR_BOOL/VAR_SPECIAL/VAR_STRING/VAR_NUMBER]` are NULL; the
proof of "never reached for those types" comes from the behaviours, which is fine.

### 4. `run_wp.sh` comment: "only expected Doomed results are the abort() calls" — **low (doc)**
`SMOKE=1` on `tv_check_lock` gives one Doomed goal (`dead_code_s301`, tv.c line of
`return value_check_lock(...) || (lock != VAR_UNLOCKED && value_check_lock(lock, ...))`). This is genuinely
dead: the second `value_check_lock` is only called with a non-UNLOCKED lock and then always returns true,
so its "false" continuation is unreachable. Not vacuity, but the comment/claim should list it.
Smoke-tested clean (no Doomed): tv_get_number_chk, value_check_lock, tv_blob_equal, tv2bool,
check_repeat_count, tv_check_for_nonempty_string_arg, tv_list_uidx; tv_callback_equal only abort().

### 5. `tv_blob_check_range` accepts negative `n1` — **info**
Doc: "Check if n1-n2 is a valid range". The code (and the spec, faithfully) returns OK for `n1 < 0 <= n2 < len`.
The only caller (eval.c:980–985) calls `tv_blob_check_index` on `n1` first, so `n1 ∈ [0, len]` there. The claim
row states exactly "OK iff n1 <= n2 and 0 <= n2 < len", which is correct; consider adding a note that the
function itself does not check `n1 >= 0`.

### 6. Preconditions/stubs/prelude — checked, no problem found
- `check_repeat_count` `slen > 0`: all three funcs.c callers check `slen == 0`/`<= 0` and `n <= 0` first. The
  `n * slen > INT_MAX` post in `too_large` is correct (floor division).
- `tv_check_lock`/`value_check_lock` `lock_ok` and `name_len <= INT_MAX`: reasonable (enum values; real names short).
- `tv_check_for_*_arg` `idx <= MAX_FUNC_ARGS`: fine (only used for `idx + 1`).
- `vim_str2nr` stub pins the call shape (`what == STR2NR_ALL`, NULL out-params); a different call shape fails
  the stub precondition rather than proving silently. `num_value` uses `str2nr_all(s, 0)`, so a wrong initial
  `n` is caught (R9).
- Truncated `dictvar_S`, `listitem_S` without `li_tv`: no proved function reads the missing fields; with the
  Typed model layout does not matter. Enum values and key fields are checked by `CHECKS`.
- `strequal`, `strlen` contracts match libc/memory-wp semantics; `abort()` with `requires \false` is correct.

## Mutant results (`python3 -I wp/review_mutants.py /home/user/nv-upstream`)

The script adds a guard (vs. mutants.py) that the replaced text's first occurrence lies inside the target
function's body, so a mutant cannot silently land in the prelude or another function.

| # | Function | Mutation | Result |
|---|---|---|---|
| R1 | tv_list_uidx | `n < 0` → `n <= 0` (normalise 0) | caught |
| R2 | tv_list_locked | NULL → `VAR_LOCKED` instead of `VAR_FIXED` | caught |
| R3 | tv_check_str_or_nr | Special accepted silently | caught |
| R4 | tv2bool | float `!= 0.0` → `> 0.0` | caught |
| R5 | tv2bool | dict `ht_used` → `ht_filled` | caught |
| R6 | tv2bool | UNKNOWN → true | caught |
| R7 | tv_get_number_chk | swap -1/0 error results | caught |
| R8 | tv_get_number_chk | Special → 1 | caught |
| R9 | tv_get_number_chk | str2nr initial `n = 1` | caught |
| R10 | tv_get_float | no message for UNKNOWN | caught |
| R11 | tv_callback_equal | None/None → false | caught |
| R12 | tv_callback_equal | luaref `==` → `<=` | caught |
| R13 | tv_check_lock | `||` → `|` (two messages) | caught |
| R14 | value_check_lock | FIXED leaves message NULL (assert) | caught |
| R15 | check_repeat_count | `<=` → `<` | caught |
| R16 | tv_islocked | drop dict NULL check | caught |
| R17 | tv_blob_equal | same pointer → false | caught |
| R18 | tv_check_for_opt_bool_arg | UNKNOWN → FAIL | caught |
| R19 | tv_check_for_nonnull_dict_arg | `== NULL` → `!= NULL` | caught |
| R20 | tv_blob_len | NULL → 1 | caught |
| R21 | tv_check_str_or_nr | wrong error text for Float (E745) | **MISSED** (issue 2) |
| R22 | value_check_lock | "cannot change" instead of "is locked" | **MISSED** (issue 2) |
| R23 | tv_blob_check_range | message prints `n1` not `n2` | **MISSED** (issue 2) |
| R24 | tv_check_for_float_or_nr_arg | argument number `idx` not `idx + 1` | **MISSED** (issue 2) |
| R25 | tv_check_for_opt_string_arg | delegate to string_or_number check | caught |
| R26 | tv_get_number_chk | writes `*ret_error = true` on a valid Number | **MISSED** (issue 1, verified by a single-function run: 106/106; added to the script after the 25-mutant run) |

Totals: 21/26 caught. All 5 misses are non-equivalent, user-visible bugs → spec weaknesses (issues 1 and 2).
Equivalent mutant noted but not listed: dropping `lock != VAR_UNLOCKED &&` in `tv_check_lock`
(value_check_lock(UNLOCKED) is false and silent).
