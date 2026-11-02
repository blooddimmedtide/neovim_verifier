# src/nvim/charset.c: work in progress

Claimed by the "Verify Neovim string and charset code" thread (2026-11-02), together with
`src/nvim/strings.c`. First targets: the leaf helpers that need no global state
(skip*/getdigits*/hex2nr/hexhex2nr/rem_backslash/backslash_halve/vim_isblankline/nr2hex/vim_str2nr).
This file is replaced by the full claim card when proofs land.
