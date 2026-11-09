# marktree.c: mt_dbg_id (candidate)

Scope: only `mt_dbg_id` in src/nvim/marktree.c @ 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd. The rest of marktree.c is
claimed by draft PR #16 ("Verify Neovim marks code"); this PR does not touch those functions.

Property (written from the key layout in marktree.h, not the code): the result equals bits 1..32 of the key,
floor(x/2) mod 2^32, for every uint64_t x. Tool: CBMC 5.95.1, all inputs nondeterministic, no preconditions,
overflow/conversion/shift checks on, signed and unsigned char. The copy is checked verbatim against the pin by run_cbmc.sh.
Not done: adversarial review and mutants, pinned-container CI run.
