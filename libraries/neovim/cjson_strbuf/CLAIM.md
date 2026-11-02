# src/cjson/strbuf.c (claimed, work in progress)

Claimed by the "Verify Neovim bundled libraries" thread (draft PR #5). Nothing is proved yet.

Functions (src/cjson/strbuf.c): die, strbuf_init, strbuf_new, debug_stats, strbuf_free,
strbuf_free_to_string, calculate_new_size, strbuf_resize, strbuf_append_string; plus the
static inline helpers in strbuf.h they use.
