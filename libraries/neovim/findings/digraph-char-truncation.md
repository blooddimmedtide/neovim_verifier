# digraph_set() silently truncates multibyte digraph characters to one byte

File: src/nvim/digraph.c (pinned 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd), `registerdigraph()`.
Severity: wrong result (no memory-safety impact). Status: reproduced (concrete run and CBMC counterexample). The widened-struct registerdigraph is proved; full fix not finished.

`digraph_set()` / `digraph_setlist()` accept "a string with two characters" (`:help digraph_set()`);
`get_digraph_chars()` decodes each with `mb_cptr2char_adv()`, so {chars} may be any codepoints, and
`check_digraph_chars_valid()` accepts them. `registerdigraph()` then stores
`dp->char1 = (uint8_t)char1; dp->char2 = (uint8_t)char2;` because `digr_T` has `uint8_t` fields.

Effect: `digraph_set('ŀx', 'Y')` (U+0140) returns v:true but registers `@x` (0x40) instead:
`digraph_get('ŀx')` returns `x`, and `digraph_get('@x')` returns `Y`, silently overriding an unrelated pair.
Reproducer: `digraph/cbmc/repro_truncation.c` (verbatim extracted code; exit 1 = bug present).

Fix options (not yet done): (a) reject characters above 0xFF in `get_digraph_chars()` with an
error, or (b) widen `digr_T.char1/char2` to `int` and update the three places that print them as
bytes (lines ~1508, ~1756, ~1858) to use `utf_char2bytes`. Widening alone was checked with the
reproducer (passes) but the printing paths still need changing before a fix can be proved.
Upstream issue: draft only, not filed (owner files).
