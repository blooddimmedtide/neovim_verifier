# src/nvim/quickfix.c (work in progress, stopped 2026-11-09 ~08:56 UTC at the sprint deadline)

Nothing here is a candidate yet. CBMC harness for the 'errorformat' helpers is in `cbmc/`
(verbatim, sha256-pinned extraction via `build.py`; references in `spec.h`; one run per
concrete exact-size string length). Run: `bash cbmc/run_cbmc.sh <neovim tree at pinned commit> 3`.

Results so far (`cbmc/results_len3.txt`, CBMC 6.4.1, signed char only, x86_64):

| Function | Status |
|---|---|
| efm_option_part_len | matches reference + memory safe for lengths 0..3 (bounded; no unbounded proof yet) |
| efm_analyze_prefix | harness FAILS for lengths >= 1, not yet diagnosed (harness/spec bug or code bug unknown) |
| efm_to_regpat (+ efmpat_to_regpat, scanf_fmt_to_regpat, efm_regpat_bufsz) | memory safe for length 0 only; lengths >= 1 ran out of memory in this container |

Open: everything else in quickfix.c (all ~230 functions), the --unsigned-char runs, WP proofs
for unbounded lengths, difftest, review and mutants. No bugs found so far.
