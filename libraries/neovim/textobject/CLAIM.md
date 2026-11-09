# src/nvim/textobject.c: claim

Upstream: neovim/neovim 7b87ce822e6f (textobject.c unchanged on the fork's base).
Fixed: blooddimmedtide/verified_neovim branch `fix-textobject-inmacro-overread` (f563ea4).

| function | status | tool | what is proved |
|---|---|---|---|
| inmacro | fixed-candidate | CBMC 6.4.1 | Fixed code equals `spec.h` and reads nothing past either NUL, for every option string up to 12 bytes and line up to 3 bytes, x86_64, signed and unsigned char, unwinding assertions on. Upstream proved the same for non-empty lines; on an empty line it reads one byte past the NUL (findings/textobject-inmacro-overread.md). |

Strength: bounded. The loop runs over the option string, which has no length limit, so this is a
bounded model check, not a proof for all lengths. A WP proof with a loop invariant is still to do.
Lines longer than 3 bytes are covered because inmacro reads at most s[0] and s[1].

Reference decisions (spec.h): the option is read as two-byte names; a space matches a space or
the end of the line; when the line has ended there is no second character, so nothing past the
NUL is read.

Harness preconditions: `opt` and `s` are NUL-terminated (startPS passes an option value and a
memline line, both always NUL-terminated).

Not done yet: adversarial review and mutants, differential test, WP proof for unbounded length.

Still unverified in this file (22 of 23): findsent, findpar, startPS, cls, fwd_word, bck_word,
end_word, bckend_word, skip_chars, back_in_line, find_first_blank, findsent_forward, current_word,
current_line, current_sent, current_block, in_html_tag, current_tagblock, current_par,
find_next_quote, find_prev_quote, current_quote.
