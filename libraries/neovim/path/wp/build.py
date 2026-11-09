"""Annotated standalone copy of path.c functions for Frama-C WP (UNIX build).

Usage: python3 -I build.py <neovim checkout> <out.c> [upstream|fixed]
Each function is the exact upstream (or fixed-fork) text, sha256 pinned. ACSL goes
in comments only, and the build checks that removing every /*@ ... */ gives the
pinned text back exactly (after the declared tool patches in tool_patches.py).
"""
import hashlib, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "tools"))
from extract_c import find
from contracts import LOGIC, C, GHOST, SIG, annotations
from tool_patches import PATCHES

F = "src/nvim/path.c"
SHA = {  # upstream 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd, in callee-first order
    "vim_ispathsep": "1795324c1fbcb991fe5ddddb9ef6dc66514880e585ffcab79b4d5ce321d059f9",
    "vim_ispathsep_nocolon": "944b159c8e3e23a40693d857b9fc687c6a44aa2c8e9aab7445a9d4a089ff71fd",
    "vim_ispathlistsep": "d9482677e5e69590af1f4004df9258f8ec1c9c74497e35bdce8ea2767cd28d80",
    "path_head_length": "00d680ccfef5b7ba33626fa687d53ce433ff1e76b52ea98afdcccb9f17906212",
    "is_path_head": "9e1732897f282ac5b411b2960798608b1b8640f2290b690d27a89c67ca2d7964",
    "path_skip_sep": "5bd4f7d187bd387d6d5f7af684476576d569cdf257e674c4020f9f132fa26a8a",
    "get_past_head": "6a84f318ba0a6c78f7575c9755bd90b7e0c7b0d690851e01cfc944f6cbaee5c9",
    "path_tail": "da741aa1742b05485b6cbdc8627e628ee8f53b9df7164c5e04020b8dcd0b077e",
    "path_next_component": "45dedd2d297a911ff042ac323ae65df680f9d836e4de88389ba1c9317a3883a9",
    "path_is_absolute": "74c75e555971951578932c4eabe17db402df02363972cef047ab88b544762096",
    "path_has_drive_letter": "c7a1a3c22bf856b0c084b71a785823d32822940f38433e70dc3a757b0511f8a8",
    "path_is_url": "41b88effbbbf13f1aac0a017d7a960175ebb39ea5da59059339d72dbec062e57",
    "path_with_url": "590615db83248f3fdab9019fd300cedc596c11370402264fce30b3a93dc4226a",
    "vim_isAbsName": "5aa01b38e65eed63d95f1c547ad1a92dc9ddd6f1adcec6ff46884cbe1ef854ce",
    "after_pathsep": "f0844600fa21d41dbc73ae9d5e2cb4ca1dd0165f47b69496e7f2f78c06a77b9b",
    "path_tail_with_sep": "b5f33925f2e170571434579c48d82569cd8339c3c9a22ad50987aa32a56e8388",
    "add_pathsep": "30da35d8e8ce0208b15ab8e08a0c1d3fef2d5f8f7da14cfaf4137ed66b8ee5f2",
    "path_to_slash": "74fdbbd964ad41bf235e8713eab9598f4f14c4a97ed67032598edd77b4b4f0d8",
    "path_to_backslash": "e1ce9afcf790005f7d6ca890a190c30fe0b629ccba195f3ad99f74e9a03c43b3",
    "invocation_path_tail": "98ec5fa5d4d44edf0a06e92c4a87f6d8c4d2e939d2365974bddf4de70103d713",
}
FIXED_SHA = {  # verified_neovim branch claude/project-thread-t2grsh (fix: backslash at end)
    "invocation_path_tail": "c7e078a8ea7daee005c6765702a5ec51fa061804a7c20b074d87c079d74da68f",
}
PRELUDE = """\
// Prelude: the UNIX build's definitions path.c uses (checked against upstream by
// build.py), and contracts for what it calls.
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "vp_path.h"
#define UNIX 1
#define NUL '\\000'
#define FUNC_ATTR_NONNULL_ALL
#define FUNC_ATTR_NONNULL_RET
#define FUNC_ATTR_PURE
#define FUNC_ATTR_NONNULL_ARG(...)
#define ASCII_ISLOWER(c) ((unsigned)(c) >= 'a' && (unsigned)(c) <= 'z')
#define ASCII_ISUPPER(c) ((unsigned)(c) >= 'A' && (unsigned)(c) <= 'Z')
#define ASCII_ISALPHA(c) (ASCII_ISUPPER(c) || ASCII_ISLOWER(c))
#define ASCII_ISALNUM(c) (ASCII_ISALPHA(c) || ascii_isdigit(c))
/*@ assigns \\nothing;
    ensures \\result == ('0' <= c && c <= '9' ? 1 : 0); */
static inline bool ascii_isdigit(int c)
{
  return c >= '0' && c <= '9';
}
#define MAXPATHL 4096   // os_defs.h: DEFAULT_MAXPATHL, Linux PATH_MAX is 4096 (not larger)
#define PATHSEP '/'
// ascii_defs.h has #define PATHSEPSTR "/"; tool patch: the same bytes as a compound
// literal (Frama-C 33 WP assumes string literals are zeros; ../equiv/literals.c checks)
#define PATHSEPSTR ((const char[]){'/', '\\0'})
/*@ requires c != 0 && str_len(str, n) && \\valid(str + (0 .. n));
    assigns str[0 .. n];
    ensures \\forall integer i; 0 <= i <= n ==> str[i] == (\\at(str[i], Pre) == c ? x : \\at(str[i], Pre)); */
void strchrsub(char *str, char c, char x) /*@ ghost (size_t n) */;
enum {
  URL_SLASH = 1,      // path_is_url() has found ":/"
  URL_BACKSLASH = 2,  // path_is_url() has found ":\\\\"
};
"""
CHECKS = [("src/nvim/ascii_defs.h", "#define NUL             '\\000'"),
          ("src/nvim/macros_defs.h", "#define ASCII_ISLOWER(c) ((unsigned)(c) >= 'a' && (unsigned)(c) <= 'z')"),
          ("src/nvim/macros_defs.h", "#define ASCII_ISUPPER(c) ((unsigned)(c) >= 'A' && (unsigned)(c) <= 'Z')"),
          ("src/nvim/macros_defs.h", "#define ASCII_ISALPHA(c) (ASCII_ISUPPER(c) || ASCII_ISLOWER(c))"),
          ("src/nvim/macros_defs.h", "#define ASCII_ISALNUM(c) (ASCII_ISALPHA(c) || ascii_isdigit(c))"),
          ("src/nvim/ascii_defs.h", "  return c >= '0' && c <= '9';"),
          ("src/nvim/ascii_defs.h", "#define PATHSEP        '/'"),
          ("src/nvim/ascii_defs.h", "#define PATHSEPSTR     \"/\""),
          ("src/nvim/os/os_defs.h", "#define DEFAULT_MAXPATHL 4096"),
          ("src/nvim/memory.c", "void strchrsub(char *str, char c, char x)"),
          (F, "  URL_SLASH = 1,      // path_is_url() has found \":/\""),
          (F, "  URL_BACKSLASH = 2,  // path_is_url() has found \":\\\\\"")]


def strip(s):
    s = re.sub(r"^[ \t]*/\*@.*?\*/\n", "", s, flags=re.S | re.M)
    s = re.sub(r" /\*@.*?\*/", "", s, flags=re.S)
    return s


def main(tree, out, mode="upstream"):
    fixed = mode == "fixed"
    for path, text in CHECKS:
        if text not in open(f"{tree}/{path}").read().split("\n"):
            sys.exit(f"build: {path} no longer contains: {text}")
    lines = open(f"{tree}/{F}").read().split("\n")
    A = annotations(fixed)
    protos = []
    for name in SHA:
        s, _ = find(lines, name)
        sig = lines[s]
        if name in GHOST:
            sig = f"{sig} /*@ ghost ({GHOST[name]}) */"
        protos.append(f"/*@ {C[name]} */\n{sig};")
    parts = [PRELUDE, LOGIC] + protos
    for name, want in SHA.items():
        s, e = find(lines, name)
        piece = "\n".join(lines[s:e + 1])
        h = hashlib.sha256(piece.encode()).hexdigest()
        if fixed and name in FIXED_SHA:
            want = FIXED_SHA[name]
        if h != want:
            sys.exit(f"build: {name} ({F}:{s + 1}) differs from the pinned {mode} text: sha256 {h}")
        code = piece
        for old, new in PATCHES.get(name, []):
            if code.count(old) != 1:
                sys.exit(f"build: {name}: tool patch anchor not found once: {old!r}")
            code = code.replace(old, new)
        mut = os.environ.get("VP_MUTANT")  # "function\x1fold\x1fnew", used by ../run_mutants.py only
        if mut and mut.split("\x1f")[0] == name:
            _, mo, mn = mut.split("\x1f")
            if code.count(mo) != 1:
                sys.exit(f"build: mutant anchor not found once in {name}: {mo!r}")
            code = piece = code.replace(mo, mn)
        annotated = code
        if name in GHOST:
            assert annotated.count(SIG[name] + "\n") == 1, name
            annotated = annotated.replace(SIG[name] + "\n", f"{SIG[name]} /*@ ghost ({GHOST[name]}) */\n")
        for kind, anchor, annot in A.get(name, []):
            if annotated.count(anchor) != 1:
                sys.exit(f"build: {name}: anchor not found once: {anchor!r}")
            if kind == "before":
                indent = re.match(r"\s*", anchor).group(0)
                annotated = annotated.replace(anchor, f"{indent}/*@ {annot} */\n{anchor}")
            elif kind == "after":
                annotated = annotated.replace(anchor, f"{anchor} /*@ {annot} */")
            else:
                sys.exit(f"build: bad annotation kind {kind}")
        if strip(annotated) != code:
            sys.exit(f"build: {name}: stripping the annotations does not give the source back")
        parts.append(f"// {F}:{s + 1} ({mode}, verbatim plus ACSL comments{', tool patch' if code != piece else ''})\n{annotated}\n")
    open(out, "w").write("\n".join(parts))


if __name__ == "__main__":
    main(*sys.argv[1:])
