"""Annotated standalone copy of marktree.c leaf functions for Frama-C WP.

Usage: python3 -I build.py <neovim checkout> <out.c> [upstream|fixed]
Each function is the exact pinned text (sha256). ACSL goes in comments only, and the
build checks that removing every /*@ ... */ gives the pinned text back. Every line of
stubs/vp_marktree.h that copies a Neovim declaration is checked against the headers.
"""
import hashlib, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "tools"))
from extract_c import find
from contracts import LOGIC, contracts, annotations

F, H = "src/nvim/marktree.c", "src/nvim/marktree.h"
PIECES = [  # (file, function, sha256 at upstream 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd)
    (H, "mt_end", None), (H, "mt_invalid", None),
    (F, "pos_leq", "a3a807c20e5c19952c65708cab88f288b916224d8fb8e80dda091894c104913b"),
    (F, "pos_less", "7db32e4a24c454640bbf243321e64978db8c2d4335e8a5e56d4f8706553e1873"),
    (F, "relative", "807edc70b90c43336c44948c4b2ff2bc139965eb35bfb18aa673ca73856a66ee"),
    (F, "unrelative", "2d4bf9fd9c668cf1331db8d38584d7520d760d790020810415ecf7fd73eb6ddf"),
    (F, "compose", "dc816fca5a467451bbe7df97a86dcb16202ef352c3736866971673c773d0fd95"),
    (F, "key_cmp", "cdbcf9cdb1c39200be148d5ca6d68f5ea6ad022219a106d83fc647fe20821fa8"),
    (F, "marktree_getp_aux", "3e39e9bf7134789ecf87c7d4241475ed2500ec54f77bf20112069c3a9013589c"),
    (F, "intersection_has", "4297d150fb4c74d391b858d11f70343c929e74035687807886bda7abd98390ba"),
    (F, "intersect_item_pos", "f5553500d0fe9802a3d413f7386b9b9a871b5c4408bbcbeca8acabc3fcad720c"),
    (F, "meta_describe_key_inc", "b0cf035931fc01d1d89cb057e76f573dcfb8760e90fd5599a931c6d64aab32e7"),
    (F, "meta_describe_key", "56a265b82a7ecb227047038d0a530d2f2618fc1a234ec339c63f1e861e0d5a27"),
    (F, "marktree_itr_node_done", "a20c2dd50d22750dbd6f739caa2d3ac69bbf6e11247fda53dfb070a6e6038a9e"),
    (F, "marktree_itr_pos", "1452afc2c477f614d372e95a88723243701d557d5cd903993149b297fec7b85e"),
    (F, "itr_eq", "f1e183772bc3da9d06ca91cde461c7e245205ddfd81102cb6ebd61fdc0611791"),
    (F, "meta_has", "ed692d28e1e8be06d312d3a61cb7e3da428ac08d00c95cd97bdb44225401d5c0"),
]
HSHA = {"mt_end": "d5b42722affb2b6d2a71c4b8a72d3528ae7c0720c5ed7a946d07ef64b0a1d4fa",
        "mt_invalid": "9e5995241d29d115333955bbf9292083d657f3ba883281602165faf8e75a6323"}
FIXED_SHA = {"meta_has": "df4ea46a0f3367e14402dbfa52cefc8bdce4d78cb82a7f1193619f718f0bf9dc"}  # verified_neovim fix
EXEMPT = ("#include", "/*@", "void vp_assert", "#define assert", "typedef struct { void",
          "typedef struct mtnode_s", "typedef struct { size_t size", "  MTKey key[", "// ")


def no_comment_tokens(where, text):
    """ACSL must not contain comment tokens: an annotation holding `*/ code /*@` would smuggle
    code past the strip check (review finding 1)."""
    body = text
    if "/*" in body or "*/" in body:
        sys.exit(f"build: {where}: annotation text contains a comment token")


def strip(s):
    s = re.sub(r"^[ \t]*/\*@.*?\*/\n", "", s, flags=re.S | re.M)
    s = re.sub(r" /\*@.*?\*/", "", s, flags=re.S)
    return re.sub(r"/\*@.*?\*/ ", "", s, flags=re.S)


def check_prelude(tree):
    hdr = "\n".join(open(f"{tree}/src/nvim/{h}").read() for h in ("marktree.h", "marktree_defs.h"))
    hdr += open(f"{tree}/src/klib/kvec.h").read()
    lines = set(hdr.split("\n"))
    for l in open(f"{HERE}/stubs/vp_marktree.h").read().split("\n"):
        if not l.strip() or l.startswith(EXEMPT) or l.startswith("#define MT_BRANCH_FACTOR") \
           or l.startswith(("#define mt_generic_cmp", "#define MT_MAX_DEPTH", "#define rawkey")):
            continue
        if l not in lines:
            sys.exit(f"build: prelude line not in the pinned headers: {l!r}")
    # review finding 2: each copied type must match the header as a whole block, in order
    full = hdr.replace("  struct mtnode_inner_s s[];\n", "")  # the prelude leaves out MTNode's inner part
    pre = open(f"{HERE}/stubs/vp_marktree.h").read()
    for blk in re.findall(r"^(?:typedef struct \{|typedef enum \{|struct mtnode_s \{)\n.*?^\}[^\n]*;$", pre, re.S | re.M):
        if blk not in full:
            sys.exit(f"build: prelude type block differs from the pinned headers: {blk.splitlines()[-1]!r}")
    if "  MT_BRANCH_FACTOR = 10," not in open(f"{tree}/src/nvim/marktree_defs.h").read():
        sys.exit("build: MT_BRANCH_FACTOR changed")
    if "#define mt_generic_cmp(a, b) (((b) < (a)) - ((a) < (b)))" not in open(f"{tree}/{F}").read():
        sys.exit("build: mt_generic_cmp changed")
    if "  MT_MAX_DEPTH     = 20," not in hdr:
        sys.exit("build: MT_MAX_DEPTH changed")
    if "#define rawkey(itr) ((itr)->x->key[(itr)->i])" not in open(f"{tree}/{F}").read():
        sys.exit("build: rawkey changed")
    if "typedef kvec_withinit_t(uint64_t, 4) Intersection;" not in hdr:
        sys.exit("build: Intersection changed")
    m = re.search(r"const uint16_t cmp_mask = (.*);", open(f"{tree}/{F}").read())
    if m.group(1) != "MT_FLAG_RIGHT_GRAVITY | MT_FLAG_END | MT_FLAG_REAL | MT_FLAG_LAST":
        sys.exit("build: key_cmp mask changed")  # 0x4000|0x2|0x1|0x8000 == 0xC003 in contracts.py


def main(tree, out, mode="upstream"):
    fixed = mode == "fixed"
    check_prelude(tree)
    C, A = contracts(fixed), annotations(fixed)
    no_comment_tokens("LOGIC", LOGIC.strip()[3:-2])  # inside its own /*@ ... */
    parts = ['#include "vp_marktree.h"', LOGIC]
    cache = {}
    for path, name, want in PIECES:
        lines = cache.setdefault(path, open(f"{tree}/{path}").read().split("\n"))
        s, e = find(lines, name)
        piece = "\n".join(lines[s:e + 1])
        h = hashlib.sha256(piece.encode()).hexdigest()
        want = HSHA.get(name, want)
        if fixed and name in FIXED_SHA:
            want = FIXED_SHA[name]
        if h != want:
            sys.exit(f"build: {name} ({path}:{s + 1}) differs from the pinned {mode} text: sha256 {h}")
        no_comment_tokens(name + " contract", C[name])
        ann = piece
        for kind, anchor, annot in A.get(name, []):
            if ann.count(anchor) != 1:
                sys.exit(f"build: {name}: anchor not found once: {anchor!r}")
            no_comment_tokens(name + " annotation", annot)
            indent = re.match(r"\s*", anchor).group(0)
            ann = ann.replace(anchor, f"{indent}/*@ {annot} */\n{anchor}")
        if strip(ann) != piece:
            sys.exit(f"build: {name}: stripping the annotations does not give the source back")
        parts.append(f"// {path}:{s + 1} ({mode}, verbatim plus ACSL comments)\n/*@ {C[name]} */\n{ann}\n")
    open(out, "w").write("\n".join(parts))


if __name__ == "__main__":
    main(*sys.argv[1:])
