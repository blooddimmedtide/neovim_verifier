"""Bit-level facts for the xdiff hash proofs, written once and used two ways.

`python3 -I lemmas.py` proves each with Z3 bit-vectors of 80 bits: every value is below
2^70, so the bit-vector and the integer meaning agree (x mod 2^64 is x & (2^64 - 1) in two's
complement). `--acsl` prints them as ACSL lemmas for WP, which has no bit-vector reasoning;
WP uses them as hypotheses and does not prove them (see ../CLAIM.md).
"""
import sys
M = 2 ** 64
ACSL = {
  # one step of the hash, as the C code computes it: ha += ha << 5; ha ^= (unsigned long)c;
  "hash_step": ("\\forall integer h, c; 0 <= h < 18446744073709551616 && -128 <= c < 256 ==> "
                "(unsigned long)((unsigned long)(h + (unsigned long)(h << 5)) ^ (unsigned long)c) == step(h, c)"),
  # the whitespace flags of xdiff.h (XDF_WHITESPACE_FLAGS == 30) are the bits 2, 4, 8 and 16
  "ws_bits": ("\\forall integer f; -9223372036854775808 <= f < 9223372036854775808 ==> "
              "(((f & 30) != 0) <==> ((f & 2) != 0 || (f & 4) != 0 || (f & 8) != 0 || (f & 16) != 0))"),
}

def check():
    import z3
    W = 80
    h, c = z3.BitVec("h", W), z3.BitVec("c", W)
    mask = z3.BitVecVal(M - 1, W)
    ul = lambda e: e & mask                       # (unsigned long)e = e mod 2^64
    u64c = z3.If(c < 0, c + z3.BitVecVal(M, W), c)
    step = ((h * 33) & mask) ^ u64c                # (h*33) % 2^64 for h >= 0, then xor
    lhs = ul(ul(h + ul(h * 32)) ^ ul(c))           # h << 5 on integers is h * 32
    hyp = z3.And(h >= 0, h < z3.BitVecVal(M, W), c >= -128, c < 256)
    s = z3.Solver(); s.add(hyp, lhs != step)
    r = s.check(); print("hash_step", "proved" if r == z3.unsat else "FAILED")
    ok = r == z3.unsat
    f = z3.BitVec("f", W)                          # & on integers is & on two's complement
    nz = lambda k: (f & z3.BitVecVal(k, W)) != 0
    s = z3.Solver(); s.add(f >= -2 ** 63, f < 2 ** 63, nz(30) != z3.Or(nz(2), nz(4), nz(8), nz(16)))
    r = s.check(); print("ws_bits", "proved" if r == z3.unsat else "FAILED")
    return ok and r == z3.unsat

if __name__ == "__main__":
    if "--acsl" in sys.argv:
        names = sys.argv[sys.argv.index("--acsl") + 1:] or list(ACSL)   # --acsl [name ...]
        print("".join(f"/*@ lemma {n}: {ACSL[n]}; */\n" for n in names), end="")
    else:
        sys.exit(0 if check() else 1)
