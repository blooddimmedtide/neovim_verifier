# src/nvim/buffer.c (pinned 7b87ce8): self-contained helpers

Status: **in progress, not verified.** Stopped at the 2026-11-09 09:00 UTC deadline.

| Function | Tool | Result |
|---|---|---|
| calc_percentage | CBMC 6.4.1 (`cbmc/harness.c`, h_calc_percentage) | harness written (division-free reference); CBMC timed out after 230 s in the SAT step. Not proved. Next: split by branch, or Frama-C WP. |
| buf_time_compare | CBMC 6.4.1 (h_buf_time_compare, h_buf_time_compare_bufmatch) | VERIFICATION SUCCESSFUL, signed and unsigned char, x86_64. Candidate (no review or mutants yet). |

Spec for calc_percentage (from the doc comment and every caller): with 0 <= part <= whole and
whole >= 1, the result r satisfies 0 <= r <= 100 and r is floor(100*part/whole) or one above it;
exact when part <= 1,000,000. The precondition is the caller contract (fileinfo: 1 <= lnum <=
line_count; get_rel_pos: above, below >= 1), not documented on the function itself.

Note (not a reachable bug): outside that contract, `part > 1000000` with `1 <= whole <= 99`
divides by zero (`whole / 100 == 0`), and `whole == 0` divides by zero. No caller in buffer.c
can pass such values. `cbmc/harness_outside.c` documents it.

Spec for buf_time_compare: qsort comparator, most recently used first: -1 / 0 / +1,
antisymmetric, 0 on self-compare; also correct on bufmatch_T elements (first member is buf_T *).

Every other function in buffer.c (about 150) is unverified: they use global editor state.
