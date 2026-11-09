"""Insert the ACSL contract of uhp_table_find into the verbatim extraction from ../cbmc/build.py.

Usage: python3 -I annotate.py <undo_io.c from build.py> <out.c>
Fails if an anchor line is missing or appears more than once. The code itself is not changed.
"""
import sys

CONTRACT = """/*@ requires count: num_head >= 0;
    requires valid_table: num_head > 0 ==> \\valid_read(uhp_table + (0 .. num_head - 1));
    requires valid_heads: \\forall integer i; 0 <= i < num_head ==> \\valid_read(uhp_table[i]);
    requires sorted: \\forall integer i, j; 0 <= i <= j < num_head ==>
                       uhp_table[i]->uh_seq <= uhp_table[j]->uh_seq;
    assigns \\nothing;
    behavior found:
      assumes \\exists integer i; 0 <= i < num_head && uhp_table[i]->uh_seq == seq;
      ensures 0 <= \\result < num_head && uhp_table[\\result]->uh_seq == seq;
    behavior missing:
      assumes \\forall integer i; 0 <= i < num_head ==> uhp_table[i]->uh_seq != seq;
      ensures \\result == -1;
    complete behaviors;
    disjoint behaviors;
*/
"""
LOOP = """  /*@ loop invariant 0 <= lo;
      loop invariant hi <= num_head - 1;
      loop invariant below: \\forall integer i; 0 <= i < lo && i < num_head ==> uhp_table[i]->uh_seq < seq;
      loop invariant above: \\forall integer i; hi < i < num_head && 0 <= i ==> uhp_table[i]->uh_seq > seq;
      loop assigns lo, hi;
      loop variant hi - lo;
  */
"""

def main(src, out):
    lines = open(src).read().split("\n")
    sig = [i for i, l in enumerate(lines) if l.startswith("static int uhp_table_find(")]
    if len(sig) != 1: sys.exit("annotate: signature anchor")
    s = sig[0]
    loop = [i for i in range(s, s + 8) if lines[i] == "  while (lo <= hi) {"]
    if len(loop) != 1: sys.exit("annotate: loop anchor")
    mid = [i for i in range(s, s + 10) if lines[i] == "    int mid = lo + (hi - lo) / 2;"]
    if len(mid) != 1: sys.exit("annotate: mid anchor")
    lines.insert(mid[0] + 1, "    //@ assert mid_range: lo <= mid <= hi;")
    lines.insert(mid[0], "    //@ assert diff_range: 0 <= hi - lo <= 2147483647;")
    lines.insert(loop[0], LOOP.rstrip("\n"))
    lines.insert(s, CONTRACT.rstrip("\n"))
    open(out, "w").write("\n".join(lines))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
