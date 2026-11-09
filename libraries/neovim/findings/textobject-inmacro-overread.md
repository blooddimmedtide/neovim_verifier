# textobject.c inmacro(): one-byte read past the line's NUL

`startPS()` calls `inmacro(p_sections, s + 1)` (and `p_para`) when a line starts with `.`.
For the line `"."`, `s + 1` points at the NUL. If an option pair starts with a space
(for example `:set sections=\ X`), the first test passes (`macro[0] == ' '` and `s[0] == NUL`)
and the code then evaluates `macro[1] == s[1]`, reading the byte after the NUL. If that byte
happens to equal `macro[1]`, the line counts as a section start.

Default 'sections' and 'paragraphs' have no pair that starts with a space, so only a
user-set option reaches it. The extra byte is usually still inside the memline block, so
ASan does not catch it in a running Neovim; CBMC finds it with an exact-size line object
(`cbmc/run_cbmc.sh` on upstream). Impact: a one-byte out-of-bounds read and a possible
wrong `{`/`}`/`[[` motion. Low severity.

Fix (verified_neovim `fix-textobject-inmacro-overread`, f563ea4): compare the second byte only
while the line has not ended: `(s[0] != NUL && macro[1] == s[1])`. Proved with CBMC against
`textobject/cbmc/spec.h` (bounded, see textobject/CLAIM.md).

Upstream issue: draft only, not filed (the owner files).
