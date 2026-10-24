"""Bit-level lemmas for base64.c, written once and used two ways.

WP states them over mathematical integers, where SMT solvers treat & | << >>
as uninterpreted. `python3 -I lemmas.py --check` proves each one with Z3
bit-vectors (128-bit, all values non-negative and far below 2^127, so the
bit-vector and integer meanings agree). `--acsl` prints them as ACSL.
The same expression strings feed both, so the two cannot drift apart.
"""
import sys

B = [f"b{i}" for i in range(8)]
G = lambda a, b, c: f"({a} * 65536 + {b} * 256 + {c})"
SEXTET = [  # k-th 6-bit chunk of a 24-bit group g
    lambda g: f"({g} / 262144)",
    lambda g: f"(({g} / 4096) % 64)",
    lambda g: f"(({g} / 64) % 64)",
    lambda g: f"({g} % 64)",
]
BE64 = " + ".join(f"b{j} * {2 ** (56 - 8 * j)}" for j in range(8))
BE32 = " + ".join(f"b{j} * {2 ** (24 - 8 * j)}" for j in range(4))

# Big-endian value of 8 or 4 bytes, as named logic functions. A lemma over a
# named function is matched by SMT triggers; one over a bare sum is not, because
# WP reorders the sum's terms differently in the goal and in the lemma.
BYTES_LOGIC = [
    ("bytes_be64", 8, " + ".join(f"b{j} * {2 ** (56 - 8 * j)}" for j in range(8))),
    ("bytes_be32", 4, " + ".join(f"b{j} * {2 ** (24 - 8 * j)}" for j in range(4))),
]
BBE64 = "bytes_be64(" + ", ".join(B) + ")"
BBE32 = "bytes_be32(" + ", ".join(B[:4]) + ")"

LEMMAS = []  # (name, byte vars, extra vars with bounds, hypothesis, lhs, rhs)
for m in range(8):  # 64-bit fast path: char m of the 8 written per step
    g = G(*B[3 * (m // 4): 3 * (m // 4) + 3])
    # Stated over the bytes only (no x == ... hypothesis) so every quantified
    # variable appears in the left side and SMT triggers can instantiate it.
    LEMMAS.append((f"fast64_{m}", B, [], "1",
                   f"(({BBE64} >> {58 - 6 * m}) & 63)", SEXTET[m % 4](g)))
for m in range(4):  # 32-bit path
    LEMMAS.append((f"fast32_{m}", B[:4], [], "1",
                   f"(({BBE32} >> {26 - 6 * m}) & 63)", SEXTET[m](G(*B[:3]))))
g3, g2, g1 = G("b0", "b1", "b2"), G("b0", "b1", "0"), G("b0", "0", "0")
LEMMAS += [  # tails, exactly as written in the C source
    ("tail_c0", B[:1], [], "1", "(b0 >> 2)", SEXTET[0](g1)),
    ("tail_c1", B[:2], [], "1", "(((b0 & 3) << 4) | (b1 >> 4))", SEXTET[1](g2)),
    # Stated over only the bytes that appear on the left, so SMT triggers can fire.
    ("tail_c2", ["b1", "b2"], [], "1", "(((b1 & 15) << 2) | (b2 >> 6))", "(((b1 * 256 + b2) / 64) % 64)"),
    ("tail_c3", ["b2"], [], "1", "(b2 & 63)", "(b2 % 64)"),
    ("tail2_c2", ["b1"], [], "1", "((b1 & 15) << 2)", "(((b1 * 256) / 64) % 64)"),
    ("tail1_c1", B[:1], [], "1", "((b0 & 3) << 4)", SEXTET[1](g1)),
]
# Arithmetic form of the four sextets of a group, and of the bit pieces the
# tail code uses. Stated separately so each SMT step is small.
LEMMAS += [
    ("grp_s0", B[:3], [], "1", SEXTET[0](g3), "(b0 / 4)"),
    ("grp_s1", B[:3], [], "1", SEXTET[1](g3), "((b0 % 4) * 16 + b1 / 16)"),
    ("grp_s2", B[:3], [], "1", SEXTET[2](g3), "((b1 % 16) * 4 + b2 / 64)"),
    ("grp_s3", B[:3], [], "1", SEXTET[3](g3), "(b2 % 64)"),
    ("byte_shr6", ["b0"], [], "1", "(b0 >> 6)", "(b0 / 64)"),
    ("or_shl4", [], ["x", "y"], "0 <= x <= 3 && 0 <= y <= 15", "((x << 4) | y)", "(x * 16 + y)"),
    ("or_shl2", [], ["x", "y"], "0 <= x <= 15 && 0 <= y <= 3", "((x << 2) | y)", "(x * 4 + y)"),
    ("shl4", [], ["x"], "0 <= x <= 3", "(x << 4)", "(x * 16)"),
    ("shl2", [], ["x"], "0 <= x <= 15", "(x << 2)", "(x * 4)"),
]
# The tool patches (tool_patches.py) assemble bits_be from bytes with << and |.
# Each shifted byte is cast back to the C type, exactly as WP reads the C code
# ((uint64_t)s[i] << 56 is to_uint64(lsl(s[i], 56))), so the lemma matches the goal.
OR64 = " | ".join(f"(uint64_t)(b{j} << {56 - 8 * j})" for j in range(7)) + " | b7"
OR32 = " | ".join(f"(uint32_t)(b{j} << {24 - 8 * j})" for j in range(3)) + " | b3"
LEMMAS += [
    ("or_bytes64", B, [], "1", f"({OR64})", f"({BE64})"),
    ("or_bytes32", B[:4], [], "1", f"({OR32})", f"({BE32})"),
]
# Facts the sextet spec needs about zero bytes past the end.
LEMMAS += [
    ("tail_c0_any", B[:3], [], "1", SEXTET[0](g1), SEXTET[0](g3)),
    ("tail_c1_any", B[:3], [], "1", SEXTET[1](g2), SEXTET[1](g3)),
]
# Decoder accumulator facts (acc is an int in 0..4095).
LEMMAS += [
    ("acc_shift", [], ["x"], "0 <= x <= 4095", "((x << 6) & 4095)", "((x % 64) * 64)"),
    ("acc_shl6", [], ["x"], "0 <= x <= 4095", "(x << 6)", "(x * 64)"),
    ("acc_shr0", [], ["x"], "0 <= x <= 4095", "(x >> 0)", "x"),
    ("acc_shr2", [], ["x"], "0 <= x <= 4095", "(x >> 2)", "(x / 4)"),
    ("acc_shr4", [], ["x"], "0 <= x <= 4095", "(x >> 4)", "(x / 16)"),
    ("acc_mask0", [], ["x"], "0 <= x <= 4095", "(x & 0)", "0"),
    ("acc_mask2", [], ["x"], "0 <= x <= 4095", "(x & 3)", "(x % 4)"),
    ("acc_mask4", [], ["x"], "0 <= x <= 4095", "(x & 15)", "(x % 16)"),
    ("pow_0", [], [], "1", "(1 << 0)", "1"),
    ("pow_2", [], [], "1", "(1 << 2)", "4"),
    ("pow_4", [], [], "1", "(1 << 4)", "16"),
    # dest[out_i] = (char)(acc >> acc_len), read back as uint8_t.
    ("cast_u8s8", [], ["x"], "0 <= x <= 4095", "(uint8_t)(char)(x)", "(x % 256)"),
]
RANGE_LEMMAS = [
    ("shr_range", ["x", "k"], "0 <= x <= 4095 && 0 <= k <= 6", "0 <= (x >> k) <= x"),
]


def part_of(name):
    """Which proof uses a lemma: 'dec' (decoder), 'enc' (encoder) or 'both'."""
    if name in ("shr_range", "acc_shr2", "acc_shr4", "acc_mask2", "acc_mask4"):
        return "both"   # byte-level shift/mask facts the encoder tail also uses
    if name.startswith(("acc_", "pow_", "cast_")):
        return "dec"
    return "enc"


def acsl(part="all"):
    keep = lambda n: part == "all" or part_of(n) in (part, "both")
    out = ["/*@ // Generated by lemmas.py; each lemma is checked there with Z3 bit-vectors."]
    for name, n, body in BYTES_LOGIC:
        out.append(f"    logic integer {name}({', '.join('integer ' + b for b in B[:n])}) = {body};")
    for name, bs, xs, hyp, lhs, rhs in [l for l in LEMMAS if keep(l[0])]:
        vs = bs + xs
        rng = " && ".join([f"0 <= {b} <= 255" for b in bs] + ([hyp] if hyp != "1" else []))
        q = f"\\forall integer {', '.join(vs)}; " if vs else ""
        body = f"{rng} ==> {lhs} == {rhs}" if rng else f"{lhs} == {rhs}"
        out.append(f"    lemma {name}: {q}{body};")
    for name, vs, hyp, concl in [l for l in RANGE_LEMMAS if keep(l[0])]:
        out.append(f"    lemma {name}: \\forall integer {', '.join(vs)}; {hyp} ==> {concl};")
    out.append("*/")
    return "\n".join(out)


def check():
    from z3 import BitVec, BitVecVal, ULE, And, Implies, Not, Solver, unsat
    W = 128
    ok = True

    def env(names):
        return {n: BitVec(n, W) for n in names}

    import re as _re
    from z3 import If
    M = lambda bits: (lambda v: v & BitVecVal(2 ** bits - 1, W))
    def S8(v):  # (char)v on x86_64: signed 8-bit, two's complement
        lo = v & BitVecVal(255, W)
        return If(lo >= 128, lo - 256, lo)
    CASTS = {"U64": M(64), "U32": M(32), "U8": M(8), "S8": S8}
    for _name, _n, _body in BYTES_LOGIC:   # same body text as the ACSL definition
        CASTS[_name] = eval("lambda " + ", ".join(B[:_n]) + ": " + _body)

    def py(expr):
        # ACSL casts to function calls: (uint64_t)(e) -> U64(e), (char)(e) -> S8(e)
        # innermost cast first, so (uint8_t)(char)(e) becomes U8(S8(e))
        for c, f in (("char", "S8"), ("uint64_t", "U64"), ("uint32_t", "U32"), ("uint8_t", "U8")):
            expr = _re.sub(r"\(" + c + r"\)\s*([A-Z]\w*\([^()]*\))", f + r"(\1)", expr)
            expr = _re.sub(r"\(" + c + r"\)\s*\(", f + "(", expr)
        return expr

    def ev(expr, e):
        # ACSL and Python share these operators; chained comparisons are split.
        return eval(expr.replace("&&", " and_ ").replace("==>", " imp "), {}, e)

    def conj(parts, e):
        return And(*[cmp(p, e) for p in parts]) if parts else BitVecVal(1, W) == 1

    def cmp(p, e):
        # handle a <= x <= b and a < x
        import re
        toks = re.split(r"(<=|(?<!<)<(?![<=])|==)", p)
        exprs = [eval(t, {}, e) if not isinstance(t, int) else t for t in toks[0::2]]
        ops = toks[1::2]
        cs = []
        for a, op, b in zip(exprs, ops, exprs[1:]):
            a = a if not isinstance(a, int) else BitVecVal(a, W)
            b = b if not isinstance(b, int) else BitVecVal(b, W)
            cs.append({"<=": a <= b, "<": a < b, "==": a == b}[op])
        return And(*cs)

    for name, bs, xs, hyp, lhs, rhs in LEMMAS:
        e = env(bs + xs)
        pre = [f"0 <= {b} <= 255" for b in bs] + ([] if hyp == "1" else hyp.split("&&"))
        pre = [p for p in pre]
        nonneg = [e[v] >= 0 for v in xs] + [e[v] < BitVecVal(2 ** 100, W) for v in xs]
        f = Implies(And(conj(pre, e), *nonneg),
                    eval(py(lhs), dict(CASTS), e) == eval(py(rhs), dict(CASTS), e))
        s = Solver(); s.add(Not(f)); r = s.check()
        print(f"{name}: {'PROVED' if r == unsat else 'FAILED'}"); ok &= r == unsat
    for name, vs, hyp, concl in RANGE_LEMMAS:
        e = env(vs)
        nonneg = [e[v] >= 0 for v in vs]
        f = Implies(And(conj(hyp.split("&&"), e), *nonneg), conj(concl.split("&&"), e))
        s = Solver(); s.add(Not(f)); r = s.check()
        print(f"{name}: {'PROVED' if r == unsat else 'FAILED'}"); ok &= r == unsat
    return ok


if __name__ == "__main__":
    if "--acsl" in sys.argv:
        i = sys.argv.index("--acsl")
        print(acsl(sys.argv[i + 1] if len(sys.argv) > i + 1 else "all"))
    else:
        sys.exit(0 if check() else 1)
