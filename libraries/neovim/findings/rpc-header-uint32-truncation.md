# msgpack-rpc header: type and msgid truncated to 32 bits before they are checked

File: src/nvim/msgpack_rpc/unpacker.c, `unpacker_parse_header`. Pinned upstream 7b87ce8.

    uint32_t type = (uint32_t)mpack_unpack_uint(tok);
    ...
    p->request_id = (uint32_t)mpack_unpack_uint(tok);

Both values are 64-bit msgpack uints cast to 32 bits with no range check. Reproduced
(rpc-header-uint32-truncation-repro.c, the verbatim function with the real mpack reader):

    [2^32+2, "a", []]      -> accepted as a notification (type 2)
    [0, 2^32+7, "a", []]   -> accepted as a request with msgid 7

The msgpack-rpc spec makes msgid a 32-bit unsigned integer and type 0, 1 or 2, so both
messages are malformed. Impact is low: a client that sends a msgid of 2^32 or more gets a
response carrying a different msgid (it may match another outstanding request of that client),
and junk type values are not rejected. Found while writing the parse_header spec.

Fix (verified_neovim branch claude/project-thread-3l219g, second commit): keep the uint64
for the type check, and reject msgid > UINT32_MAX as a decode error. The reproducer shows
both messages rejected and a normal notification still accepted.

Status: the fix is tested, NOT yet proved. The CBMC harness (unpacker/cbmc/harness_hdr.c)
runs out of memory on a 16 GB machine; needs splitting or a contract for mpack_read.
