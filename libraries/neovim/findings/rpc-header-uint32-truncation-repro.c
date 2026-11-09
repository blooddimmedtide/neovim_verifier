// Reproducer: build init.c with unpacker/cbmc/build_init.py, then
// gcc -I <nvim>/src/mpack -DINIT_C="\"init.c\"" rpc-header-uint32-truncation-repro.c
#include INIT_C
#include "conv.c"
#include <stdio.h>
MsgpackRpcRequestHandler msgpack_rpc_get_handler_for(const char *name, size_t len, Error *e)
{ MsgpackRpcRequestHandler h = {0}; printf("  handler lookup: %.*s\n", (int)len, name); return h; }
void api_set_error(Error *err, ErrorType t, const char *f, ...) { err->type = t; }
static void run(const char *label, const char *b, size_t n)
{
  Unpacker p; unpacker_init(&p); p.read_ptr = b; p.read_size = n; p.state = 0;
  bool ok = unpacker_parse_header(&p);
  printf("%s: ok=%d type=%d request_id=%u state=%d\n", label, ok, (int)p.type, p.request_id, p.state);
}
int main(void)
{
  // [2^32+2, "a", []] : type is a uint64 that is not 2
  const char m1[] = "\x93\xcf\x00\x00\x00\x01\x00\x00\x00\x02\xa1" "a" "\x90";
  run("type 2^32+2 (should be rejected)", m1, sizeof m1 - 1);
  // [0, 2^32+7, "a", []] : msgid does not fit 32 bits
  const char m2[] = "\x94\x00\xcf\x00\x00\x00\x01\x00\x00\x00\x07\xa1" "a" "\x90";
  run("msgid 2^32+7 (should be rejected)", m2, sizeof m2 - 1);
  const char m3[] = "\x93\x02\xa1" "a" "\x90";
  run("normal notification", m3, sizeof m3 - 1);
}
