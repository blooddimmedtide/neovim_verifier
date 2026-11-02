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
src = open(os.path.join(sys.argv[1], "src/nvim/sha256.c")).read()
m = re.search(r"\nstatic void sha256_process\(context_sha256_T \*ctx, const uint8_t data\[SHA256_BUFFER_SIZE\]\)\n\{\n(.*?)\n\}\n\nvoid sha256_update\(", src, re.S)
if not m:
    sys.exit("check_structure: sha256_process not found")
body = m.group(1)
body = re.sub(r"^#define(?:[^\n]*\\\n)*[^\n]*\n", "", body, flags=re.M)   # drop macro definitions
body = re.sub(r"//[^\n]*", "", body)
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
print(f"sha256_process structure: {len(stmts)} statements match FIPS 180-4 (64 rounds)")
