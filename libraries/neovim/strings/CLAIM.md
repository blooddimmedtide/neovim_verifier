# src/nvim/strings.c: work in progress

Claimed by the "Verify Neovim string and charset code" thread (2026-11-02), together with
`src/nvim/charset.c`. First targets: the leaf helpers that need no global state
(xstrnsave, the vim_str*up family, vim_stricmp/vim_strnicmp/striequal/vim_strnicmp_asc, vim_strchr, has_non_ascii*, concat_str, del_trailing_spaces, reverse_text, strrep).
This file is replaced by the full claim card when proofs land.
