# memline.c / memfile.c verification plan

Claimed by draft PR "neovim: verify src/nvim/memline.c, src/nvim/memfile.c".
Tool: Frama-C WP (sha-pinned extraction, reusing garray/hashtab tooling).
Order: block/pointer arithmetic helpers first, then the rest.
Progress and the list of unverified functions are kept in this file.
