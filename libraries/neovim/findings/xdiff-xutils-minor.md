# src/xdiff/xutils.c: three smaller bugs

Neovim commit 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd (vendored from git's xdiff; git master has
the same code). None of them is reachable from Neovim today, as far as we can tell, but each
function is wrong for some valid input. Each fix is a fork branch of its own.

## 1. xdl_num_out prints negative numbers backwards, and -LONG_MIN overflows

The buffer is filled from the end, but the minus sign is written first, so `-5` comes out as
`"5-"`, and `-120` as `"120-"`. For `LONG_MIN`, `val = -val` overflows (undefined behaviour;
UBSan: `negation of -9223372036854775808 cannot be represented`); in practice `val` stays negative
and `"0123456789"[val % 10]` reads before the literal. Neovim only passes line numbers >= 0.
Fix (branch `fix-xdiff-num-out-long-min`): take the magnitude as `unsigned long`, write the sign
after the digits.

## 2. xdl_recmatch overflows an int index on lines of 2 GiB or more

`int i1, i2` index lines whose sizes are `long`. With a whitespace flag, a line longer than
`INT_MAX` bytes overflows them (UBSan: `xutils.c:219:6: signed integer overflow: 2147483647 + 1`).
Neovim's `mmfile_t.size` is an `int`, so no record can be that long there. Fix (branch
`fix-xdiff-recmatch-long-index`): `long i1, i2`.

## 3. xdl_recmatch with only ignore-cr-at-eol matches lines that differ

It compares the common prefix and then accepts one CR left before the newline. A CR inside one
line can then stand in for the CR that ends the other: `"a\r"` (an incomplete last line) matches
`"a\r\n"`, and `"a\r\r\n"` matches `"a\r\n"`, although the code's own comment says a CR on an
incomplete line is not ignored. An exhaustive check over lines of up to 5 bytes from
{a, b, space, tab, CR, LF} finds 374 such pairs, and no other mismatch in any whitespace mode.
`xdl_hash_record` hashes these lines differently, and every caller compares hashes first; the
hashes can never collide here (`h * 33 ^ 13 == h` has no solution mod 2^64), so diffs were not
affected. Fix (branch `fix-xdiff-recmatch-cr-at-eol`): compare the two lines without their ends.

## Not a bug, but a precondition

`xdl_fall_back_diff(env, xpp, line1, count1, line2, count2)` computes `line1 + count1 - 2` in
`int`; it overflows only when the range ends at record number 2^31 - 1, which needs a file of
exactly `INT_MAX` bytes made of empty lines. Listed in `../xdiff_xutils/CLAIM.md`.
