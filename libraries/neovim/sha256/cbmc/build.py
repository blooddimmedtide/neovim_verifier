"""Copy of src/nvim/sha256.c with one CBMC loop contract added to sha256_update.

Usage: python3 -I build.py <neovim checkout> <out.c>
The loop `while (length >= SHA256_BUFFER_SIZE)` gets __CPROVER_assigns /
__CPROVER_loop_invariant / __CPROVER_decreases clauses (they name the recorder globals
of harness_stream.c). Everything else is the upstream text; removing the inserted
clause line gives the upstream file back (checked). Works on the fixed fork too.
"""
import sys

ANCHOR = "  while (length >= SHA256_BUFFER_SIZE) {\n"
CONTRACT = (
    "  while (length >= SHA256_BUFFER_SIZE)\n"
    "    __CPROVER_assigns(length, input, rec_calls, __CPROVER_object_upto(ctx->state, sizeof(ctx->state)))"
    " __CPROVER_loop_invariant(LOOP_INV) __CPROVER_decreases(length)\n"
    "  {\n")

src = open(f"{sys.argv[1]}/src/nvim/sha256.c").read()
if src.count(ANCHOR) != 1:
    sys.exit("build: loop anchor not found once in sha256.c")
out = src.replace(ANCHOR, CONTRACT)
assert out.replace(CONTRACT, ANCHOR) == src
open(sys.argv[2], "w").write(out)
