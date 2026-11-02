"""Tool patches: rewrites of statements WP cannot read, each proved equal to the original
in ../equiv/ (CBMC, no assumptions).

1. Byte reads through `uint8_t *` of `char` memory (hash_hash, hash_hash_len): WP's typed
   memory model keeps the uint8_t and char views of a byte apart, so the pointers are read
   as `const char *` and each byte converted with (uint8_t), which gives the same value.
   HASH_CYCLE_BODY(hash, p) is `hash = hash * 101 + *p++`; it is written out with the
   (uint8_t) conversion.
2. memset / memcpy of hashtab_T and hashitem_T objects (hash_init, hash_may_resize): WP
   cannot read struct fields written as bytes. The zeroing and the copy are done field by
   field by vp_clear_table / vp_clear_items / vp_copy_items (proved by WP in the prelude),
   which write the same bytes (the types have no padding on x86_64; checked in ../equiv/).
"""
CYCLE_OLD = "    HASH_CYCLE_BODY(hash, p);"
CYCLE_NEW = "    hash = hash * 101 + (uint8_t)*p++;"
PATCHES = {
    "hash_hash": [
        ("  const uint8_t *p = (uint8_t *)key + 1;\n  while (*p != NUL) {",
         "  const char *p = key + 1;\n  while ((uint8_t)*p != NUL) {"),
        (CYCLE_OLD, CYCLE_NEW),
    ],
    "hash_hash_len": [
        ("  hash_T hash = *(uint8_t *)key;", "  hash_T hash = (uint8_t)*key;"),
        ("  const uint8_t *end = (uint8_t *)key + len;", "  const char *end = key + len;"),
        ("  const uint8_t *p = (const uint8_t *)key + 1;", "  const char *p = key + 1;"),
        (CYCLE_OLD, CYCLE_NEW),
    ],
    "hash_init": [
        ("  CLEAR_POINTER(ht);", "  vp_clear_table(ht);"),
    ],
    "hash_may_resize": [
        ("? memcpy(temparray, ht->ht_smallarray, sizeof(temparray))",
         "? vp_copy_items(temparray, ht->ht_smallarray)"),
        ("    CLEAR_FIELD(ht->ht_smallarray);", "    vp_clear_items(ht->ht_smallarray);"),
    ],
}
