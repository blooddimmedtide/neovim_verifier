# Findings: typval.c blob functions (upstream 7b87ce8)

## 1. `tv_blob_slice`: signed overflow on `n2--` (undefined behaviour, low impact)

`slice(0z, 0, v:numbermin)` reaches `tv_blob_slice(.., len = 0, n1 = 0, n2 = INT64_MIN,
exclusive = true, ..)` through `eval_index_inner` (eval.c:3351). With `len == 0`,
`n2 = len + n2` leaves `n2 == INT64_MIN`, and the exclusive branch then runs `n2--`, which
overflows `int64_t` (undefined behaviour in C).

- Found by WP (`-wp-rte`): the `signed_overflow` guard on `n2--` is false for this input; the
  upstream proof therefore carries `requires exclusive ==> n2 > INT64_MIN`.
- Reproducer: `repro/repro_slice_overflow.c` (the index arithmetic copied verbatim; a diff
  against the pinned source is in RESULTS.md):
  `runtime error: signed integer overflow: -9223372036854775808 - 1 cannot be represented in type 'long int'`.
- Effect: on today's compilers the subtraction wraps to INT64_MAX and the result is still the
  empty blob (`n1 >= len`), so nothing visible goes wrong. It is still UB, and an optimizer
  may assume it cannot happen. Only an empty blob triggers it (for `len > 0`,
  `len + INT64_MIN > INT64_MIN`).
- Suggested fix (not yet written or proved): clamp before decrementing, e.g.
  `if (exclusive && n2 > VARNUMBER_MIN) { n2--; }` is NOT equivalent for len == 0 (n2 stays
  INT64_MIN < 0, still empty) but gives the same result in every other case; a fix branch and
  its proof are still to do.

## Not bugs, noted for the spec

- `tv_blob_index` and `tv_blob_slice` read the bytes from `rettv->vval.v_blob`, not from their
  `blob` argument. Every caller passes `rettv` holding the blob being indexed, so the result
  is right, but `blob` is unused. The contracts are stated over `rettv`'s blob.
- `tv_blob_set_append` writes at a negative `idx` if one is passed (`idx <= ga_len` is the only
  test). Its only caller (eval.c set_var_lval) passes `ll_n1` after `tv_blob_check_index`
  proved it is in `0 .. len`, so this is a documented precondition, not a reachable bug.
- `tv_blob_set_range` likewise relies on the caller's range check (`0 <= n1`, `n2 < len`).
- `tv_blob_remove` (not proved here) sets `ga_len` before `ga_grow` on a fresh blob, so the
  array is briefly in a state ga_grow's contract does not allow (`ga_len > ga_maxlen`);
  ga_grow's code still allocates enough. Worth a look when it is proved.
