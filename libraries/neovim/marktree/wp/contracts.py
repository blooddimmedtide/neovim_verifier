"""ACSL for marktree.c leaf functions, written from the doc comments and from what the
B-tree needs: positions are ordered lexicographically (row, then col); a child's keys are
stored relative to its parent key (relative/unrelative are inverse and keep the order);
intersect arrays are ascending; meta counters count non-end, valid keys per decoration kind."""

LOGIC = r"""
/*@ // lexicographic order on positions (row, col)
    predicate pleq(integer r1, integer c1, integer r2, integer c2) = r1 < r2 || (r1 == r2 && c1 <= c2);
    // relative(base, v): v's offset from base
    logic integer rel_row(integer br, integer vr) = vr == br ? 0 : vr - br;
    logic integer rel_col(integer br, integer bc, integer vr, integer vc) = vr == br ? vc - bc : vc;
    // unrelative(base, v): absolute position of offset v from base
    logic integer unr_row(integer br, integer vr) = vr == 0 ? br : vr + br;
    logic integer unr_col(integer bc, integer vr, integer vc) = vr == 0 ? vc + bc : vc;
    predicate pos_ok(integer r, integer c) = 0 <= r <= INT_MAX && 0 <= c <= INT_MAX;

    // the B-tree's relative encoding loses nothing: unrelative undoes relative
    lemma unrel_rel: \forall integer br, bc, vr, vc;
      pos_ok(br, bc) && pos_ok(vr, vc) && pleq(br, bc, vr, vc) ==>
        unr_row(br, rel_row(br, vr)) == vr && unr_col(bc, rel_row(br, vr), rel_col(br, bc, vr, vc)) == vc;
    // and keeps the order of positions at or after the base
    lemma rel_order: \forall integer br, bc, vr, vc, wr, wc;
      pos_ok(br, bc) && pos_ok(vr, vc) && pos_ok(wr, wc) && pleq(br, bc, vr, vc) && pleq(br, bc, wr, wc) ==>
        (pleq(vr, vc, wr, wc) <==>
         pleq(rel_row(br, vr), rel_col(br, bc, vr, vc), rel_row(br, wr), rel_col(br, bc, wr, wc)));
    // relative offsets are themselves valid positions
    lemma rel_ok: \forall integer br, bc, vr, vc;
      pos_ok(br, bc) && pos_ok(vr, vc) && pleq(br, bc, vr, vc) ==>
        pos_ok(rel_row(br, vr), rel_col(br, bc, vr, vc));

    logic integer sgn(integer x) = x < 0 ? -1 : x > 0 ? 1 : 0;
    logic integer cmp3(integer a, integer b) = sgn(a - b);
    logic integer cmp_mask = 0xC003; // RIGHT_GRAVITY | END | REAL | LAST, checked by build.py

    // key order of the B-tree (what key_cmp computes)
    logic integer kcmp(MTKey a, MTKey b) =
      cmp3(a.pos.row, b.pos.row) != 0 ? cmp3(a.pos.row, b.pos.row)
      : cmp3(a.pos.col, b.pos.col) != 0 ? cmp3(a.pos.col, b.pos.col)
      : cmp3(a.flags & cmp_mask, b.flags & cmp_mask);
    lemma kcmp_anti: \forall MTKey a, b; kcmp(b, a) == -kcmp(a, b);
    lemma kcmp_trans: \forall MTKey a, b, c; kcmp(a, b) <= 0 && kcmp(b, c) <= 0 ==> kcmp(a, c) <= 0;
    lemma kcmp_trans_lt2: \forall MTKey a, b, c; kcmp(a, b) < 0 && kcmp(b, c) <= 0 ==> kcmp(a, c) < 0;
    lemma kcmp_trans_lt: \forall MTKey a, b, c; kcmp(a, b) <= 0 && kcmp(b, c) < 0 ==> kcmp(a, c) < 0;
    // keys of a node are in key order
    predicate keys_sorted{L}(MTNode *x) =
      \forall integer i, j; 0 <= i <= j < x->n ==> kcmp(x->key[i], x->key[j]) <= 0;
    predicate sorted_u64(uint64_t *a, integer n) = \forall integer i, j; 0 <= i <= j < n ==> a[i] <= a[j];

    logic integer bit(integer f, integer b) = (f & b) != 0 ? 1 : 0;
    logic integer msum{L}(MetaFilter c, MetaFilter f, integer m) =
      m <= 0 ? 0 : msum(c, f, m - 1) + (c[m - 1] & f[m - 1]);
    logic integer add32(integer x, integer y) = (x + y) % 4294967296;
*/
"""

MT_EFFECT = r"""(!(f & 2) && !(f & 64)) ==>
       meta_inc[0] == add32(\old(meta_inc[0]), bit(f, 4096)) && meta_inc[1] == add32(\old(meta_inc[1]), bit(f, 2048))
    && meta_inc[2] == add32(\old(meta_inc[2]), bit(f, 1024)) && meta_inc[3] == add32(\old(meta_inc[3]), bit(f, 512))
    && meta_inc[4] == add32(\old(meta_inc[4]), bit(f, 8192))"""


def contracts(fixed):
    c = {
        "mt_end": r"""assigns \nothing;
    ensures \result == ((key.flags & 2) != 0);""",
        "mt_invalid": r"""assigns \nothing;
    ensures \result == ((key.flags & 64) != 0);""",
        "pos_leq": r"""assigns \nothing;
    ensures \result <==> pleq(a.row, a.col, b.row, b.col);""",
        "pos_less": r"""assigns \nothing;
    ensures \result <==> !pleq(b.row, b.col, a.row, a.col);
    ensures \result <==> (pleq(a.row, a.col, b.row, b.col) && !(a.row == b.row && a.col == b.col));""",
        "relative": r"""requires \valid(val);
    requires pos_ok(base.row, base.col) && pos_ok(val->row, val->col);
    requires pleq(base.row, base.col, val->row, val->col);   // the function asserts it
    assigns *val;
    ensures val->row == rel_row(base.row, \old(val->row));
    ensures val->col == rel_col(base.row, base.col, \old(val->row), \old(val->col));
    ensures pos_ok(val->row, val->col);""",
        "unrelative": r"""requires \valid(val);
    requires pos_ok(base.row, base.col) && pos_ok(val->row, val->col);
    // the absolute position is a valid position (true of any key in a buffer)
    requires pos_ok(unr_row(base.row, val->row), unr_col(base.col, val->row, val->col));
    assigns *val;
    ensures val->row == unr_row(base.row, \old(val->row));
    ensures val->col == unr_col(base.col, \old(val->row), \old(val->col));""",
        "compose": r"""requires \valid(base);
    requires pos_ok(base->row, base->col) && pos_ok(val.row, val.col);
    requires pos_ok(unr_row(base->row, val.row), unr_col(base->col, val.row, val.col));
    assigns *base;
    ensures base->row == unr_row(\old(base->row), val.row);
    ensures base->col == unr_col(\old(base->col), val.row, val.col);""",
        "key_cmp": r"""assigns \nothing;
    ensures \result == kcmp(a, b);""",
        "marktree_getp_aux": r"""requires \valid_read(x) && 0 <= x->n <= 2 * MT_BRANCH_FACTOR - 1;
    requires keys_sorted(x);
    requires match == \null || \valid(match);
    assigns *match;
    // the code returns the index of the last key not after k (-1 if none), which is what
    // the callers use; the doc comment's "0 to x->n" range is wrong (finding marktree-getp-doc.md)
    ensures -1 <= \result < x->n || (x->n == 0 && \result == -1);
    ensures \forall integer i; 0 <= i <= \result ==> kcmp(x->key[i], k) <= 0;
    ensures \forall integer i; 0 <= i < \result ==> kcmp(x->key[i], k) < 0;
    // a match is the first equal key; otherwise every key after the result is after k
    ensures (\result < 0 || kcmp(x->key[\result], k) != 0) ==>
      \forall integer i; \result < i < x->n ==> kcmp(x->key[i], k) > 0;
    ensures match != \null ==> (*match <==> (0 <= \result && kcmp(x->key[\result], k) == 0));""",
        "marktree_itr_node_done": r"""requires \valid_read(itr);
    requires itr->x != \null ==> \valid_read(itr->x) && 0 <= itr->x->n <= 2 * MT_BRANCH_FACTOR - 1;
    assigns \nothing;
    ensures \result <==> (itr->x == \null || itr->i == itr->x->n - 1);""",
        "marktree_itr_pos": r"""requires \valid_read(itr) && \valid_read(itr->x) && 0 <= itr->i < 2 * MT_BRANCH_FACTOR - 1;
    requires pos_ok(itr->pos.row, itr->pos.col);
    requires \let p = itr->x->key[itr->i].pos; pos_ok(p.row, p.col)
             && pos_ok(unr_row(itr->pos.row, p.row), unr_col(itr->pos.col, p.row, p.col));
    assigns \nothing;
    ensures \let p = itr->x->key[itr->i].pos;
      \result.row == unr_row(itr->pos.row, p.row) && \result.col == unr_col(itr->pos.col, p.row, p.col);""",
        "itr_eq": r"""requires \valid_read(itr1) && \valid_read(itr2) && \valid_read(itr1->x) && \valid_read(itr2->x);
    requires 0 <= itr1->i < 2 * MT_BRANCH_FACTOR - 1 && 0 <= itr2->i < 2 * MT_BRANCH_FACTOR - 1;
    assigns \nothing;
    ensures \result <==> &itr1->x->key[itr1->i] == &itr2->x->key[itr2->i];
    // for two nodes that are the same or do not overlap (any two nodes of a tree):
    ensures (itr1->x == itr2->x || \separated(itr1->x, itr2->x)) ==>
      (\result <==> (itr1->x == itr2->x && itr1->i == itr2->i));""",
        "intersection_has": r"""requires \valid_read(x) && \valid_read(x->items + (0 .. x->size - 1));
    requires sorted_u64(x->items, x->size);   // "ascending intersect array"
    assigns \nothing;
    ensures \result <==> \exists integer i; 0 <= i < x->size && x->items[i] == id;""",
        "intersect_item_pos": r"""requires \valid_read(x) && \valid_read(x->intersect.items + (0 .. x->intersect.size - 1));
    requires sorted_u64(x->intersect.items, x->intersect.size);
    assigns \nothing;
    ensures 0 <= \result <= x->intersect.size;
    ensures \forall integer i; 0 <= i < \result ==> x->intersect.items[i] < id;
    ensures \forall integer i; \result <= i < x->intersect.size ==> x->intersect.items[i] >= id;""",
        "meta_describe_key_inc": r"""requires \valid(meta_inc + (0 .. 4)) && \valid_read(k);
    requires \separated(meta_inc + (0 .. 4), k);
    assigns meta_inc[0 .. 4];
    ensures \let f = k->flags; """ + MT_EFFECT + r""";
    ensures \let f = k->flags; ((f & 2) || (f & 64)) ==> \forall integer m; 0 <= m < 5 ==> meta_inc[m] == \old(meta_inc[m]);""",
        "meta_describe_key": r"""requires \valid(meta_inc + (0 .. 4));
    assigns meta_inc[0 .. 4];
    ensures \let f = k.flags; (!(f & 2) && !(f & 64)) ==>
         meta_inc[0] == bit(f, 4096) && meta_inc[1] == bit(f, 2048) && meta_inc[2] == bit(f, 1024)
      && meta_inc[3] == bit(f, 512) && meta_inc[4] == bit(f, 8192);
    ensures \let f = k.flags; ((f & 2) || (f & 64)) ==> \forall integer m; 0 <= m < 5 ==> meta_inc[m] == 0;""",
    }
    if fixed:
        c["meta_has"] = r"""requires \valid_read(meta_count + (0 .. 4)) && \valid_read(meta_filter + (0 .. 4));
    assigns \nothing;
    ensures \result <==> \exists integer m; 0 <= m < 5 && (meta_count[m] & meta_filter[m]) != 0;"""
    else:
        # Upstream sums the masked counts in a uint32_t; the sum can wrap to 0 (finding
        # marktree-meta-has-wrap.md). Proved only under this extra, undocumented precondition.
        c["meta_has"] = r"""requires \valid_read(meta_count + (0 .. 4)) && \valid_read(meta_filter + (0 .. 4));
    requires (meta_count[0] & meta_filter[0]) + (meta_count[1] & meta_filter[1]) + (meta_count[2] & meta_filter[2])
           + (meta_count[3] & meta_filter[3]) + (meta_count[4] & meta_filter[4]) <= UINT32_MAX;
    assigns \nothing;
    ensures \result <==> \exists integer m; 0 <= m < 5 && (meta_count[m] & meta_filter[m]) != 0;"""
    return c


def annotations(fixed):
    a = {
        "marktree_getp_aux": [("before", "  while (begin < end) {",
            r"""loop invariant 0 <= begin <= end <= x->n;
      loop invariant \forall integer i; 0 <= i < begin ==> kcmp(x->key[i], k) < 0;
      loop invariant \forall integer i; end <= i < x->n ==> kcmp(x->key[i], k) >= 0;
      loop assigns begin, end; loop variant end - begin;""")],
        "intersection_has": [("before", "  for (size_t i = 0; i < kv_size(*x); i++) {",
            r"""loop invariant 0 <= i <= x->size;
      loop invariant \forall integer j; 0 <= j < i ==> x->items[j] < id;
      loop assigns i; loop variant x->size - i;""")],
        "intersect_item_pos": [("before", "  while (lo < hi) {",
            r"""loop invariant 0 <= lo <= hi <= x->intersect.size;
      loop invariant \forall integer i; 0 <= i < lo ==> x->intersect.items[i] < id;
      loop invariant \forall integer i; hi <= i < x->intersect.size ==> x->intersect.items[i] >= id;
      loop assigns lo, hi; loop variant hi - lo;""")],
    }
    if fixed:
        a["meta_has"] = [("before", "  for (int m = 0; m < kMTMetaCount; m++) {",
            r"""loop invariant 0 <= m <= 5;
      loop invariant \forall integer j; 0 <= j < m ==> (meta_count[j] & meta_filter[j]) == 0;
      loop assigns m; loop variant 5 - m;""")]
    else:
        a["meta_has"] = [("before", "  for (int m = 0; m < kMTMetaCount; m++) {",
            r"""loop invariant 0 <= m <= 5;
      loop invariant count == msum(meta_count, meta_filter, m);
      loop assigns m, count; loop variant 5 - m;""")]
    return a
