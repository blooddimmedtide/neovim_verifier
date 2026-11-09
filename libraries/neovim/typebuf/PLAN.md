# input.c typeahead and stuff buffers (was getchar.c)

Upstream `src/nvim/getchar.c` is `src/nvim/input.c` at the pinned commit
7b87ce822e6fd45a4d9993599c2854afdb0dc4dd. This target claims only the typeahead
(`typebuf`) and stuff-buffer (`readbuf1`/`readbuf2`) functions of input.c. The rest of
input.c (vgetorpeek, mappings, scripts, redo, getchar()) is not claimed here.

Tool: Frama-C WP (Typed+Cast, -wp-rte), Z3 + CVC5.

| function | status |
|---|---|
| free_buff | open |
| add_buff | open |
| read_readbuf | open |
| read_readbuffers | open |
| start_stuff | open |
| stuff_empty | open |
| readbuf1_empty | open |
| init_typebuf | open |
| ins_typebuf | open |
| typebuf_changed | open |
| typebuf_typed | open |
| typebuf_maplen | open |
| del_typebuf | open |
| alloc_typebuf | open |
| free_typebuf | open |
| put_string_in_typebuf | open |
