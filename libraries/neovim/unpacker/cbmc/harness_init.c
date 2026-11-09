// CBMC harness for unpacker_init (real mpack_parser_init / mpack_tokbuf_init from object.c).
// Spec, from what an "init" must leave for unpacker_advance / unpack: an empty parser of the
// default depth (32) whose user data points back at the unpacker, an empty token reader, no
// error, an empty arena, no pending grid_line event. Fields it does not own stay as they were.
#include INIT_C
#include <assert.h>
#include <string.h>
Unpacker nondet_unpacker(void);

void h_unpacker_init(void)
{
  Unpacker u = nondet_unpacker(), before = u;   // any prior contents
  unpacker_init(&u);
  assert(u.parser.data.p == &u);
  assert(u.parser.capacity == 32 && u.parser.size == 0);
  assert(u.parser.exiting == 0 && u.parser.status == 0);
  assert(u.parser.tokbuf.ppos == 0 && u.parser.tokbuf.plen == 0 && u.parser.tokbuf.passthrough == 0);
  assert(u.parser.items[0].pos == (size_t)-1);
  for (int i = 1; i <= 32; i++) {            // stack nodes start cleared
    assert(u.parser.items[i].pos == 0 && u.parser.items[i].key_visited == 0);
  }
  assert(u.reader.ppos == 0 && u.reader.plen == 0 && u.reader.passthrough == 0);
  assert(u.unpack_error.type == kErrorTypeNone && u.unpack_error.msg == NULL);
  assert(u.arena.cur_blk == NULL && u.arena.pos == 0 && u.arena.size == 0);
  assert(u.has_grid_line_event == false);
  // frame: fields unpacker_init does not own are unchanged
  assert(u.read_ptr == before.read_ptr && u.read_size == before.read_size);
  assert(u.state == before.state && u.nevents == before.nevents && u.ncalls == before.ncalls);
  assert(memcmp(&u.result, &before.result, sizeof u.result) == 0);
}
