"""ACSL contracts for regexp.c's getdecchrs (gethexchrs/getoctchrs are bounded and bit-level: see ../cbmc).

The reference values (dval, hval, oval) are the ordinary positional values of the
digit strings; the digit classes are written out from the C/POSIX definitions, not
from Neovim's helpers.
"""

LOGIC = r"""
/*@ predicate is_dec(integer c) = '0' <= c <= '9';
    // value of the first n characters of s read as decimal digits
    logic integer dval{L}(char *s, integer n) = n <= 0 ? 0 : 10 * dval(s, n - 1) + ((unsigned char)s[n - 1] - '0');
    // s starts with exactly k decimal digits, then a non-digit
    predicate dec_run{L}(char *s, integer k) =
      0 <= k && \valid_read(s + (0 .. k)) && !is_dec((unsigned char)s[k])
      && \forall integer j; 0 <= j < k ==> is_dec((unsigned char)s[j]);
*/
/*@ ghost
  // dval does not decrease along a digit run (induction on n, done by the loop)
  /@ requires 0 <= m <= n;
     requires \forall integer j; 0 <= j < n ==> is_dec((unsigned char)s[j]);
     assigns \nothing;
     ensures 0 <= dval(s, m) <= dval(s, n); @/
  void dval_mono(char *s, size_t m, size_t n) {
    size_t j = 0;
    /@ loop invariant 0 <= j <= m && 0 <= dval(s, j);
       loop assigns j; loop variant m - j; @/
    while (j < m) j++;
    /@ loop invariant m <= j <= n && 0 <= dval(s, m) <= dval(s, j);
       loop assigns j; loop variant n - j; @/
    while (j < n) j++;
  }
*/
"""

# Contracts. "{k}" marks the ghost length parameter where one is used.
CONTRACTS = {
    # Fixed fork version: every digit run, values above INT_MAX reported as INT_MAX + 1.
    "getdecchrs/fixed": r"""requires dec_run(regparse, k);
    assigns regparse, curchr;
    behavior none:
      assumes k == 0;
      ensures \result == -1 && regparse == \old(regparse) && curchr == \old(curchr);
    behavior some:
      assumes k > 0;
      ensures regparse == \old(regparse) + k && curchr == -1;
      ensures \result == (dval(\old(regparse), k) <= INT_MAX ? dval(\old(regparse), k) : INT_MAX + 1);
    complete behaviors; disjoint behaviors;""",

    # Upstream version: the same value, but only provable while the run is shorter
    # than 2^31 characters and its value fits int64_t (findings/regexp-getdecchrs-overflow.md).
    "getdecchrs/upstream": r"""requires dec_run(regparse, k);
    requires k <= INT_MAX && dval(regparse, k) <= INT64_MAX;
    assigns regparse, curchr;
    behavior none:
      assumes k == 0;
      ensures \result == -1 && regparse == \old(regparse) && curchr == \old(curchr);
    behavior some:
      assumes k > 0;
      ensures regparse == \old(regparse) + k && curchr == -1;
      ensures \result == dval(\old(regparse), k);
    complete behaviors; disjoint behaviors;""",
}

GHOST_PARAMS = {
    "getdecchrs": ("static int64_t getdecchrs(void)", "size_t k"),
}

LOOPS = {
    "getdecchrs/fixed": [("  while (true) {", r"""loop invariant 0 <= regparse - start <= k && \base_addr(regparse) == \base_addr(start);
    loop invariant start == \at(regparse, Pre);
    loop invariant nr == (dval(start, regparse - start) <= INT_MAX ? dval(start, regparse - start) : INT_MAX + 1);
    loop invariant 0 <= nr <= INT_MAX + 1;
    loop invariant regparse - start < k ==> is_dec((unsigned char)*regparse);
    loop invariant regparse - start == k ==> !is_dec((unsigned char)*regparse);
    loop invariant regparse != start ==> curchr == -1;
    loop invariant regparse == start ==> curchr == \at(curchr, Pre);
    loop assigns nr, regparse, curchr;
    loop variant k - (regparse - start);"""),
                         ("    regparse++;", r"""ghost dval_mono(start, (size_t)(regparse - start), (size_t)(regparse - start) + 1);""")],
    "getdecchrs/upstream": [("  int64_t nr = 0;", r"""ghost char *s0 = regparse;"""),
                            ("  for (i = 0;; i++) {", r"""loop invariant 0 <= i <= k && s0 == \at(regparse, Pre);
    loop invariant regparse == \at(regparse, Pre) + i;
    loop invariant nr == dval(\at(regparse, Pre), i) && 0 <= nr;
    loop invariant i < k ==> is_dec((unsigned char)*regparse);
    loop invariant i == k ==> !is_dec((unsigned char)*regparse);
    loop invariant i > 0 ==> curchr == -1;
    loop invariant i == 0 ==> curchr == \at(curchr, Pre);
    loop assigns i, c, nr, regparse, curchr;
    loop variant k - i;"""),
                            ("    nr *= 10;", r"""ghost dval_mono(s0, i + 1, k);""")],
}
