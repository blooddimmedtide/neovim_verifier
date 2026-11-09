# Claim: src/nvim/digraph.c (partial, in progress)

Upstream: blooddimmedtide/verified_neovim @ 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd.
Code is extracted verbatim by `cbmc/extract.py`, pinned by sha256 in `cbmc/pins.txt`.
Tool: CBMC 6.4.1, x86_64, `--bounds-check --pointer-check --signed-overflow-check --conversion-check
--unwinding-assertions`, both `char` signednesses.

| Function | Status | Evidence |
|---|---|---|
| check_digraph_chars_valid | proved (candidate) | `cbmc/harness.c` check_valid: result == (char2 != 0 && no ESC) and exactly one error message on rejection, for all int inputs. Relies on a contract stub for `utf_char2bytes` (writes 1..4 bytes; mbyte proof) and message stubs. |
| getexactdigraph | open | harness `check_exact` against `spec.h` written; CBMC over the full 1,400-entry built-in table did not finish in 5 min. Next: split the table into chunks or prove with WP. |
| digraph_get | open | harness `check_get` written, not run (same cost). |
| registerdigraph | finding; partial fix proved | multibyte chars truncated to one byte: `../findings/digraph-char-truncation.md`, `cbmc/repro_truncation.c`. `cbmc/harness_register.c`: "after registering (c1,c2)->n, the table holds exactly one entry for (c1,c2) and it yields n" for all accepted codepoints, user table up to 2 entries. Upstream FAILS (counterexample = truncation); with `digr_T` widened to `int` (`-DFIXED`) it is SUCCESSFUL, both signednesses. Relies on a garray append model (one free slot, no growth/OOM) and the no-duplicate-pairs table invariant. The fix is not complete: the printing paths still cast chars to bytes, and the fix branch is not pushed. |
| all other functions in digraph.c (do_digraph, get_digraph_for_char, get_digraph, putdigraph, digraph_header, listdigraphs, digraph_getlist_appendpair, digraph_getlist_common, printdigraph, get_digraph_chars, digraph_set_common, f_digraph_get, f_digraph_getlist, f_digraph_set, f_digraph_setlist, keymap_init, ex_loadkeymap, keymap_ga_clear, keymap_unload, get_keymap_str) | open | not started |

Run: `cbmc/run_cbmc.sh`.

Not done yet: difftest, mutation review, vpipe.toml target, status.tsv rows.
