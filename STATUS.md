# Neovim verification status

**0 / 8107 functions done** (verified, or a verified fix) across 189 files.
A function is done only when every property in its contract is proved; partial results stay open.

## Files with work in progress or done

| File | Done | Partial | Open | Total |
|---|---|---|---|---|
| src/nvim/base64.c | 0 | 4 | 0 | 4 |

## Function details

| File | Function | Status | Evidence | Notes |
|---|---|---|---|---|
| src/nvim/base64.c | `base64_encode` | candidate | base64/wp (Frama-C WP), base64/equiv (CBMC) | RFC 4648 output for every input, one allocation returned; see base64/CLAIM.md. Needs reviews + mutants before full-correctness |
| src/nvim/base64.c | `base64_decode` | fixed-candidate | base64/wp (Frama-C WP, upstream 120/120 under 2 GiB, fixed 118/118 no limit) | upstream wrong at >= 2 GiB (findings/base64-decode-over-2gib.md); fix in verified_neovim proved for all inputs. Needs reviews + mutants |
| src/nvim/base64.c | `vim_htobe64` | candidate | base64/bridge (CBMC, no loops, all inputs) | equals big-endian reading of the bytes |
| src/nvim/base64.c | `vim_htobe32` | candidate | base64/bridge (CBMC, no loops, all inputs) | equals big-endian reading of the bytes |

## All files

| File | Done / Total |
|---|---|
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
