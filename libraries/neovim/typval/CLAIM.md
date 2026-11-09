---
entry: neovim/src/nvim/eval/typval.c, typval.h inlines (partial: see PROGRESS.md)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
fixed_fork: none needed so far (no bug found in a proved function)
toolchain: Frama-C 33.0 WP, Why3, Z3 5.1.0, CVC5 (pipeline toolchain, nixpkgs 5adc508)
strength: candidate   # needs the adversarial review and the owner's spec sign-off
tools: Frama-C WP (deductive, every input), Typed+Cast memory model, -wp-rte, -warn-signed-overflow, -warn-signed-downcast
platform: x86_64 (machdep x86_64). No proved function reads a plain `char` value except as a NUL test, so char signedness does not matter.
---

# Claim card: Neovim typval.c (first batch)

Also covered, each with its own RESULTS.md: `wp_blob/` (10 blob functions) and `wp_list/`
(6 linked-list functions); `wp_lnum/` (the line-number fix, findings/lnum-wraps.md).

`wp/build.py` copies the exact upstream text of each function (sha256 pinned in `wp/pins.txt`)
from `src/nvim/eval/typval.c` and `typval.h`. Contracts sit on prototypes in the prelude
(Frama-C joins them to the definition). The one loop annotation is a `/*@ */` comment, and
the build checks that removing it gives back the pinned text. Type definitions in the prelude
are copied from `typval_defs.h` / `hashtab_defs.h`; key lines are checked against upstream
(`CHECKS` in `wp/contracts.py`). Nothing is admitted; no axioms; `abort()` has precondition
`\false`, so WP proves it is never reached.

Run: `bash wp/run_wp.sh <neovim tree at the pinned commit> 20` (all goals proved = exit 0).
Planted bugs: `python3 -I wp/mutants.py <tree>` (13/13 caught).
Vacuity check: `SMOKE=1 bash wp/run_wp.sh <tree> 20` (2026-11-09: no contradictory callee
contract or dead code anywhere, except the `abort()` calls after the type switches, which are
dead by design). `wp_blob` and `wp_list` run smoke tests too (see their RESULTS.md).

## What is proved, for every input

"Message" = one call of `emsg`/`semsg`, modelled by a counter `vp_msgs` and a ghost `vp_last`
holding the message (format) pointer. All arguments are still evaluated, so overflow or bad
array reads in them are checked. Message identity is proved for the 21 `tv_check_for_*_arg`
functions, `tv_blob_check_index/range` (E979) and `value_check_lock` (which of the 4 lock
messages). Not proved: the identity of messages given as string literals (e.g. the E805/E745
texts in `tv_check_str_or_nr`, `tv_get_float`), and the values of format arguments
(the argument number `idx + 1`, the index printed by E979). Review (REVIEW.md) issue 2.

| Function | Property |
|---|---|
| `tv_list_len`, `tv_blob_len` | 0 for NULL, else the stored length |
| `tv_list_locked` | `VAR_FIXED` for NULL, else `lv_lock` |
| `tv_list_uidx(l, n)` | `n` if `0 <= n < len`; `n + len` if `n < 0` and that is in range; else -1 |
| `tv_blob_get(b, i)` | byte `i` of the data (valid index required, as documented) |
| `tv_check_str_or_nr` / `tv_check_num` / `tv_check_str` | true exactly for the accepted types ({Number, String} / {Number, Bool, Special, String} / those plus Float); otherwise false with one message; never reaches `abort()` |
| `tv_islocked` | true iff the value is `VAR_LOCKED`, or it is a non-NULL List/Dict whose own lock is `VAR_LOCKED` |
| `tv2bool` | the documented truth value for each of the 11 types (NULL/empty string, list, dict, blob are false) |
| `tv_get_float` | the Number converted to double, the Float itself, else 0 with one message |
| `check_repeat_count(slen, n)` (slen > 0) | OK iff `n <= INT_MAX / slen`, and then `n * slen <= INT_MAX` (no overflow in the caller's product); else FAIL with one message |
| `tv_blob_check_index(len, n1, quiet)` | OK iff `0 <= n1 <= len` (`len` itself allowed: append position); else FAIL, one message unless quiet |
| `tv_blob_check_range(len, n1, n2, quiet)` | OK iff `n1 <= n2` and `0 <= n2 < len`; else FAIL, one message unless quiet |
| `tv_blob_equal(b1, b2)` | true iff same length (NULL = empty) and the same bytes |
| `tv_get_number_chk(tv, err)` | Number: the value; String: 0 for NULL, else the value `vim_str2nr` stores (uninterpreted function of the string); Bool: 1/0; Special: 0; other types: one message, and `*err = true`, result 0 if `err` given, else -1 |
| (all three) | on success `*err` is not touched (review issue 1, fixed) |
| `tv_get_bool_chk`, `tv_get_bool` | the same as `tv_get_number_chk` (with `err`, resp. NULL) |
| `tv_callback_equal` | true iff same type and equal payload (string equality for Funcref/Expr by `strequal`'s proved contract; pointer/ref equality for Partial/Lua) |
| `value_check_lock(lock, name, len)` | true iff `lock != VAR_UNLOCKED`, and then exactly one message; `assert(error_message != NULL)` proved |
| `tv_check_lock(tv, name, len)` | true iff the value's lock or its Blob/List/Dict's lock is set; exactly one message when true |
| `tv_get_string_buf_chk(tv, buf)` | String: the string itself (NULL string: a non-NULL empty literal); Number/Float/Bool/Special: `buf`, holding a NUL-terminated string within `NUMBUFLEN`; other types: NULL with one message (`str_errors[type]`). The digits written are not specified (snprintf is trusted) |
| `tv_get_string_buf(tv, buf)` | the same, but never NULL (error: an empty literal, not `buf`) |
| `tv_dict_wrong_func_name(d, tv, name)` | true iff `d` is g: or the current l: scope, the value is a Funcref/Partial, and `var_wrong_func_name(name)` says the name is wrong; no message otherwise. The three callees are modelled by their results only |
| `tv_dict_watcher_matches(w, key)` | pattern ending in `*`: true iff `key` starts with the pattern minus the `*`; otherwise true iff `key` equals the pattern (pattern length = `key_pattern_len`) |
| 21 `tv_check_for_*_arg(args, idx)` | OK iff `args[idx]` has an accepted type (the `opt_` forms also accept `VAR_UNKNOWN`; `bool` also accepts Number 0/1; `nonempty_string` needs a non-NULL non-empty string; `nonnull_dict` a non-NULL dict); else FAIL with exactly one message |

## Assumptions (preconditions) and trusted base

- Pointers are valid as the functions' NONNULL attributes and docs say; types are in the
  `VarType` range.
- `tv_check_for_*_arg`: `0 <= idx <= MAX_FUNC_ARGS` (arguments are counted by the evaluator,
  at most 20). Needed only for the `idx + 1` in the message.
- `check_repeat_count`: `slen > 0`; all three callers (funcs.c repeat_list/blob/string) test this first.
- `value_check_lock` / `tv_check_lock`: the name length (given, or `strlen(name)`) is at most
  `INT_MAX`, because the code converts it with `(int)name_len` for `%.*s`. Above that the
  conversion is implementation-defined (the message would print a different length; no memory error).
- `vim_str2nr` (charset.c) is modelled by its effect only: it writes `*nptr` with a value that
  depends on the string and the old `*nptr`. Its own proof belongs to the charset.c claim (PR #3).
- `strequal`: the contract proved in `memory/wp`. `strlen`: the libc contract used in `memory/wp`.
- `snprintf`/`vim_snprintf` into a `NUMBUFLEN` buffer: write only the buffer and leave a string
  there; `strcpy` of `encode_bool_var_names`/`encode_special_var_names` (short strings, separate
  from `buf`): writes only `buf`.
- `emsg`, `semsg`, `vim_snprintf` are stubs (messages only; `vim_snprintf` writes only `buf`).
- `struct dictvar_S` is copied up to `dv_hashtab`; later fields (used-list links, watchers)
  are left out because no proved function reads them. `listitem_S.li_tv` is left out for the same reason.
- Frama-C, WP, Why3, Z3, CVC5 are trusted.

## Not covered

Everything listed as unverified in `PROGRESS.md`, including all of `typval_encode.c.h`.
