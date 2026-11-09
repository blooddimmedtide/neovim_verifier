# ShaDa additional data byte count wraps at 4 GiB (push_additional_data)

File: src/nvim/msgpack_rpc/unpacker.c, `push_additional_data`; type in src/nvim/types_defs.h.
Pinned upstream: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd.

    a->nbytes += (uint32_t)size;   // nbytes is uint32_t

The builder keeps ShaDa map keys and array elements Neovim does not understand so they can
be written back unchanged. `nbytes` counts their bytes. When the kept bytes of one entry
reach 2^32, the count wraps; `dump_additional_data` then calls
`mpack_raw(src->data, src->nbytes, ...)` with the wrapped length, while the item count it
writes (`additional_data_len`) still includes every item. The rewritten ShaDa entry is
malformed (fewer bytes than items), so the next read reports an error or misparses the
following entries.

Reachability: needs one ShaDa item of 4 GiB or more with unknown keys, read with the item
size limit (`s` in 'shada') disabled or set very high. Low severity; found by the proof.
Not yet reproduced on a real Neovim build (needs a 4 GiB ShaDa file).

Proof: CBMC, libraries/neovim/unpacker/cbmc/harness_ad.c. Upstream fails with empty builder,
size = 2^39. Fixed version proved for every size below 2^48.

Fix (blooddimmedtide/verified_neovim, branch claude/project-thread-3l219g, 76c51e8):
`size_t nbytes;` and `a->nbytes += size;`.
