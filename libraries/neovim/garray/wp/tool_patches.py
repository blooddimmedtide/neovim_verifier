"""Declared tool patches (vpipe.toml [[framac.tool_patch]]). Each rewrite is proved
identical to the original by ../equiv/ (CBMC, no assumptions)."""
PATCHES = {
    # GA_APPEND(uint8_t, gap, c): WP's Typed model keeps uint8_t and char views of the
    # same bytes apart, so the store is written through char (with the value moved into char's range first, so no
    # out-of-range conversion is added). ../equiv/append_store.c
    # proves both stores leave identical bytes for every c and index.
    "ga_append": [("((uint8_t *)(gap)->ga_data)[(gap)->ga_len] = (c);",
                   "((char *)(gap)->ga_data)[(gap)->ga_len] = (char)((c) - ((c) > 127 ? 256 : 0));")],
}
