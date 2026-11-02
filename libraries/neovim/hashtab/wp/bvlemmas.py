"""Integer lemmas about 64-bit arithmetic for hashtab.c, written once and used two ways.

WP states them over mathematical integers, where SMT solvers treat & >> << as
uninterpreted and arithmetic modulo 2^64 as nonlinear. `python3 -I bvlemmas.py` proves
each one with Z3 on 256-bit bit-vectors; `--acsl` prints them as ACSL lemmas.

Why the two readings agree. Every variable is an integer in [0, 2^64) (or a smaller
range given in `bounds`); the ACSL hypothesis states these ranges. The checker computes
an upper bound on the magnitude of every subterm from those ranges and refuses a lemma
where any bound reaches 2^250. Below that, 256-bit two's complement arithmetic is exact
integer arithmetic: + - * << are exact, >> is the arithmetic shift (ACSL's >> on
integers rounds down), & is ACSL's two's complement &, comparisons are signed, and the
cast (size_t)e (e modulo 2^64) is e & (2^64 - 1). Shift amounts must have a bound
below 190. So each ACSL lemma holds for all integers in range iff Z3 proves it.
"""
import sys

W = 256
M64 = 2 ** 64 - 1


class E:
    def __add__(s, o): return Op("+", s, lift(o))
    def __radd__(s, o): return Op("+", lift(o), s)
    def __sub__(s, o): return Op("-", s, lift(o))
    def __mul__(s, o): return Op("*", s, lift(o))
    def __rmul__(s, o): return Op("*", lift(o), s)
    def __lshift__(s, o): return Op("<<", s, lift(o))
    def __and__(s, o): return Op("&", s, lift(o))
    def __rshift__(s, o): return Op(">>", s, lift(o))
    def __floordiv__(s, o): return Op("/", s, lift(o))   # ACSL / (truncating), divisor > 0 here


def lift(x):
    return Const(x) if isinstance(x, int) else x


class Var(E):
    def __init__(s, n): s.n = n
    def acsl(s): return s.n
    def z3(s, env): return env[s.n]
    def ub(s, bnd): return bnd.get(s.n, M64)


class Const(E):
    def __init__(s, v):
        assert 0 <= v <= M64
        s.v = v
    def acsl(s): return str(s.v)
    def z3(s, env):
        import z3
        return z3.BitVecVal(s.v, W)
    def ub(s, bnd): return s.v


class Op(E):
    def __init__(s, op, a, b): s.op, s.a, s.b = op, a, b
    def acsl(s): return f"({s.a.acsl()} {s.op} {s.b.acsl()})"
    def z3(s, env):
        a, b = s.a.z3(env), s.b.z3(env)
        return {"+": lambda: a + b, "-": lambda: a - b, "*": lambda: a * b, "<<": lambda: a << b,
                "&": lambda: a & b, ">>": lambda: a >> b, "/": lambda: a / b}[s.op]()
    def ub(s, bnd):
        x, y = s.a.ub(bnd), s.b.ub(bnd)
        if s.op in "+-":
            return x + y
        if s.op == "*":
            return x * y
        if s.op in ("<<", ">>"):
            if y >= 190:
                raise ValueError(f"shift amount {s.b.acsl()} not bounded below 190")
            return x << y if s.op == "<<" else x
        if s.op == "/":
            assert isinstance(s.b, Const) and s.b.v > 0, "division only by a positive constant"
            return x
        return max(x, y)  # &: |a & b| <= max(|a|, |b|) in two's complement


class Cast(E):
    def __init__(s, a): s.a = a
    def acsl(s): return f"(size_t){s.a.acsl()}"
    def z3(s, env):
        import z3
        return z3.ZeroExt(W - 64, mod64(s.a, env))
    def ub(s, bnd):
        s.a.ub(bnd)
        return M64


def sz(e): return Cast(lift(e))


def mod64(e, env):
    """e modulo 2^64 as a 64-bit term: + - * << commute with reduction modulo 2^64, so a
    ring operation is done in 64 bits; any other subterm is computed exactly, then
    reduced (Extract of the low 64 bits is the reduction of a two's complement value)."""
    import z3
    if isinstance(e, Op) and e.op in ("+", "-", "*", "<<"):
        x = mod64(e.a, env)
        y = mod64(e.b, env) if e.op != "<<" else z3.Extract(63, 0, e.b.z3(env))
        if e.op == "<<":
            return z3.If(z3.ULT(e.b.z3(env), 64), x << y, z3.BitVecVal(0, 64))
        return {"+": x + y, "-": x - y, "*": x * y}[e.op]
    return z3.Extract(63, 0, e.z3(env))


class P:  # propositions
    def __init__(s, op, *xs):
        if op in ("==", "!=", "<=", "<"):
            xs = tuple(lift(x) for x in xs)
        s.op, s.xs = op, xs
    def acsl(s):
        if s.op in ("==", "!=", "<=", "<"):
            return f"{s.xs[0].acsl()} {s.op} {s.xs[1].acsl()}"
        if s.op == "!":
            return f"!({s.xs[0].acsl()})"
        j = {"&&": " && ", "||": " || ", "==>": " ==> "}[s.op]
        return "(" + j.join(x.acsl() for x in s.xs) + ")"
    def z3(s, env):
        import z3
        if s.op in ("==", "!=", "<=", "<"):
            a, b = (x.z3(env) for x in s.xs)
            return {"==": a == b, "!=": a != b, "<=": a <= b, "<": a < b}[s.op]
        xs = [x.z3(env) for x in s.xs]
        return {"!": lambda: z3.Not(xs[0]), "&&": lambda: z3.And(*xs), "||": lambda: z3.Or(*xs),
                "==>": lambda: z3.Implies(xs[0], xs[1])}[s.op]()
    def ub(s, bnd):
        return max([0] + [x.ub(bnd) for x in s.xs])


def poly(e):
    """e as a polynomial over the integers (dict: sorted tuple of atoms -> coefficient),
    read modulo 2^64: a cast is dropped (e mod 2^64 is congruent to e), + - * and << by a
    constant are expanded, anything else (& >> or a shift by a variable) is an opaque atom."""
    def mul(f, g):
        out = {}
        for m1, c1 in f.items():
            for m2, c2 in g.items():
                m = tuple(sorted(m1 + m2))
                out[m] = out.get(m, 0) + c1 * c2
        return out
    def add(f, g, k=1):
        out = dict(f)
        for m, c in g.items():
            out[m] = out.get(m, 0) + k * c
        return out
    if isinstance(e, Var):
        return {(e.n,): 1}
    if isinstance(e, Const):
        return {(): e.v}
    if isinstance(e, Cast):
        return poly(e.a)
    if isinstance(e, Op) and e.op in "+-*":
        f, g = poly(e.a), poly(e.b)
        return add(f, g) if e.op == "+" else add(f, g, -1) if e.op == "-" else mul(f, g)
    if isinstance(e, Op) and e.op == "<<" and isinstance(e.b, Const):
        return mul(poly(e.a), {(): 2 ** e.b.v})
    return {(e.acsl(),): 1}


def ring_ok(hyps, concl, certs):
    """concl (an equation between values in [0, 2^64)) follows from the equations hyps,
    modulo 2^64, with the given multipliers: lhs - rhs - sum(q_i * (l_i - r_i)) has every
    coefficient divisible by 2^64. In range, congruence modulo 2^64 is equality."""
    def in_range(e):
        return isinstance(e, (Cast, Var, Const))
    assert concl.op == "==" and all(map(in_range, concl.xs)), "conclusion must equate two size_t values"
    d = poly(concl.xs[0] - concl.xs[1])
    for h, q in zip(hyps, certs):
        assert h.op == "==" and all(map(in_range, h.xs))
        for m, c in poly(lift(q) * (h.xs[0] - h.xs[1])).items():
            d[m] = d.get(m, 0) - c
    return all(c % 2 ** 64 == 0 for c in d.values())


eq = lambda a, b: P("==", a, b)
ne = lambda a, b: P("!=", a, b)
le = lambda a, b: P("<=", a, b)
lt = lambda a, b: P("<", a, b)
conj = lambda *xs: P("&&", *xs)
imp = lambda a, b: P("==>", a, b)

a, b, x, t, A, d, u, v, mask, y, p, s = (Var(n) for n in "a b x t A d u v mask y p s".split())
# C arithmetic on size_t: every operation wraps, so it is written with a cast per operation,
# the way WP reads the ghost code.
cadd = lambda e, f: sz(e + f)
csub = lambda e, f: sz(e - f)
cmul = lambda e, f: sz(e * f)
INV5 = 0xCCCCCCCCCCCCCCCD                  # 5 * INV5 == 1 modulo 2^64
POW2 = lambda e: conj(le(1, e), eq(e & (e - 1), 0))       # e is a power of two
# mask + 1 is a power of two. Written with a "mask == 15 ||" case (true anyway) so that a
# table of the initial size needs no & evaluation: SMT solvers cannot compute 15 & 16.
TMASK = P("||", eq(mask, 15), eq(mask & (mask + 1), 0))
LOW = lambda e: csub(cmul(2, e), 1)        # 2p - 1, as the C code computes it
# A == 1 + 4p modulo 8p: the property of 5^p that makes p more steps fix one more bit
QA = lambda pp, AA=A: eq(csub(AA, 1) & csub(cmul(8, pp), 1), cmul(4, pp))
FA = lambda bb: cadd(cmul(4, bb), 1)        # the multiplier a = 4b + 1 (mod 2^64), kept implicit
VAL = lambda bb: cadd(cmul(FA(bb), x), bb)  # the slot value a*x + b
B2 = cadd(cmul(A, b), csub(A, 1) >> 2)     # b after composing with p more steps
BP = csub(b, cmul(FA(b), INV5))            # b after taking off one step 5*x + 1 at the front
P2 = 2 ** 59

LEMMAS = [  # (name, variables, {var: upper bound}, hypothesis, conclusion)
    # one bit of the step count: add p steps when bit p of a*x+b differs from t's.
    # Split in four so each Z3 query is small. B = (A - 1) >> 2 is exact: A == 1 mod 4.
    ("bv_step_quarter", "A p", {"p": P2}, conj(POW2(p), QA(p)), eq(cmul(4, csub(A, 1) >> 2), csub(A, 1))),
    ("bv_step_mult", "b A", {}, eq(cmul(4, csub(A, 1) >> 2), csub(A, 1)), eq(FA(B2), cmul(A, FA(b)))),
    ("bv_step_bit", "u t A p", {"p": P2},
     conj(POW2(p), QA(p), eq(u & csub(p, 1), t & csub(p, 1)), ne(u & LOW(p), t & LOW(p))),
     eq(cadd(cmul(A, u), csub(A, 1) >> 2) & LOW(p), t & LOW(p))),
    # squaring keeps A of the form 1 + 4p (mod 8p) one level up
    ("bv_square", "A p", {"p": P2}, conj(POW2(p), QA(p)), QA(cmul(2, p), cmul(A, A))),
    ("bv_pow2_double", "p", {"p": 2 ** 60}, POW2(p), conj(POW2(cmul(2, p)), eq(cmul(2, p), 2 * p))),
    ("bv_pow2_bound", "p", {}, conj(POW2(p), le(p, 2 ** 60 - 1)), le(p, P2)),
    ("bv_pow2_le", "p mask", {"p": 2 ** 60}, conj(POW2(p), TMASK, le(p, mask)), le(2 * p, mask + 1)),
    ("bv_base", "", {}, conj(), QA(Const(1), Const(5))),
    # take one step 5*x + 1 off the front
    ("bv_peel", "b x", {}, conj(),
     conj(eq(cadd(cmul(FA(BP), cadd(cmul(5, x), 1)), BP), VAL(b)), eq(FA(BP), cmul(FA(b), INV5)))),
    ("bv_unfive", "u", {}, conj(), eq(cmul(cmul(5, u), INV5), u)),
    # zero steps: a == 1 gives the slot of x itself
    ("bv_zero", "b x mask", {"mask": 2 ** 60 - 1}, conj(TMASK, eq(FA(b), 1)), eq(VAL(b) & mask, x & mask)),
    # all bits below the table size are right: the slot is t
    ("bv_done", "b x t p mask", {"p": 2 ** 61},
     conj(TMASK, POW2(p), lt(mask, p), le(t, mask), eq(VAL(b) & csub(p, 1), t & csub(p, 1))),
     eq(VAL(b) & mask, t)),
    # 5^(m+n) = 5^m * 5^n, one step of the induction
    ("bv_assoc5", "u v", {}, conj(), eq(cmul(5, cmul(u, v)), cmul(u, cmul(5, v)))),
    # the slot depends only on the low bits: (5*i + p + 1) & m from i or from i & m
    ("bv_slot", "y d mask", {}, TMASK,
     eq(cadd(cadd(cmul(5, y & mask), d), 1) & mask, cadd(cadd(cmul(5, y), d), 1) & mask)),
    ("bv_mask_le", "y mask", {}, conj(), conj(le(0, y & mask), le(y & mask, mask))),
    # a shift by a variable 5 equals the shift by the constant (WP writes them differently)
    ("bv_lsr5", "p s", {"s": 5}, eq(s, 5), eq(p >> s, p // 32)),
    ("bv_mask_idem", "y mask", {}, conj(), eq((y & mask) & mask, y & mask)),
    # perturb = hash >> 5n shrinks to 0 within 13 steps
    ("bv_shr_mono", "p y s", {"s": 64}, le(p, y >> s), le(p >> 5, y >> (s + 5))),
    ("bv_shr_zero", "y s", {"s": 70}, le(64, s), eq(y >> s, 0)),
]


# Ring identities modulo 2^64, checked by expanding polynomials with explicit multipliers
# for the hypotheses (a certificate), not by Z3: (name, variables, hypotheses, conclusion,
# multipliers). Variables range over [0, 2^64) as above.
RING = [
    ("bv_step_val", "b x A", [eq(cmul(4, csub(A, 1) >> 2), csub(A, 1))],
     eq(VAL(B2), cadd(cmul(A, VAL(b)), csub(A, 1) >> 2)), [x]),
]


def acsl(only=None):
    """The lemmas as ACSL lemmas (all, or the names in `only`), for uses on logic terms
    where a lemma function cannot be called."""
    out = ["/*@ // Generated by bvlemmas.py; each lemma is checked there with Z3."]
    for name, vs, bnd, hyp, concl in LEMMAS:
        if only is not None and name not in only:
            continue
        vs = vs.split()
        rng = [f"0 <= {n} <= {bnd.get(n, M64)}" for n in vs]
        h = " && ".join(rng + ([hyp.acsl()] if hyp.xs else []))
        q = f"\\forall integer {', '.join(vs)}; " if vs else ""
        out.append(f"    lemma {name}: {q}{h + ' ==> ' if h else ''}{concl.acsl()};")
    for name, vs, hyps, concl, _ in RING:
        if only is not None and name not in only:
            continue
        vs = vs.split()
        h = " && ".join([f"0 <= {n} <= {M64}" for n in vs] + [x.acsl() for x in hyps])
        out.append(f"    lemma {name}: \\forall integer {', '.join(vs)}; {h} ==> {concl.acsl()};")
    return "\n".join(out) + "\n*/\n"


def ghost():
    """The same statements as ghost functions with a contract and no body ("lemma
    functions"): `ensures hypothesis ==> conclusion` for the arguments given. A call
    instantiates the statement with the actual arguments, so the provers need no quantifier
    instantiation. The contract is trusted by WP and justified only by check() here, like
    the lemmas of acsl(). Arguments are size_t, so each is in [0, 2^64)."""
    out = ["/*@ ghost // Generated by bvlemmas.py; each statement is checked there."]
    rows = [(n, vs, bnd, [hyp] if hyp.xs else [], concl) for n, vs, bnd, hyp, concl in LEMMAS]
    rows += [(n, vs, {}, hyps, concl) for n, vs, hyps, concl, _ in RING]
    for name, vs, bnd, hyps, concl in rows:
        vs = vs.split()
        h = [f"{n} <= {bnd[n]}" for n in vs if n in bnd] + [x.acsl() for x in hyps]
        ens = f"({' && '.join(h)}) ==> {concl.acsl()}" if h else concl.acsl()
        args = ", ".join(f"size_t {n}" for n in vs) or "void"
        out.append(f"  /@ assigns \\nothing;\n     ensures {ens}; @/\n  void {name}({args});")
    return "\n".join(out) + "\n*/\n"


def check():
    import z3
    bad = 0
    for name, vs, bnd, hyp, concl in LEMMAS:
        try:
            m = max(hyp.ub(bnd), concl.ub(bnd))
            assert m < 2 ** 250, f"magnitude bound 2^{m.bit_length()} too large"
        except (ValueError, AssertionError) as e:
            print(f"{name}: REFUSED ({e})")
            bad += 1
            continue
        env, rng = {}, []
        for n in vs.split():
            env[n] = z3.ZeroExt(W - 64, z3.BitVec(n, 64))
            rng.append(env[n] <= bnd.get(n, M64))
        s = z3.Solver()
        s.set("timeout", 600000)
        f = z3.Implies(z3.And(*rng, hyp.z3(env)) if hyp.xs else z3.And(*rng), concl.z3(env))
        s.add(z3.Not(f))
        r = s.check()
        ok = r == z3.unsat
        bad += not ok
        print(f"{name}: {'PROVED' if ok else r}", flush=True)
    for name, vs, hyps, concl, certs in RING:
        ok = ring_ok(hyps, concl, certs)
        bad += not ok
        print(f"{name}: {'PROVED (ring identity)' if ok else 'FAILED'}", flush=True)
    n = len(LEMMAS) + len(RING)
    print(f"{n - bad} / {n} proved")
    return bad == 0


if __name__ == "__main__":
    if "--acsl" in sys.argv:
        print(acsl(), end="")
    elif "--ghost" in sys.argv:
        print(ghost(), end="")
    else:
        sys.exit(0 if check() else 1)
