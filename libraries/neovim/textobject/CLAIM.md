# src/nvim/textobject.c: claim

Upstream: neovim/neovim 7b87ce822e6f (textobject.c unchanged on the fork's base).
Fixed: blooddimmedtide/verified_neovim branch `fix-textobject-inmacro-overread` (f563ea4).

| function | status | tool | what is proved |
|---|---|---|---|
| inmacro | fixed-candidate | CBMC 6.4.1 | Fixed code equals `spec.h` and reads nothing past either NUL, for every option string up to 12 bytes and line up to 3 bytes, x86_64, signed and unsigned char, unwinding assertions on. Upstream proved the same for non-empty lines; on an empty line it reads one byte past the NUL (findings/textobject-inmacro-overread.md). |

Strength: bounded. The loop runs over the option string, which has no length limit, so this is a
bounded model check, not a proof for all lengths. A WP proof with a loop invariant is still to do.
Lines longer than 3 bytes are covered because inmacro reads at most s[0] and s[1].

| find_next_quote | candidate (partial) | CBMC 6.4.1 (`cbmc_quote/`) | Equals `ref_next` on every ASCII line up to 6 bytes, every start column, every ASCII quote char, escape set NULL or up to 2 ASCII chars. |
| find_prev_quote | candidate (partial) | CBMC 6.4.1 (`cbmc_quote/`) | Equals `ref_prev` on every ASCII line up to 4 bytes, same inputs otherwise. |

Quote finders, limits: ASCII lines only. The callees utfc_ptr2len, utf_head_off and vim_strchr are
copied only up to their ASCII fast path (verbatim, pinned in extract.py); every other path is an
assert(0), so the proof shows it is never reached, but multibyte lines are not covered. Precondition:
the quote char is not one of the escape chars (callers pass '"', '\'' or '`' with 'quoteescape',
default "\\"). Bounded lengths, as above.

Reference decisions (spec.h): the option is read as two-byte names; a space matches a space or
the end of the line; when the line has ended there is no second character, so nothing past the
NUL is read.

Harness preconditions: `opt` and `s` are NUL-terminated (startPS passes an option value and a
memline line, both always NUL-terminated).

Not done yet: adversarial review and mutants, differential test, WP proof for unbounded length.

Still unverified in this file (20 of 23 not started; inmacro, find_next_quote and find_prev_quote only partly): findsent, findpar, startPS, cls, fwd_word, bck_word,
end_word, bckend_word, skip_chars, back_in_line, find_first_blank, findsent_forward, current_word,
current_line, current_sent, current_block, in_html_tag, current_tagblock, current_par,
current_quote.
