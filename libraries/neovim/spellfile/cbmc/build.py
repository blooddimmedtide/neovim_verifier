"""Write a standalone C file holding exact upstream text of the spellfile.c reader helpers.

Usage: python3 -I build.py <neovim checkout> <out.c>
Each piece is copied verbatim (signature to closing brace) and checked against the
sha256 recorded below; an upstream change stops the build until it is reviewed again.
The FILE*, allocator and slang_T definitions the pieces use come from model.h.
"""
import hashlib, re, sys

PIECES = {  # name -> (file, start regex, end regex, sha256)
    "SPELL_READ_BYTES": ("src/nvim/spellfile.c", r"^#define SPELL_READ_BYTES\(", r"^  \} while \(0\)$",
                         None),
    "SPELL_READ_NONNUL_BYTES": ("src/nvim/spellfile.c", r"^#define SPELL_READ_NONNUL_BYTES\(", r"^  \} while \(0\)$",
                                None),
    "spell_check_magic_string": ("src/nvim/spellfile.c", r"^static inline int spell_check_magic_string\(", r"^\}", None),
    "read_string": ("src/nvim/fileio.c", r"^char \*read_string\(", r"^\}", None),
    "read_cnt_string": ("src/nvim/spellfile.c", r"^static char \*read_cnt_string\(", r"^\}", None),
    "read_region_section": ("src/nvim/spellfile.c", r"^static int read_region_section\(", r"^\}", None),
}
PRELUDE_CHECKS = [
    ("src/nvim/spellfile.c", '#define VIMSPELLMAGIC "VIMspell"  // string at start of Vim spell file'),
    ("src/nvim/spellfile.c", "#define VIMSPELLMAGICL (sizeof(VIMSPELLMAGIC) - 1)"),
    ("src/nvim/spell_defs.h", "enum { MAXREGIONS = 8, };  ///< Number of regions supported."),
    ("src/nvim/spell_defs.h", "  SP_TRUNCERROR = -1,  ///< spell file truncated error"),
    ("src/nvim/spell_defs.h", "  SP_FORMERROR  = -2,  ///< format error in spell file"),
    ("src/nvim/spell_defs.h", "  SP_OTHERERROR = -3,  ///< other error while reading spell file"),
    ("src/nvim/spell_defs.h", "  char sl_regions[MAXREGIONS * 2 + 1];"),
]

def main(tree, out, shafile):
    want = dict(l.split() for l in open(shafile) if l.strip())
    for path, text in PRELUDE_CHECKS:
        if text not in open(f"{tree}/{path}").read().split("\n"):
            sys.exit(f"build: {path} no longer contains: {text}")
    parts = ['#include "model.h"']
    for name, (path, sp, ep, _) in PIECES.items():
        lines = open(f"{tree}/{path}").read().split("\n")
        starts = [i for i, l in enumerate(lines) if re.match(sp, l)]
        if len(starts) != 1:
            sys.exit(f"build: {name}: expected one definition, found {len(starts)}")
        s = e = starts[0]
        while not re.match(ep, lines[e]):
            e += 1
        piece = "\n".join(lines[s:e + 1])
        h = hashlib.sha256(piece.encode()).hexdigest()
        if want.get(name) != h:
            sys.exit(f"build: {name} ({path}:{s+1}) sha256 {h} not reviewed")
        parts.append(f"// {path}:{s + 1} (verbatim)\n{piece}\n")
    open(out, "w").write("\n".join(parts))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else __file__.replace("build.py", "reviewed.sha256"))
