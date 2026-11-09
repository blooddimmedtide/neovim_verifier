# repeat() on a List: signed overflow before the size check (candidate finding, not yet reported)

- File: `src/nvim/eval/funcs.c`, `repeat_list`, upstream 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
- Found while proving `check_repeat_count` (typval.c), whose callers rely on it to stop overflow.
- Status: reproduced on the extracted expression with UBSan; not yet run in a Neovim build;
  no fix branch yet; no upstream issue filed (the owner files).

## What happens

```c
const int slen = tv_list_len(l);
tv_list_alloc_ret(rettv, (n > 0) * n * slen);   // computed first
...
if (check_repeat_count(slen, n) == FAIL) {      // the overflow check comes after
```

`n` is the user's count (`varnumber_T`, 64-bit). `(n > 0) * n * slen` is a 64-bit signed
multiply, so `repeat([1, 2], 9223372036854775807)` evaluates `INT64_MAX * 2`: undefined
behaviour (UBSan: "signed integer overflow: 9223372036854775807 * 2 cannot be represented").
In practice it wraps, and `tv_list_alloc` ignores its `len` argument entirely (typval.c:220),
so the visible effect today is nil, and `check_repeat_count`
then rejects the call with E1240. It is still UB that an optimising compiler may exploit.

## Fix (proposed, not yet proved)

Move the `tv_list_alloc_ret` hint after the check, or compute it only once
`check_repeat_count` has passed (then `n * slen <= INT_MAX`, which our proof of
`check_repeat_count` guarantees).

Reproducer: `repeat-list-overflow-repro.c` (the verbatim expression).
