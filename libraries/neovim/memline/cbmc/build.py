"""Verbatim, sha256-pinned copy of memline.c long_to_char / char_to_long for CBMC.
Usage: python3 -I build.py <neovim checkout at 7b87ce8> <out.c>"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "tools"))
from extract_c import build
ML = "src/nvim/memline.c"
PIECES = [
    (ML, "long_to_char", "1800b390d551632a7dd286c586374e7f85ebbc049b5c44e7b19909f7cc63c68e"),
    (ML, "char_to_long", "51d2031a345a7dde3fdeb0ffffc42e82889df695e385ed048add75bee8dc0067"),
    (ML, "ml_check_b0_id", "8a559552929085d2fdc99e3cfd1d0abafb4e5bca3d83dd7ad58f75a3e7172080"),
    (ML, "ml_check_b0_strings", "93a2ac1ea81e8fbf802ffa0dadcaae4e81add57eef5461b2d35afa3525af6e72"),
    (ML, "b0_magic_wrong", "00d7b69db01b3d036391d105c85b9bc4293d4dbfe6eab92b07165761390877f0"),
]
CHECKS = [(ML, l) for l in [
    "  BLOCK0_ID0 = 'b',              // block 0 id 0",
    "  BLOCK0_ID1 = '0',              // block 0 id 1",
    "  B0_FNAME_SIZE_ORG = 900,      // what it was in older versions",
    "  B0_FNAME_SIZE_CRYPT = 890,    // 10 bytes used for other things",
    "  B0_UNAME_SIZE = 40,",
    "  B0_HNAME_SIZE = 40,",
    "  B0_MAGIC_LONG = 0x30313233,",
    "  B0_MAGIC_INT = 0x20212223,",
    "  B0_MAGIC_SHORT = 0x10111213,",
    "  B0_MAGIC_CHAR = 0x55,",
    "  char b0_id[2];                     ///< ID for block 0: BLOCK0_ID0 and BLOCK0_ID1.",
    "  char b0_version[10];               ///< Vim version string",
    "  char b0_fname[B0_FNAME_SIZE_ORG];  ///< name of file being edited",
    "  int16_t b0_magic_short;            ///< check for byte order of short",
    "  char b0_magic_char;                ///< check for last char",
]]
PRELUDE = open(os.path.join(HERE, "prelude.h")).read()
if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], PRELUDE, CHECKS, PIECES)
