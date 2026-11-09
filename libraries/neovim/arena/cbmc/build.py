"""Write a standalone C file holding the exact arena text from src/nvim/memory.c.

Usage: python3 -I build.py <neovim checkout> <out.c>
The piece runs from '#define REUSE_MAX 4' to the end of arena_strdup and is
pinned by sha256; any upstream change stops the build until it is reviewed.
"""
import hashlib, sys

FIXED_PIN = "71aa9a949d3c1262d658ffcb02de7217744db13965daa5b1bfd85a80505d7777"  # blooddimmedtide/verified_neovim branch fix-arena-alloc-size-wrap
PIN = "3fd72a7c8a75f2a6ecfb1b2e2ccaa2c7e4ff4407d0dc32f53c1a3cb64e47ef3c"
START, END = "#define REUSE_MAX 4\n", "  return arena_memdupz(arena, str, strlen(str));\n}\n"

PRELUDE = r'''
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <stdlib.h>
#include <assert.h>
#define NUL '\0'
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define FUNC_ATTR_NONNULL_ARG(...)
typedef struct consumed_blk { struct consumed_blk *prev; } *ArenaMem;   // memory_defs.h
typedef struct { char *cur_blk; size_t pos, size; } Arena;              // memory_defs.h
#define ARENA_BLOCK_SIZE 4096
#define ARENA_EMPTY { .cur_blk = NULL, .pos = 0, .size = 0 }
size_t arena_alloc_count = 0;                                           // memory.h
void *xmalloc(size_t size);
void xfree(void *p);
void preserve_exit(const char *msg);   // exits; never returns
static char e_outofmem[] = "E342: Out of memory!";
// prototypes normally from memory.h.generated.h
void *arena_alloc(Arena *arena, size_t size, bool align);
static size_t arena_align_offset(uint64_t off);
void *alloc_block(void);
void free_block(void *block);
static void arena_free_reuse_blks(void);
char *arena_allocz(Arena *arena, size_t size);
char *arena_memdupz(Arena *arena, const char *buf, size_t size);
'''

def main(tree, out):
    src = open(f"{tree}/src/nvim/memory.c").read()
    a = src.index(START); b = src.index(END, a) + len(END)
    piece = src[a:b]
    h = hashlib.sha256(piece.encode()).hexdigest()
    if len(sys.argv) > 3 and sys.argv[3] == "--print-hash":
        print(h); return
    fixed = h == FIXED_PIN
    if not fixed and h != PIN:
        sys.exit(f"build: arena piece of memory.c changed: sha256 {h}")
    line = src[:a].count("\n") + 1
    tag = "#define NVIM_FIXED_ARENA 1  // fixed fork version\n" if fixed else ""
    open(out, "w").write(tag + PRELUDE + f"\n// src/nvim/memory.c:{line} (verbatim)\n" + piece)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
