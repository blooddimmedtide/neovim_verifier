# Neovim verification status

**0 / 8556 functions done** (verified, or a verified fix) across 215 files.
A function is done only when every property in its contract is proved; partial results stay open.

## Files with work in progress or done

| File | Done | Partial | Open | Total |
|---|---|---|---|---|
| src/mpack/mpack_core.c | 0 | 23 | 0 | 23 |
| src/nvim/base64.c | 0 | 4 | 0 | 4 |
| src/nvim/math.c | 0 | 7 | 0 | 7 |
| src/nvim/mbyte.c | 0 | 8 | 82 | 90 |
| src/nvim/memory.c | 0 | 15 | 28 | 43 |
| src/nvim/undo.c | 0 | 16 | 67 | 83 |

## Function details

| File | Function | Status | Evidence | Notes |
|---|---|---|---|---|
| src/nvim/base64.c | `base64_encode` | candidate | base64/wp (Frama-C WP), base64/equiv (CBMC) | RFC 4648 output for every input, one allocation returned; see base64/CLAIM.md. All machine gates pass (35/35 mutants, 2 reviews, CI x2); waiting on owner spec sign-off |
| src/nvim/base64.c | `base64_decode` | fixed-candidate | base64/wp (Frama-C WP, upstream 120/120 under 2 GiB, fixed 118/118 no limit) | upstream wrong at >= 2 GiB (findings/base64-decode-over-2gib.md); fix in verified_neovim proved for all inputs. All machine gates pass; waiting on owner spec sign-off |
| src/nvim/base64.c | `vim_htobe64` | candidate | base64/bridge (CBMC, no loops, all inputs) | equals big-endian reading of the bytes |
| src/nvim/base64.c | `vim_htobe32` | candidate | base64/bridge (CBMC, no loops, all inputs) | equals big-endian reading of the bytes |
| src/nvim/mbyte.c | `utf_byte2len` | candidate | mbyte/cbmc (CBMC, all inputs) | lead-byte length for 0..255; see mbyte/CLAIM.md. Review + 24/24 planted bugs done; waiting on owner spec sign-off |
| src/nvim/mbyte.c | `utf_char2len` | candidate | mbyte/cbmc (CBMC, all inputs) | shortest RFC 2279 encoding length; 1 for c < 0 |
| src/nvim/mbyte.c | `utf_char2bytes` | candidate | mbyte/cbmc (CBMC, all inputs) | shortest encoding, decodes back to c, writes only buf[0..r-1] |
| src/nvim/mbyte.c | `utf_ptr2len` | candidate | mbyte/cbmc (CBMC, all inputs) | sequence length; never reads past NUL |
| src/nvim/mbyte.c | `utf_ptr2char` | candidate | mbyte/cbmc (CBMC, all inputs) | decoded value or first byte; never reads past NUL |
| src/nvim/mbyte.c | `utf_ptr2len_len` | candidate | mbyte/cbmc (CBMC, all inputs) | always reads p[0]; never reads past p[size-1] |
| src/nvim/mbyte.c | `utf_cp_bounds_len` | fixed-candidate | mbyte/cbmc (CBMC, upstream for p - base <= INT_MAX, fixed for every distance) | upstream UB / out-of-bounds read at >= 2 GiB (findings/cp-bounds-over-2gib.md); fix in verified_neovim. Reviewer mutants for this function still to do |
| src/nvim/mbyte.c | `utf_cp_bounds` | fixed-candidate | mbyte/cbmc (CBMC, same as utf_cp_bounds_len) | wrapper with p_len = INT_MAX on a NUL-terminated stream; inherits the 2 GiB bug and its fix |
| src/mpack/mpack_core.c | `mpack_tokbuf_init` | candidate | mpack/cbmc (CBMC, all inputs) | sets the empty state. Review + planted bugs pending |
| src/mpack/mpack_core.c | `mpack_rtoken` | candidate | mpack/cbmc (CBMC, all inputs) | spec token, consumes exactly its header. Review + planted bugs pending |
| src/mpack/mpack_core.c | `mpack_read` | fixed-candidate | mpack/cbmc (CBMC, all inputs) | streaming reader; any split gives the same tokens; upstream hangs with a multiple of 4 GiB of input left (findings/mpack-chunk-over-4gib.md), fixed in verified_neovim. Review + planted bugs pending |
| src/mpack/mpack_core.c | `mpack_write` | candidate | mpack/cbmc (CBMC, all inputs) | streaming writer; shortest encoding in order. Review + planted bugs pending |
| src/mpack/mpack_core.c | `mpack_rpending` | candidate | mpack/cbmc (CBMC, through its callers) | static helper, proved for every input its callers can pass |
| src/mpack/mpack_core.c | `mpack_rvalue` | candidate | mpack/cbmc (CBMC, through its callers) | static helper, proved for every input its callers can pass |
| src/mpack/mpack_core.c | `mpack_rblob` | candidate | mpack/cbmc (CBMC, through its callers) | static helper, proved for every input its callers can pass |
| src/mpack/mpack_core.c | `mpack_wtoken` | candidate | mpack/cbmc (CBMC, through its callers) | static helper, proved for every input its callers can pass |
| src/mpack/mpack_core.c | `mpack_wpending` | candidate | mpack/cbmc (CBMC, through its callers) | static helper, proved for every input its callers can pass |
| src/mpack/mpack_core.c | `mpack_wpint` | candidate | mpack/cbmc (CBMC, through its callers) | static helper, proved for every input its callers can pass |
| src/mpack/mpack_core.c | `mpack_wnint` | candidate | mpack/cbmc (CBMC, through its callers) | static helper, proved for every input its callers can pass |
| src/mpack/mpack_core.c | `mpack_wfloat` | candidate | mpack/cbmc (CBMC, through its callers) | static helper, proved for every input its callers can pass |
| src/mpack/mpack_core.c | `mpack_wstr` | candidate | mpack/cbmc (CBMC, through its callers) | static helper, proved for every input its callers can pass |
| src/mpack/mpack_core.c | `mpack_wbin` | candidate | mpack/cbmc (CBMC, through its callers) | static helper, proved for every input its callers can pass |
| src/mpack/mpack_core.c | `mpack_wext` | candidate | mpack/cbmc (CBMC, through its callers) | static helper, proved for every input its callers can pass |
| src/mpack/mpack_core.c | `mpack_warray` | candidate | mpack/cbmc (CBMC, through its callers) | static helper, proved for every input its callers can pass |
| src/mpack/mpack_core.c | `mpack_wmap` | candidate | mpack/cbmc (CBMC, through its callers) | static helper, proved for every input its callers can pass |
| src/mpack/mpack_core.c | `mpack_w1` | candidate | mpack/cbmc (CBMC, through its callers) | static helper, proved for every input its callers can pass |
| src/mpack/mpack_core.c | `mpack_w2` | candidate | mpack/cbmc (CBMC, through its callers) | static helper, proved for every input its callers can pass |
| src/mpack/mpack_core.c | `mpack_w4` | candidate | mpack/cbmc (CBMC, through its callers) | static helper, proved for every input its callers can pass |
| src/mpack/mpack_core.c | `mpack_value` | candidate | mpack/cbmc (CBMC, through its callers) | static helper, proved for every input its callers can pass |
| src/mpack/mpack_core.c | `mpack_blob` | candidate | mpack/cbmc (CBMC, through its callers) | static helper, proved for every input its callers can pass |
| src/mpack/mpack_core.c | `mpack_byte` | candidate | mpack/cbmc (CBMC, through its callers) | static helper, proved for every input its callers can pass |
| src/nvim/math.c | `xfpclassify` | candidate | math/cbmc (CBMC, all inputs) | IEEE 754 class; see math/CLAIM.md. Review pending |
| src/nvim/math.c | `xisinf` | candidate | math/cbmc (CBMC, all inputs) | true exactly for infinities; see math/CLAIM.md. Review pending |
| src/nvim/math.c | `xisnan` | candidate | math/cbmc (CBMC, all inputs) | true exactly for NaN; see math/CLAIM.md. Review pending |
| src/nvim/math.c | `xctz` | candidate | math/cbmc (CBMC, all inputs) | 64 for 0, else lowest set bit (builtin and fallback); see math/CLAIM.md. Review pending |
| src/nvim/math.c | `xpopcount` | candidate | math/cbmc (CBMC, all inputs) | number of set bits (builtin and fallback; NetBSD system call not covered); see math/CLAIM.md. Review pending |
| src/nvim/math.c | `vim_append_digit_int` | candidate | math/cbmc (CBMC, all inputs) | appends a digit when it fits, for value >= 0; see math/CLAIM.md. Review pending |
| src/nvim/math.c | `trim_to_int` | candidate | math/cbmc (CBMC, all inputs) | clamp to int; see math/CLAIM.md. Review pending |
| src/nvim/memory.c | `xmemcpyz` | candidate | memory/wp (Frama-C WP, every length), memory/difftest | copies len bytes and a NUL; see memory/CLAIM.md. Review done (accept with changes); waiting on owner spec sign-off |
| src/nvim/memory.c | `xstrnlen` | candidate | memory/wp (Frama-C WP, every length), memory/difftest | index of first NUL below n, else n; see memory/CLAIM.md. Review done (accept with changes); waiting on owner spec sign-off |
| src/nvim/memory.c | `xstrchrnul` | candidate | memory/wp (Frama-C WP, every length), memory/difftest | first c or NUL; see memory/CLAIM.md. Review done (accept with changes); waiting on owner spec sign-off |
| src/nvim/memory.c | `xmemscan` | candidate | memory/wp (Frama-C WP, every length), memory/difftest | first c, else end; see memory/CLAIM.md. Review done (accept with changes); waiting on owner spec sign-off |
| src/nvim/memory.c | `strchrsub` | candidate | memory/wp (Frama-C WP, every length), memory/difftest | replaces every c in the string; see memory/CLAIM.md. Review done (accept with changes); waiting on owner spec sign-off |
| src/nvim/memory.c | `memchrsub` | candidate | memory/wp (Frama-C WP, every length), memory/difftest | replaces every c in the buffer; see memory/CLAIM.md. Review done (accept with changes); waiting on owner spec sign-off |
| src/nvim/memory.c | `strcnt` | candidate | memory/wp (Frama-C WP, every length), memory/difftest | count of c in the string; see memory/CLAIM.md. Review done (accept with changes); waiting on owner spec sign-off |
| src/nvim/memory.c | `memcnt` | candidate | memory/wp (Frama-C WP, every length), memory/difftest | count of c in the buffer; see memory/CLAIM.md. Review done (accept with changes); waiting on owner spec sign-off |
| src/nvim/memory.c | `xstpcpy` | candidate | memory/wp (Frama-C WP, every length), memory/difftest | copies the string, returns end; see memory/CLAIM.md. Review done (accept with changes); waiting on owner spec sign-off |
| src/nvim/memory.c | `xstpncpy` | candidate | memory/wp (Frama-C WP, every length), memory/difftest | stpncpy semantics, NUL padding; see memory/CLAIM.md. Review done (accept with changes); waiting on owner spec sign-off |
| src/nvim/memory.c | `xstrlcpy` | candidate | memory/wp (Frama-C WP, every length), memory/difftest | BSD strlcpy semantics; see memory/CLAIM.md. Review done (accept with changes); waiting on owner spec sign-off |
| src/nvim/memory.c | `xstrlcat` | candidate | memory/wp (Frama-C WP, every length), memory/difftest | BSD strlcat semantics; see memory/CLAIM.md. Review done (accept with changes); waiting on owner spec sign-off |
| src/nvim/memory.c | `xmemrchr` | candidate | memory/wp (Frama-C WP, every length), memory/difftest | last c, or NULL; see memory/CLAIM.md. Review done (accept with changes); waiting on owner spec sign-off |
| src/nvim/memory.c | `strequal` | candidate | memory/wp (Frama-C WP, every length), memory/difftest | NULL-aware string equality; see memory/CLAIM.md. Review done (accept with changes); waiting on owner spec sign-off |
| src/nvim/memory.c | `strnequal` | candidate | memory/wp (Frama-C WP, every length), memory/difftest | NULL-aware bounded equality; see memory/CLAIM.md. Review done (accept with changes); waiting on owner spec sign-off |
| src/nvim/undo.c | `undo_write` | candidate | undo/cbmc (CBMC) | fwrite result; inside every write harness; review + 22/22 planted bugs done; waiting on owner sign-off |
| src/nvim/undo.c | `undo_write_bytes` | candidate | undo/cbmc (CBMC, every nr, len 1..8) | big-endian nr mod 256^len; see undo/CLAIM.md; review + 22/22 planted bugs done; waiting on owner sign-off |
| src/nvim/undo.c | `put_header_ptr` | candidate | undo/cbmc (CBMC) | 4-byte uh_seq or 0; review + 22/22 planted bugs done; waiting on owner sign-off |
| src/nvim/undo.c | `serialize_pos` | candidate | undo/cbmc (CBMC) | 3 big-endian 4-byte fields; review + 22/22 planted bugs done; waiting on owner sign-off |
| src/nvim/undo.c | `serialize_visualinfo` | candidate | undo/cbmc (CBMC) | 8 big-endian 4-byte fields; review + 22/22 planted bugs done; waiting on owner sign-off |
| src/nvim/undo.c | `undo_read_4c` | candidate | undo/cbmc (CBMC, every 0..6 byte stream) | get4c: 32-bit two's complement or -1; review + 22/22 planted bugs done; waiting on owner sign-off |
| src/nvim/undo.c | `undo_read_2c` | candidate | undo/cbmc (CBMC) | get2c: 0..65535 or -1; review + 22/22 planted bugs done; waiting on owner sign-off |
| src/nvim/undo.c | `undo_read_byte` | candidate | undo/cbmc (CBMC) | next byte or EOF; review + 22/22 planted bugs done; waiting on owner sign-off |
| src/nvim/undo.c | `undo_read_time` | fixed-candidate | undo/cbmc (CBMC, fixed fork) | upstream get8ctime signed shift overflow (findings/get8ctime-shift-overflow.md); fix verified_neovim PR #8 proved; review + 22/22 planted bugs done; waiting on owner sign-off |
| src/nvim/undo.c | `undo_read_len` | candidate | undo/cbmc (CBMC, every file size) | valid length or -1 + one corruption report; review + 22/22 planted bugs done; waiting on owner sign-off |
| src/nvim/undo.c | `undo_read` | candidate | undo/cbmc (CBMC, any size < 2^40) | next size bytes or false + zero-filled; review + 22/22 planted bugs done; waiting on owner sign-off |
| src/nvim/undo.c | `undo_read_string` | candidate | undo/cbmc (CBMC, any len < 2^40) | NUL-terminated copy or NULL, no leak; review + 22/22 planted bugs done; waiting on owner sign-off |
| src/nvim/undo.c | `unserialize_pos` | candidate | undo/cbmc (CBMC, every 0..13 byte stream) | fields clamped at 0; review + 22/22 planted bugs done; waiting on owner sign-off |
| src/nvim/undo.c | `unserialize_visualinfo` | candidate | undo/cbmc (CBMC, every 0..33 byte stream) | review + 22/22 planted bugs done; waiting on owner sign-off |
| src/nvim/undo.c | `uhp_seq_cmp` | candidate | undo/cbmc (CBMC) | sign of uh_seq comparison; review + 22/22 planted bugs done; waiting on owner sign-off |
| src/nvim/undo.c | `uhp_table_find` | candidate | undo/wp (Frama-C WP, any size, 33/33) | binary search on sorted table; CBMC n<=4 cross-check; review + 22/22 planted bugs done; waiting on owner sign-off |

## All files

| File | Done / Total |
|---|---|
| src/bit.c | 0 / 4 |
| src/nlua0.c | 0 / 1 |
| src/static_ts_registry.c | 0 / 1 |
| src/cjson/fpconv.c | 0 / 7 |
| src/cjson/lua_cjson.c | 0 / 56 |
| src/cjson/strbuf.c | 0 / 9 |
| src/lpeg/lpcap.c | 0 / 24 |
| src/lpeg/lpcode.c | 0 / 37 |
| src/lpeg/lpcset.c | 0 / 5 |
| src/lpeg/lpprint.c | 0 / 12 |
| src/lpeg/lptree.c | 0 / 74 |
| src/lpeg/lpvm.c | 0 / 6 |
| src/mpack/conv.c | 0 / 23 |
| src/mpack/lmpack.c | 0 / 34 |
| src/mpack/mpack_core.c | 0 / 23 |
| src/mpack/object.c | 0 / 9 |
| src/mpack/rpc.c | 0 / 16 |
| src/nvim/arabic.c | 0 / 10 |
| src/nvim/arglist.c | 0 / 41 |
| src/nvim/autocmd.c | 0 / 76 |
| src/nvim/base64.c | 0 / 4 |
| src/nvim/buffer.c | 0 / 98 |
| src/nvim/buffer_updates.c | 0 / 11 |
| src/nvim/bufwrite.c | 0 / 18 |
| src/nvim/change.c | 0 / 32 |
| src/nvim/channel.c | 0 / 42 |
| src/nvim/charset.c | 0 / 57 |
| src/nvim/clipboard.c | 0 / 5 |
| src/nvim/cmdexpand.c | 0 / 89 |
| src/nvim/cmdhist.c | 0 / 25 |
| src/nvim/context.c | 0 / 20 |
| src/nvim/cursor.c | 0 / 23 |
| src/nvim/cursor_shape.c | 0 / 6 |
| src/nvim/debugger.c | 0 / 19 |
| src/nvim/decoration.c | 0 / 49 |
| src/nvim/decoration_provider.c | 0 / 14 |
| src/nvim/dialog.c | 0 / 10 |
| src/nvim/diff.c | 0 / 81 |
| src/nvim/digraph.c | 0 / 24 |
| src/nvim/drawline.c | 0 / 34 |
| src/nvim/drawscreen.c | 0 / 52 |
| src/nvim/eval.c | 0 / 156 |
| src/nvim/ex_cmds.c | 0 / 59 |
| src/nvim/ex_cmds2.c | 0 / 26 |
| src/nvim/ex_docmd.c | 0 / 213 |
| src/nvim/ex_eval.c | 0 / 44 |
| src/nvim/ex_getln.c | 0 / 114 |
| src/nvim/ex_session.c | 0 / 19 |
| src/nvim/extmark.c | 0 / 19 |
| src/nvim/file_search.c | 0 / 28 |
| src/nvim/fileio.c | 0 / 55 |
| src/nvim/fold.c | 0 / 83 |
| src/nvim/fuzzy.c | 0 / 21 |
| src/nvim/garray.c | 0 / 11 |
| src/nvim/grid.c | 0 / 48 |
| src/nvim/hashtab.c | 0 / 16 |
| src/nvim/help.c | 0 / 12 |
| src/nvim/highlight.c | 0 / 39 |
| src/nvim/highlight_group.c | 0 / 44 |
| src/nvim/indent.c | 0 / 39 |
| src/nvim/indent_c.c | 0 / 58 |
| src/nvim/input.c | 0 / 100 |
| src/nvim/input_cmdatom.c | 0 / 71 |
| src/nvim/insert.c | 0 / 82 |
| src/nvim/insexpand.c | 0 / 208 |
| src/nvim/keycodes.c | 0 / 17 |
| src/nvim/linematch.c | 0 / 10 |
| src/nvim/log.c | 0 / 12 |
| src/nvim/main.c | 0 / 38 |
| src/nvim/map.c | 0 / 10 |
| src/nvim/map_glyph_cache.c | 0 / 4 |
| src/nvim/mapping.c | 0 / 47 |
| src/nvim/mark.c | 0 / 56 |
| src/nvim/marktree.c | 0 / 82 |
| src/nvim/match.c | 0 / 22 |
| src/nvim/math.c | 0 / 7 |
| src/nvim/mbyte.c | 0 / 90 |
| src/nvim/mcursor.c | 0 / 67 |
| src/nvim/memfile.c | 0 / 25 |
| src/nvim/memline.c | 0 / 79 |
| src/nvim/memory.c | 0 / 43 |
| src/nvim/menu.c | 0 / 43 |
| src/nvim/message.c | 0 / 130 |
| src/nvim/mouse.c | 0 / 31 |
| src/nvim/move.c | 0 / 61 |
| src/nvim/normal.c | 0 / 164 |
| src/nvim/ops.c | 0 / 48 |
| src/nvim/option.c | 0 / 231 |
| src/nvim/optionstr.c | 0 / 150 |
| src/nvim/path.c | 0 / 67 |
| src/nvim/plines.c | 0 / 30 |
| src/nvim/popupmenu.c | 0 / 32 |
| src/nvim/profile.c | 0 / 49 |
| src/nvim/quickfix.c | 0 / 237 |
| src/nvim/regexp.c | 0 / 176 |
| src/nvim/register.c | 0 / 53 |
| src/nvim/runtime.c | 0 / 93 |
| src/nvim/search.c | 0 / 57 |
| src/nvim/sha256.c | 0 / 6 |
| src/nvim/shada.c | 0 / 57 |
| src/nvim/sign.c | 0 / 50 |
| src/nvim/spell.c | 0 / 72 |
| src/nvim/spellfile.c | 0 / 78 |
| src/nvim/spellsuggest.c | 0 / 42 |
| src/nvim/state.c | 0 / 10 |
| src/nvim/statusline.c | 0 / 16 |
| src/nvim/strings.c | 0 / 74 |
| src/nvim/syntax.c | 0 / 122 |
| src/nvim/tag.c | 0 / 53 |
| src/nvim/terminal.c | 0 / 72 |
| src/nvim/testing.c | 0 / 26 |
| src/nvim/textformat.c | 0 / 13 |
| src/nvim/textobject.c | 0 / 23 |
| src/nvim/ui.c | 0 / 44 |
| src/nvim/ui_client.c | 0 / 19 |
| src/nvim/ui_compositor.c | 0 / 25 |
| src/nvim/undo.c | 0 / 83 |
| src/nvim/usercmd.c | 0 / 33 |
| src/nvim/version.c | 0 / 14 |
| src/nvim/window.c | 0 / 193 |
| src/nvim/winfloat.c | 0 / 20 |
| src/nvim/api/autocmd.c | 0 / 12 |
| src/nvim/api/buffer.c | 0 / 32 |
| src/nvim/api/command.c | 0 / 12 |
| src/nvim/api/deprecated.c | 0 / 42 |
| src/nvim/api/events.c | 0 / 2 |
| src/nvim/api/extmark.c | 0 / 18 |
| src/nvim/api/options.c | 0 / 8 |
| src/nvim/api/tabpage.c | 0 / 9 |
| src/nvim/api/ui.c | 0 / 44 |
| src/nvim/api/vim.c | 0 / 82 |
| src/nvim/api/vimscript.c | 0 / 8 |
| src/nvim/api/win_config.c | 0 / 20 |
| src/nvim/api/window.c | 0 / 19 |
| src/nvim/api/private/converter.c | 0 / 11 |
| src/nvim/api/private/dispatch.c | 0 / 1 |
| src/nvim/api/private/helpers.c | 0 / 48 |
| src/nvim/api/private/validate.c | 0 / 5 |
| src/nvim/eval/buffer.c | 0 / 37 |
| src/nvim/eval/decode.c | 0 / 13 |
| src/nvim/eval/deprecated.c | 0 / 4 |
| src/nvim/eval/encode.c | 0 / 11 |
| src/nvim/eval/executor.c | 0 / 7 |
| src/nvim/eval/fs.c | 0 / 43 |
| src/nvim/eval/funcs.c | 0 / 248 |
| src/nvim/eval/list.c | 0 / 23 |
| src/nvim/eval/typval.c | 0 / 188 |
| src/nvim/eval/userfunc.c | 0 / 108 |
| src/nvim/eval/vars.c | 0 / 110 |
| src/nvim/eval/window.c | 0 / 44 |
| src/nvim/event/libuv_proc.c | 0 / 6 |
| src/nvim/event/loop.c | 0 / 14 |
| src/nvim/event/multiqueue.c | 0 / 18 |
| src/nvim/event/proc.c | 0 / 17 |
| src/nvim/event/rstream.c | 0 / 17 |
| src/nvim/event/signal.c | 0 / 7 |
| src/nvim/event/socket.c | 0 / 13 |
| src/nvim/event/stream.c | 0 / 5 |
| src/nvim/event/time.c | 0 / 8 |
| src/nvim/event/wstream.c | 0 / 8 |
| src/nvim/lua/base64.c | 0 / 3 |
| src/nvim/lua/converter.c | 0 / 31 |
| src/nvim/lua/executor.c | 0 / 91 |
| src/nvim/lua/secure.c | 0 / 3 |
| src/nvim/lua/spell.c | 0 / 2 |
| src/nvim/lua/stdlib.c | 0 / 23 |
| src/nvim/lua/treesitter.c | 0 / 99 |
| src/nvim/lua/xdiff.c | 0 / 8 |
| src/nvim/msgpack_rpc/channel.c | 0 / 32 |
| src/nvim/msgpack_rpc/packer.c | 0 / 16 |
| src/nvim/msgpack_rpc/server.c | 0 / 11 |
| src/nvim/msgpack_rpc/unpacker.c | 0 / 16 |
| src/nvim/os/dl.c | 0 / 1 |
| src/nvim/os/env.c | 0 / 36 |
| src/nvim/os/fileio.c | 0 / 11 |
| src/nvim/os/fs.c | 0 / 63 |
| src/nvim/os/input.c | 0 / 23 |
| src/nvim/os/lang.c | 0 / 13 |
| src/nvim/os/mem.c | 0 / 1 |
| src/nvim/os/os_win_console.c | 0 / 14 |
| src/nvim/os/proc.c | 0 / 6 |
| src/nvim/os/pty_conpty_win.c | 0 / 6 |
| src/nvim/os/pty_proc_unix.c | 0 / 16 |
| src/nvim/os/pty_proc_win.c | 0 / 16 |
| src/nvim/os/shell.c | 0 / 24 |
| src/nvim/os/signal.c | 0 / 10 |
| src/nvim/os/stdpaths.c | 0 / 9 |
| src/nvim/os/time.c | 0 / 11 |
| src/nvim/os/users.c | 0 / 9 |
| src/nvim/tui/input.c | 0 / 25 |
| src/nvim/tui/terminfo.c | 0 / 11 |
| src/nvim/tui/tui.c | 0 / 84 |
| src/nvim/tui/ugrid.c | 0 / 9 |
| src/nvim/tui/termkey/driver-csi.c | 0 / 24 |
| src/nvim/tui/termkey/driver-ti.c | 0 / 13 |
| src/nvim/tui/termkey/termkey.c | 0 / 38 |
| src/nvim/viml/parser/expressions.c | 0 / 18 |
| src/nvim/viml/parser/parser.c | 0 / 4 |
| src/nvim/vterm/encoding.c | 0 / 5 |
| src/nvim/vterm/keyboard.c | 0 / 5 |
| src/nvim/vterm/mouse.c | 0 / 3 |
| src/nvim/vterm/parser.c | 0 / 7 |
| src/nvim/vterm/pen.c | 0 / 19 |
| src/nvim/vterm/screen.c | 0 / 41 |
| src/nvim/vterm/state.c | 0 / 47 |
| src/nvim/vterm/vterm.c | 0 / 17 |
| src/tee/tee.c | 0 / 2 |
| src/wasm/wasm_stubs.c | 0 / 23 |
| src/xdiff/xdiffi.c | 0 / 19 |
| src/xdiff/xemit.c | 0 / 8 |
| src/xdiff/xhistogram.c | 0 / 8 |
| src/xdiff/xpatience.c | 0 / 10 |
| src/xdiff/xprepare.c | 0 / 8 |
| src/xdiff/xutils.c | 0 / 14 |
| src/xxd/xxd.c | 0 / 16 |
