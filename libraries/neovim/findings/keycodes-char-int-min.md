# keycodes.c: `<Char-N>` with N >= 2^31 becomes a negative (special) key; N = 2^31 negates INT_MIN

Found 2026-11-09 while writing WP contracts for `simplify_key` / `special_to_buf`
(upstream 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd).

## What happens

`find_special_key()` parses `<Char-N>` with `vim_str2nr()` into an unsigned 64-bit `n`
and then does `key = (int)n;` with no range check.

* For `0x80000000 <= N <= 0xFFFFFFFF` the key is negative. Negative keys are special key
  codes (`IS_SPECIAL(c)` is `c < 0`), so `<Char-N>` can produce any K_SPECIAL byte triple,
  for example `<Char-0xFFFF9803>` is `TERMCAP2KEY(KS_EXTRA, KE_LUA)` (K_LUA) and
  `<Char-0xFFFF7D83>` is `TERMCAP2KEY(KS_EXTRA, KE_SNR)`... These are not characters, which
  is what `<Char-N>` is documented to mean (`:help <Char->`: "character specified with
  decimal, octal or hexadecimal number").
* For `N = 0x80000000` the key is `INT_MIN`. `special_to_buf()` (and `simplify_key()` when
  Shift or Ctrl is given, e.g. `<C-Char-0x80000000>`) evaluates
  `KEY2TERMCAP0(key) = (-(key)) & 0xff`, negating INT_MIN: undefined behavior in C.

Reach: any `:map`, `:menu`, `feedkeys()`, `nvim_replace_termcodes()` / `keytrans()` input,
e.g. `:nnoremap x <Char-0x80000000>` or `nvim_replace_termcodes("<Char-0x80000000>", ...)`.

## Reproducer

`keycodes-char-int-min-repro.c` repeats the two exact lines (`key = (int)n` and
`KEY2TERMCAP0/1`) with the value `vim_str2nr` returns for `0x80000000`:

    $ gcc -fsanitize=undefined -fno-sanitize-recover=all keycodes-char-int-min-repro.c && ./a.out
    runtime error: negation of -2147483648 cannot be represented in type 'int'

Not yet reproduced in a full UBSan build of Nvim (no time in this session).

## Fix

verified_neovim branch `claude/project-thread-vh5tc9`, commit 4c94621: reject `<Char-N>`
when `n > INT_MAX` (same `E474: Invalid argument` as a malformed number). After the fix the
`<Char->` branch yields `0 <= key <= INT_MAX`, and every other branch yields a key from
`utf_ptr2char` (>= 0) or `get_special_key_code` (>= -65535), so `key != INT_MIN` holds on
entry to `simplify_key` / `special_to_buf`, which is the precondition their WP proofs use.
The proof of that fact for `find_special_key` itself is **not done yet** (find_special_key
is unverified), so the fix is `fixed-candidate`, not a verified fix.

Upstream issue draft: /mnt/project-files/neovim-verify/upstream/issue-keycodes-char-int-min.md (not filed).
