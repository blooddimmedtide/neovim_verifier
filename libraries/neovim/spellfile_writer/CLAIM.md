---
entry: neovim/src/nvim/spellfile.c (writer side: .sug <sugnr> encoder)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
fixed_fork: none yet
toolchain: CBMC 6.11.0 (nixpkgs) + gcc -O2 UBSan exhaustive enumeration
strength: candidate (1 function, in-range inputs); not reviewed, no mutants yet
platform: x86_64, char signed and unsigned
---

# Claim card: spellfile.c writer helpers

Readers are claimed by neovim_verifier#21; this entry covers only the writer side.

Run: `bash spellfile_writer/exhaustive/run.sh <neovim checkout>`. Code is extracted verbatim
(`extract.sh`, sha256 pins in `pins.sha256`).

| Function | Property | Strength |
|---|---|---|
| `offset2bytes(nr, buf)` | For 0 <= nr < 15*255^3 (= 248,720,625): writes the minimal 1..4 bytes from the spec in `check.c` (base-255 digits + 1, so no NUL; UTF-8-like lead tags), writes nothing past them, and `bytes2offset` (spellsuggest.c, the reader) returns nr and advances by exactly that length | CBMC proved (cbmc/harness.c, nondet nr in range, exact 4-byte object, bounds/pointer/overflow/shift/leak checks, unwinding assertions), signed and unsigned char; plus exhaustive run of all 2^32 ints with UBSan |

The spec is written from the format comment at spellfile.c:215-224 (`<sugnr>` "stored as an offset
to the previous number in as few bytes as possible", `<sugline>` ends at NUL) and the reader
`bytes2offset`, which keeps only 4 bits of a 4-byte lead byte. The reference decides that values
outside 0 .. 248,720,624 are not representable.

## Finding (minor, data integrity, not memory safety)

`offset2bytes` silently writes an undecodable encoding for nr >= 248,720,625 (1,898,763,023 values):
the lead byte `0xe0 + b4` gets b4 >= 16, which the reader masks with `0x0f`, so the number read back
is wrong (and for b4 >= 32 the lead byte wraps). For nr < 0 (outside the documented domain) 8,421,505
values produce a NUL byte, which would end the `<sugline>` early. Reachability not established:
nr is the difference of word numbers in `sug_filltable` (spellfile.c:5094-5101); a positive gap of
248M+ needs a word list that large. Whether the gap can be negative (sibling order) is not checked.
No fix branch yet. Suggested fix: reject (or use a 5-byte form for) nr outside the range, and assert
nr >= 0.

## Still unverified in spellfile.c (writer side)

Everything else, including rep_compare, write_vim_spell, put_node, sug_filltree, sug_maketable,
sug_filltable, sug_write, mkspell, wordtree_compress, node_compress, node_equal, write_spell_prefcond,
spell_add_word, init_spellfile, set_spell_charflags, set_spell_finish, set_map_str, and all .aff/.dic
readers. offset2bytes: no independent review or planted-bug run yet; bytes2offset (spellsuggest.c) is used as the reader in the spec, so a shared bug in both would not be caught by the round-trip alone (the length and no-NUL checks are independent).
