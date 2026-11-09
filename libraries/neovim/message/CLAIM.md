# Claim: src/nvim/message.c (in progress, NOT finished)

Pinned source: blooddimmedtide/verified_neovim commit bc10c4818179847a38f43e8959c6cd9a7d064de4.
Extraction: cbmc/trunc_string.c, verbatim, sha256 c06ab95c6bcce0ca9c8f65e6e3a7b7624fd26f438b8b3f841b44e61bc334e916.

## What is proved (strength: bounded, ASCII model only)

trunc_string, CBMC 6.4.1, `--bounds-check --pointer-check --signed-overflow-check --unwinding-assertions`:
no out-of-bounds access, no signed overflow, for every input with
strlen(s) <= 2, 1 <= buflen <= 3, -2 <= room_in <= 5, separate `s` and `buf`, bytes 1..127, signed char
and the same with --unsigned-char: both VERIFICATION SUCCESSFUL.

Model assumptions (stubs, not proved against mbyte.c): ASCII bytes are one-byte characters, so
utfc_ptr2len = 1, utf_head_off = 0, ptr2cells = 2 for control characters and 1 otherwise.

## What is not proved

- Functional spec (prefix + "..." + suffix, width <= room_in): the spec harness (CHECKSPEC=1) has
  harness-side memcmp bound errors; not yet a valid result.
- Aliased call (s == buf), multibyte input, larger bounds.
- buflen == 0 fails: see ../findings/trunc_string-buflen-zero.md. No fix written yet.

## Functions still unverified in message.c

All of them. trunc_string has only the bounded memory-safety result above. msg_strtrunc,
msg_outtrans_len and every other function in message.c (inventory: libraries/neovim/inventory.tsv) are untouched.
