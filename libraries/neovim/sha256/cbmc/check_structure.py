"""Check that sha256_process is exactly FIPS 180-4's compression, statement by statement.

Usage: python3 -I check_structure.py <neovim checkout>

CBMC proves the pieces (harness.c): the helper macros equal FIPS's functions (h_prims),
P is one round with renamed working variables (h_round), R(t) is the message schedule
(h_sched), GET_UINT32 is a big-endian load (h_endian). This script checks how they are put
together: after the #define lines, the body must be, in this order and nothing else:
  the declarations; GET_UINT32(W[t], data, 4t) for t = 0..15; A..H = ctx->state[0..7];
  64 calls P(names rotated right by t, W[t] or R(t), K[t]) with K[t] = FIPS's constant
  (read from spec.h); ctx->state[i] += A..H.
Rotating the names by one per round is exactly FIPS's "h = g; g = f; ...; a = T1 + T2".
"""
import re, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
NV = sys.argv[1]
raw = open(os.path.join(NV, "src/nvim/sha256.c")).read()


def clean(text):
    """C translation phases 2-3: join backslash-newlines first, then replace comments by a
    space (keeping their newlines), leaving string and character literals alone."""
    text = text.replace("\\\n", "")
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c in "\"'":
            j = i + 1
            while j < n and text[j] != c:
                j += 2 if text[j] == "\\" else 1
            out.append(text[i:j + 1]); i = j + 1
        elif text.startswith("//", i):
            j = text.find("\n", i); j = n if j < 0 else j
            out.append(" "); i = j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            if j < 0:
                sys.exit("check_structure: unterminated comment")
            out.append(" " + "\n" * text.count("\n", i, j)); i = j + 2
        else:
            out.append(c); i += 1
    return "".join(out)


def directives(text):
    return [ln.strip() for ln in text.split("\n") if ln.lstrip().startswith("#")]


src = clean(raw)

# Every preprocessor directive in the file. The macro harnesses (harness.c) include the same
# file and see each macro's last definition, so each must be defined exactly once, with no
# #undef and no conditional, for what they prove to be what the body uses.
BODY_MACROS = ["SHR", "ROTR", "S0", "S1", "S2", "S3", "F0", "F1", "R", "P"]
FILE_MACROS = ["GET_UINT32", "PUT_UINT32", "SHA_STEP"]
INCLUDES = ["<stdbool.h>", "<stddef.h>", "<stdio.h>", "<string.h>", '"nvim/ascii_defs.h"',
            '"nvim/memory.h"', '"nvim/sha256.h"', '"sha256.c.generated.h"']
defined, included = [], []
for d in directives(src):
    mm = re.fullmatch(r"#\s*define\s+([A-Za-z_]\w*).*", d, re.S)
    mi = re.fullmatch(r"#\s*include\s+(\S+)", d)
    if mm:
        defined.append(mm.group(1))
    elif mi:
        included.append(mi.group(1))
    else:
        sys.exit(f"check_structure: directive not allowed in sha256.c: {d!r}")
if sorted(defined) != sorted(BODY_MACROS + FILE_MACROS):
    sys.exit(f"check_structure: macros defined {sorted(defined)}, expected each of {sorted(BODY_MACROS + FILE_MACROS)} once")
if sorted(included) != sorted(INCLUDES):
    sys.exit(f"check_structure: includes {included}, expected {INCLUDES}")

m = re.search(r"\nstatic void sha256_process\(context_sha256_T \*ctx, const uint8_t data\[SHA256_BUFFER_SIZE\]\)\s*\{\n(.*?)\n\}\s*void sha256_update\(", src, re.S)
if not m:
    sys.exit("check_structure: sha256_process not found (or something between it and sha256_update)")
body = m.group(1)
in_body = [re.match(r"#\s*define\s+(\w+)", d).group(1) for d in directives(body)]
if sorted(in_body) != sorted(BODY_MACROS):
    sys.exit(f"check_structure: macros in the body {in_body}, expected {BODY_MACROS}")
body = "\n".join(ln for ln in body.split("\n") if not ln.lstrip().startswith("#"))

# The Neovim headers this file includes (transitively, those present in the checkout) must
# not define a macro named like anything the body or the macros use.
IDENTS = set(re.findall(r"[A-Za-z_]\w*", m.group(1))) - {"define"}
EXPECTED_HDR = {"SHA256_BUFFER_SIZE": "64"}   # the one header macro the body uses
found = set()
seen, todo, hdr_macros = set(), ["nvim/ascii_defs.h", "nvim/memory.h", "nvim/sha256.h"], {}
while todo:
    h = todo.pop()
    if h in seen:
        continue
    seen.add(h)
    path = os.path.join(NV, "src", h)
    if not os.path.exists(path):
        continue          # generated headers (*.generated.h): prototypes only
    for d in directives(clean(open(path).read())):
        mi = re.fullmatch(r'#\s*include\s+"([^"]+)"', d)
        if mi:
            todo.append(mi.group(1))
        mm = re.match(r"#\s*define\s+([A-Za-z_]\w*)(.*)", d)
        if mm and mm.group(1) in EXPECTED_HDR:
            if mm.group(2).strip() != EXPECTED_HDR[mm.group(1)]:
                sys.exit(f"check_structure: {h} defines {mm.group(1)} as {mm.group(2).strip()!r}")
            found.add(mm.group(1))
        elif mm:
            hdr_macros[mm.group(1)] = h
if found != set(EXPECTED_HDR):
    sys.exit(f"check_structure: {sorted(set(EXPECTED_HDR) - found)} not defined by the headers")
clash = sorted(IDENTS & set(hdr_macros))
if clash:
    sys.exit(f"check_structure: headers define macros used in sha256_process: {[(c, hdr_macros[c]) for c in clash]}")
stmts = [s.strip() for s in re.sub(r"\s+", "", body).replace("}", "};").split(";") if s.strip()]

K = [int(x, 16) for x in re.findall(r"0x[0-9a-f]{8}", re.search(r"SPEC_K\[64\] = \{(.*?)\};", open(os.path.join(HERE, "spec.h")).read(), re.S).group(1))]
assert len(K) == 64
names = "ABCDEFGH"
want = ["uint32_ttemp1,temp2,W[SHA256_BUFFER_SIZE]", "uint32_tA,B,C,D,E,F,G,H"]
want += [f"GET_UINT32(W[{t}],data,{4 * t})" for t in range(16)]
want += [f"{names[i]}=ctx->state[{i}]" for i in range(8)]
for t in range(64):
    rot = "".join(names[(i - t) % 8] for i in range(8))
    x = f"W[{t}]" if t < 16 else f"R({t})"
    want.append(("P", ",".join(rot) + "," + x, K[t]))
want += [f"ctx->state[{i}]+={names[i]}" for i in range(8)]

if len(stmts) != len(want):
    sys.exit(f"check_structure: {len(stmts)} statements, expected {len(want)}")
for i, (got, exp) in enumerate(zip(stmts, want)):
    if isinstance(exp, tuple):
        mm = re.fullmatch(r"P\((.*),(0x[0-9A-Fa-f]+)\)", got)
        ok = mm and mm.group(1) == exp[1] and int(mm.group(2), 16) == exp[2]
    else:
        ok = got == exp
    if not ok:
        sys.exit(f"check_structure: statement {i}: {got!r}, expected {exp!r}")
print(f"sha256_process structure: {len(stmts)} statements match FIPS 180-4 (64 rounds); "
      f"{len(defined)} macros each defined once, no other directives; {len(seen)} Neovim headers define none of the {len(IDENTS)} names used")
