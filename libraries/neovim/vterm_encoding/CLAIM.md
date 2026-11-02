# src/nvim/vterm/encoding.c (claimed, work in progress)

Claimed by the "Verify Neovim bundled libraries" thread. Nothing is proved yet.

Functions: init_utf8, decode_utf8, decode_usascii, decode_table, vterm_lookup_encoding.
Plan: CBMC (byte-level, loops bounded by the buffer sizes in the harness, plus an
induction-style proof over the decoder state for unbounded inputs), independent spec from
RFC 3629 / ISO 2022 / DEC Special Graphics, both char signednesses, differential test.
