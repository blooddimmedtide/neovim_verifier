# regexp.c, search.c, fuzzy.c: plan and progress

Claimed by the draft PR "neovim: verify src/nvim/regexp.c, src/nvim/search.c, src/nvim/fuzzy.c".
Pinned upstream: neovim 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd (see ../vpipe.toml).

Functions in scope (from ../inventory.tsv): regexp.c 176 (backtracking + NFA engines and the
shared helpers), search.c 57, fuzzy.c 21. Total 254. None is done until its full functional
contract is proved; progress is tracked per function in ../status.tsv.

Order:
1. Sanitizer fuzzing (ASan + UBSan, libFuzzer) of both regex engines (compile + match),
   fuzzy matching and the pure search helpers, with a differential check between the
   backtracking and NFA engines. Every crash gets a finding and a fix branch on the fork.
2. Proofs, leaves first: byte/char-class helpers and fuzzy scoring with CBMC, loops over
   unbounded strings with Frama-C WP.
