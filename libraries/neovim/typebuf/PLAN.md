# input.c typeahead and stuff buffers (was getchar.c)

Upstream `src/nvim/getchar.c` is `src/nvim/input.c` at the pinned commit
7b87ce822e6fd45a4d9993599c2854afdb0dc4dd. This target claims only the typeahead
(`typebuf`) and stuff-buffer (`readbuf1`/`readbuf2`) functions of input.c. The rest of
input.c (vgetorpeek, mappings, scripts, redo, getchar()) is not claimed here.

Tool: Frama-C WP (Typed+Cast, -wp-rte), Z3 + CVC5.

| function | status |
|---|---|
| free_buff | proved 21/21 goals (upstream), smoke tests clean |
| add_buff | open: 87/94 goals; memmove/memcpy ranges after kv_ensure_space time out (the xrealloc result needs separation facts the kv_resize macro cannot pass as ghost arguments) |
| read_readbuf | proved 50/50 goals (upstream), smoke tests clean |
| read_readbuffers | proved 22/22 goals (upstream), smoke tests clean |
| start_stuff | proved 5/5 goals (upstream), smoke tests clean |
| stuff_empty | proved 10/10 goals (upstream), smoke tests clean |
| readbuf1_empty | proved 4/4 goals (upstream), smoke tests clean |
| init_typebuf | proved 14/14 goals (upstream), smoke tests clean |
| ins_typebuf | open: proof run did not finish in time (largest function; run_wp.sh with WP_WALL=2400) |
| typebuf_changed | proved 13/13 goals (upstream), smoke tests clean |
| typebuf_typed | proved 4/4 goals (upstream), smoke tests clean |
| typebuf_maplen | proved 4/4 goals (upstream), smoke tests clean |
| del_typebuf | open: 76/79 goals; 3 content post-conditions (bytes moved by the two memmoves) time out at 120 s |
| alloc_typebuf | proved 25/25 goals (upstream, and fixed), smoke tests clean |
| free_typebuf | proved 29/29 goals (upstream), smoke tests clean |
| put_string_in_typebuf | open: contract written, depends on ins_typebuf and del_typebuf; not run |

Proved: 12 of 16. Open: del_typebuf, add_buff, ins_typebuf, put_string_in_typebuf.
Run: `bash wp/run_wp.sh <neovim tree> upstream|fixed 30 [functions]` (results in wp/results-upstream.txt).
Functions in fixed mode: the 11 unchanged functions have the same text and contracts; alloc_typebuf proved 26/26 on the fixed text.
