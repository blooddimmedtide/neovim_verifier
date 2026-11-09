"""Standalone copy of memfile.c / memline.c block and pointer helpers for Frama-C WP.

Usage: python3 -I build.py <neovim checkout at the pinned commit> <out.c>
Each function body is the exact upstream text, sha256 pinned (tools/extract_c.py).
ACSL contracts sit on prototypes in the prelude, so the extracted text is not
touched at all. Types are copied from memfile_defs.h / memline.c / memline_defs.h;
buf_T keeps only the memline fields these functions use (checked below).
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "tools"))
from extract_c import build

MF, ML = "src/nvim/memfile.c", "src/nvim/memline.c"
PIECES = [  # upstream 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
    (MF, "mf_new_page_size", "293a96437fd47fb36042815b208ef2c12f53445cf33baba078df3415ca2e20cd"),
    (MF, "mf_alloc_bhdr", "222e4ce47f1006cec6be9b52ab76b8df3fee4c560b8ca37ed1da8a21c2ead839"),
    (MF, "mf_free_bhdr", "1eb9c21cde49d737d0e60653a3ce543ccf1fb3e3833eeab296eadb5556117048"),
    (MF, "mf_ins_free", "8c30d072385087352e27313f0be1802149dbcf16f922296940beee91fd0c2ece"),
    (MF, "mf_rem_free", "5e589b6ab569558c0f6e048a9b8fadffe5b3f004ee6dacfde9e89c42c491d041"),
    (MF, "mf_free_fnames", "11ac35bfecda05ae55c5091f10a4e9514ce78f5a4fd19cfe965fe495a533b944"),
    (MF, "mf_set_fnames", "d8f2553659e8e70cb0538356b66cc0d0fb0fe3c506cd44d472bb1f35d3154e0d"),
    (MF, "mf_need_trans", "142a3d4315b5fc9af92925e19538ffb1f10c841c99495f854bf287a2da1cb381"),
    (ML, "ml_new_data", "09407850af591dd832887e3b7ac2ba54ca4a084c67c6726e8ae7f0c0da367718"),
    (ML, "ml_new_ptr", "1b93f61c5a9b363920642783ddbf07084a6d0fb46892a31670ebf8516475361f"),
    (ML, "ml_flush_deleted_bytes", "351cb2db465ebd54b273614f12769be00a27bd3624b921e5224a0c7185678437"),
    (ML, "ml_line_alloced", "84656911ced12fcfd845bfb3ebedbdf0e79fcb7a61e95c2c7ff3394aee088cd7"),
    (ML, "ml_add_deleted_len", "6fa08d6bfd4b5db7a45ace1dbb3dbf06dadea7f539cffa708c29fe560b892f00"),
    (ML, "ml_add_deleted_len_buf", "c0e2109260bf4a54b1a75090344ca5e60ac31afd723b117bfff141e351a47935"),
    (ML, "ml_get", "c587abbebb0bbb274610bf7cae989333458d6df19aa8130db70eddca2a958a44"),
    (ML, "ml_get_buf", "9a01a5d3ef30bcae13606b4e1a93347f389d51f3adcd5ff4c7a079ca276629ad"),
    (ML, "ml_get_buf_mut", "425ee1b512741fb254bcc34f87afa4881b947f998cc48f5acc0cbd752f3659f4"),
    (ML, "ml_get_pos", "1edd975894537a7577a977b438b9e3b47e9094dd3fedd4c4540f5634d78a2938"),
    (ML, "ml_get_pos_len", "625a45ec669ac8f72ff128201e13b36d86a67aeedc631586076a1251a415ebfc"),
    (ML, "ml_timestamp", "ffdb79d158e930fd37d728b3914861674595113e5cac6884786bce44d52005dc"),
    (ML, "ml_append", "58907eeeaffba1df282085d8a8f3a9906e2e2cabec55e020416e6ae0f8138f15"),
    (ML, "ml_replace", "50557e15b6746cc4c7844b8fd086e17694a01fb20be6a77863b8efc895015ea3"),
    (ML, "ml_replace_len", "aa60333f6fffbe8b4086b669f0936ca072fb4ea062eb3add23f8ab40866c1b6b"),
    (ML, "ml_delete", "c55f30157439395cc6f1a7ac5159cb02ee0bf6035904d65c9b6406e0c7db3985"),
    (ML, "ml_add_stack", "bede1c526990704cf8f0bb5ad43cd5a3107373cc2708b0b68c0fe21458a17cfc"),
]
CHECKS = [
    (ML, "#define CHECK(c, s) do {} while (0)"),
    ("src/nvim/memory.h", "    void **ptr_ = (void **)&(ptr); \\"),
    ("src/nvim/memory.h", "    *ptr_ = NULL; \\"),
    (ML, "#define STACK_INCR      5       // nr of entries added to ml_stack at a time"),
    (ML, "#define HEADER_SIZE (offsetof(DataBlock, db_index))  // size of data block header"),
    (ML, "  (uint16_t)((mfp->mf_page_size - offsetof(PointerBlock, pb_pointer)) / sizeof(PointerEntry))"),
    (ML, "  DATA_ID = (('d' << 8) + 'a'),  // data block id"),
    (ML, "  PTR_ID = (('p' << 8) + 't'),   // pointer block id"),
    (ML, "  unsigned db_free;             // free space available"),
    (ML, "  long db_line_count;           // number of lines in this block"),
    (ML, "  uint16_t pb_count_max;        // maximum value for pb_count"),
    (ML, "  int pe_page_count;            // number of pages in block pe_bnum"),
    ("src/nvim/memfile_defs.h", "typedef int64_t blocknr_T;"),
    ("src/nvim/memfile_defs.h", "  unsigned mf_page_size;             ///< number of bytes in a page"),
    ("src/nvim/memfile_defs.h", "  bhdr_T *mf_free_first;             ///< first block header in free list"),
    ("src/nvim/memfile_defs.h", "  blocknr_T mf_neg_count;            ///< number of negative blocks numbers"),
    ("src/nvim/memline_defs.h", "  infoptr_T *ml_stack;        // stack of pointer blocks (array of IPTRs)"),
    ("src/nvim/memline_defs.h", "  int ml_stack_top;             // current top of ml_stack"),
    ("src/nvim/memline_defs.h", "  int ml_stack_size;            // total number of entries in ml_stack"),
    ("src/nvim/memline_defs.h", "#define ML_LINE_DIRTY   0x02    // cached line was changed and allocated"),
    ("src/nvim/memline_defs.h", "  int ml_flags;"),
    ("src/nvim/buffer_defs.h", "  size_t deleted_bytes;"),
    ("src/nvim/buffer_defs.h", "  size_t deleted_codepoints;"),
    ("src/nvim/buffer_defs.h", "  size_t deleted_codeunits;"),
    ("src/nvim/buffer_defs.h", "  bool update_need_codepoints;"),
    ("src/nvim/globals.h", "EXTERN int inhibit_delete_count INIT( = 0);"),
    ("src/nvim/pos_defs.h", "typedef int32_t linenr_T;"),
    ("src/nvim/pos_defs.h", "typedef int colnr_T;"),
    ("src/nvim/memline.h", "  ML_APPEND_NEW = 1,   // starting to edit a new file"),
    (ML, "  UB_FNAME = 0,         // update timestamp and filename"),
    ("src/nvim/pos_defs.h", "  colnr_T coladd;"),
]
PRELUDE = open(os.path.join(HERE, "prelude.h")).read()

if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], PRELUDE, CHECKS, PIECES)
