"""Annotated standalone copy of keycodes.c pieces for Frama-C WP.

Usage: python3 -I build.py <neovim checkout> <out.c> [--pin]
Each function and each static table is the exact upstream text (sha256 pinned).
The prelude repeats the macros the pieces use; every one is checked to exist
verbatim in the pinned headers. ACSL goes in comments only (contracts.py), so
removing every /*@ ... */ gives back the upstream text.
"""
import hashlib, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "tools"))
from extract_c import find
from contracts import LOGIC, CONTRACTS, STUBS

F = "src/nvim/keycodes.c"
# upstream 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
SHA = {
    "name_to_mod_mask": "137e59a61a4f028a8a1fc39bd1a540df330587639ac0eee5b23ea50ba12599fe",
    "simplify_key": "d9615c213ed6ddbf94d93d28f88fcae6f0cb5b1fbc8512efc488a6e2618c2ed8",
    "unsimplify_key": "ce4003f87f83a3c261c926ec86c32ad76eec881b8d478811144c79c4430d70bd",
    "handle_x_keys": "e94c97bf377277c1b851cf6ed3044bcc0afa5a5f177f3bf1bcf3edfdc736af12",
    "extract_modifiers": "6955f1261b06222b6eecdcd860334935e818dc57fcdd41d7cdd148f6da9985db",
    "get_mouse_button": "4febfd94433064504e4136ba9ac682ec15153c223a057686600a8f2f10a9834c",
    # "add_char2buf": "",
    # "special_to_buf": "",
    "vim_unescape_ks": "31aa926b8cd3871e2a64eb7daa129f6e34cadeb907468dd2be837256376d56e6",
}
TABLES = {  # first line, sha256 of the block up to the closing "};"
    "const struct modmasktable mod_mask_table[] = {": "91d82025970e06832e74d7035b48a17b8ebb46b1e36d166019abb3144c259dd5",
    "static uint8_t modifier_keys_table[] = {": "a6f3a2415447f9150ebbc7b188b4e76deb1c75c1484cb84c696843c6fc7dec13",
    "static struct mousetable {": "8657c62466dc41da66f7283ea14f0bc254ef14731d28883744e0a30c6572b105",
}
H = "src/nvim/keycodes.h"
CHECKS = [
    ("src/nvim/keycodes.h", "#define K_SPECIAL               (0x80)"),
    ("src/nvim/keycodes.h", "#define IS_SPECIAL(c)           ((c) < 0)"),
    ("src/nvim/keycodes.h", "#define KS_SPECIAL              254"),
    ("src/nvim/keycodes.h", "#define KS_EXTRA                253"),
    ("src/nvim/keycodes.h", "#define KS_MODIFIER             252"),
    ("src/nvim/keycodes.h", "#define KS_ZERO                 255"),
    ("src/nvim/keycodes.h", "#define KE_FILLER               ('X')"),
    ("src/nvim/keycodes.h", "#define TERMCAP2KEY(a, b)       (-((a) + ((int)(b) << 8)))"),
    ("src/nvim/keycodes.h", "#define KEY2TERMCAP0(x)         ((-(x)) & 0xff)"),
    ("src/nvim/keycodes.h", "#define KEY2TERMCAP1(x)         (((unsigned)(-(x)) >> 8) & 0xff)"),
    ("src/nvim/keycodes.h", "#define MOD_MASK_SHIFT      0x02"),
    ("src/nvim/keycodes.h", "#define MOD_MASK_CTRL       0x04"),
    ("src/nvim/keycodes.h", "#define MOD_MASK_ALT        0x08        // aka META"),
    ("src/nvim/keycodes.h", "#define MOD_MASK_META       0x10        // META when it's different from ALT"),
    ("src/nvim/keycodes.h", "#define MOD_MASK_2CLICK     0x20        // use MOD_MASK_MULTI_CLICK"),
    ("src/nvim/keycodes.h", "#define MOD_MASK_3CLICK     0x40        // use MOD_MASK_MULTI_CLICK"),
    ("src/nvim/keycodes.h", "#define MOD_MASK_4CLICK     0x60        // use MOD_MASK_MULTI_CLICK"),
    ("src/nvim/keycodes.h", "#define MOD_MASK_CMD        0x80        // \"super\" key (macOS: command-key)"),
    ("src/nvim/keycodes.h", "#define MOD_MASK_MULTI_CLICK    (MOD_MASK_2CLICK|MOD_MASK_3CLICK| \\"),
    ("src/nvim/keycodes.h", "                                 MOD_MASK_4CLICK)"),
    ("src/nvim/keycodes.h", "#define K_S_TAB         TERMCAP2KEY('k', 'B')"),
    ("src/nvim/keycodes.h", "#define K_ZERO          TERMCAP2KEY(KS_ZERO, KE_FILLER)"),
    ("src/nvim/ascii_defs.h", "#define NUL             '\\000'"),
    ("src/nvim/ascii_defs.h", "#define TAB             '\\011'"),
    ("src/nvim/ascii_defs.h", "#define CTRL_CHR(x)     (TOUPPER_ASC(x) ^ 0x40)  // '?' -> DEL, '@' -> ^@, etc."),
    ("src/nvim/macros_defs.h", "#define TOUPPER_ASC(c) (((c) < 'a' || (c) > 'z') ? (c) : (c) - ('a' - 'A'))"),
    ("src/nvim/macros_defs.h", "#define ASCII_ISLOWER(c) ((unsigned)(c) >= 'a' && (unsigned)(c) <= 'z')"),
    ("src/nvim/macros_defs.h", "#define ASCII_ISUPPER(c) ((unsigned)(c) >= 'A' && (unsigned)(c) <= 'Z')"),
    ("src/nvim/macros_defs.h", "#define ASCII_ISALPHA(c) (ASCII_ISUPPER(c) || ASCII_ISLOWER(c))"),
    ("src/nvim/keycodes.h", "  uint16_t mod_mask;  ///< Bit-mask for particular key modifier."),
    ("src/nvim/keycodes.h", "  uint16_t mod_flag;  ///< Bit(s) for particular key modifier."),
    ("src/nvim/keycodes.h", "  char name;  ///< Single letter name of modifier."),
]


def prelude(tree):
    kh = open(f"{tree}/{H}").read().split("\n")
    # enum key_extra is copied whole from the header (pinned with the other text).
    s = kh.index("enum key_extra {")
    e = s
    while kh[e] != "};":
        e += 1
    enum = "\n".join(kh[s:e + 1])
    # K_* key macros used by handle_x_keys / simplify_key / the tables: copied by name.
    names = ["K_UP", "K_DOWN", "K_LEFT", "K_RIGHT", "K_HOME", "K_END", "K_XUP", "K_XDOWN",
             "K_XLEFT", "K_XRIGHT", "K_XHOME", "K_ZHOME", "K_XEND", "K_ZEND", "K_XF1", "K_XF2",
             "K_XF3", "K_XF4", "K_F1", "K_F2", "K_F3", "K_F4", "K_S_XF1", "K_S_XF2", "K_S_XF3",
             "K_S_XF4", "K_S_F1", "K_S_F2", "K_S_F3", "K_S_F4"]
    kdefs = []
    for n in names:
        hits = [l for l in kh if l.startswith(f"#define {n} ") or l.startswith(f"#define {n}\t")]
        if len(hits) < 1:
            sys.exit(f"build: {n} not in keycodes.h")
        kdefs.append(hits[0])
    mouse = open(f"{tree}/src/nvim/mouse.h").read().split("\n")
    menum = []
    for n in ["MOUSE_LEFT", "MOUSE_MIDDLE", "MOUSE_RIGHT", "MOUSE_RELEASE", "MOUSE_X1", "MOUSE_X2"]:
        hits = [l for l in mouse if l.strip().startswith(n + " ")]
        if len(hits) != 1:
            sys.exit(f"build: {n} not unique in mouse.h")
        menum.append(hits[0].split("///")[0])
    checked = "\n".join(t for _, t in CHECKS if not t.startswith("  u") and not t.startswith("  c"))
    return f"""\
// Prelude: types and macros keycodes.c uses, as Neovim defines them (each line
// checked against the pinned headers by build.py), and contracts of callees.
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <limits.h>
#include <assert.h>
{checked}
{enum}
{chr(10).join(kdefs)}
enum {{
{chr(10).join(menum)}
}};
const struct modmasktable {{
  uint16_t mod_mask;  ///< Bit-mask for particular key modifier.
  uint16_t mod_flag;  ///< Bit(s) for particular key modifier.
  char name;  ///< Single letter name of modifier.
}};
#define MOD_KEYS_ENTRY_SIZE 5
#define FUNC_ATTR_CONST
#define FUNC_ATTR_WARN_UNUSED_RESULT
#define FUNC_ATTR_NONNULL_ALL
#define MB_MAXBYTES 30
{STUBS}
"""


def block(lines, first):
    s = lines.index(first)
    e = s
    while lines[e] != "};":
        e += 1
    return "\n".join(lines[s:e + 1])


def main():
    tree, out = sys.argv[1], sys.argv[2]
    pin = "--pin" in sys.argv
    for path, text in CHECKS:
        if text not in open(f"{tree}/{path}").read().split("\n"):
            sys.exit(f"build: {path} no longer contains: {text}")
    lines = open(f"{tree}/{F}").read().split("\n")
    parts, plain = [prelude(tree)], []
    for first, want in TABLES.items():
        b = block(lines, first)
        h = hashlib.sha256(b.encode()).hexdigest()
        if pin:
            print(f"    {first!r}: {h!r},")
        elif h != want:
            sys.exit(f"build: table {first} changed: {h}")
        parts.append(b)
        plain.append(b)
    parts.append(LOGIC)
    for name, want in SHA.items():
        s, e = find(lines, name)
        piece = "\n".join(lines[s:e + 1])
        h = hashlib.sha256(piece.encode()).hexdigest()
        if pin:
            print(f"    {name!r}: {h!r},")
        elif h != want:
            sys.exit(f"build: {name} changed upstream: {h}")
        c = CONTRACTS.get(name, "")
        ann = CONTRACTS.get(name + ".body", {})
        body = piece
        for anchor, text in ann.items():
            if body.count(anchor) != 1:
                sys.exit(f"build: anchor not unique in {name}: {anchor}")
            body = body.replace(anchor, text + anchor)
        plain_body = re.sub(r" /\*@ ghost [^*]*\*/", "", body)
        plain_body = re.sub(r"[ \t]*/\*@.*?\*/\n", "", plain_body, flags=re.S)
        if plain_body != piece:
            sys.exit(f"build: annotations of {name} change the code")
        parts.append(c + body)
    src = "\n\n".join(parts) + "\n"
    open(out, "w").write(src)


if __name__ == "__main__":
    main()
