# utf_safe_read_char_adv rejects some overlong sequences, accepts others (minor, not memory)

src/nvim/mbyte.c `utf_safe_read_char_adv` detects failure by `c != first byte` (plus a U+00C3
special case). Neovim's utf_ptr2char decodes overlong RFC 2279 forms, so an overlong sequence
whose value equals its own first byte (E0 83 A0 -> 0xE0, F0 80 83 B0 -> 0xF0, FC 80 80 80 83 BC
-> 0xFC, etc.) is reported as -1 while every other overlong form is accepted. Found by CBMC
(round-2 harness h_safe_read). Impact: inconsistent handling of invalid input in
mb_string2cells_len-style callers; no out-of-bounds access (proved). Fix: decide success by `utf_ptr2len(*s) == k` (verified_neovim claude/project-thread-s2rcie, 13c7bc1); CBMC proves the fixed function against the full reference.
Draft upstream issue only; the owner decides whether to file.
