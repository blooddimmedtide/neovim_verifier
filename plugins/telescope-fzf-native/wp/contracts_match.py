"""ACSL for fzf.c's position helpers and calculate_score (fzf's calculateScore, algo.go).

The score is specified by recursive logic functions that restate fzf's calculateScore
loop (algo.go, v0.27.0) one byte at a time: cs_pidx (pattern bytes matched so far),
cs_cons (length of the current run of matches), cs_fb (first bonus of the run),
cs_gap (inside a gap), cs_score. They are definitions (no axioms); WP unfolds them.
"""

LOGIC = r"""
/*@ // the byte as compared: ASCII upper case folded when the match is case-insensitive
    // (fzf.c: (char)tolower((uint8_t)c), which keeps every other byte)
    logic integer fold(integer c, integer cs) = (cs == 0 && 65 <= c <= 90) ? c + 32 : c;
    // class of the byte before t[i]; fzf treats the text start as non-word
    logic integer pc{L}(char *t, integer i) = i <= 0 ? 0 : cls(t[i - 1]);
    logic integer cs_b{L}(char *t, integer i) = bonus(pc(t, i), cls(t[i]));

    logic integer cs_pidx{L}(char *t, char *p, integer cs, integer s, integer i) =
      i <= s ? 0 :
      cs_pidx(t, p, cs, s, i - 1) + (fold(t[i - 1], cs) == p[cs_pidx(t, p, cs, s, i - 1)] ? 1 : 0);
    predicate cs_m{L}(char *t, char *p, integer cs, integer s, integer i) =
      fold(t[i], cs) == p[cs_pidx(t, p, cs, s, i)];
    logic integer cs_cons{L}(char *t, char *p, integer cs, integer s, integer i) =
      i <= s ? 0 : (cs_m(t, p, cs, s, i - 1) ? cs_cons(t, p, cs, s, i - 1) + 1 : 0);
    logic integer cs_fb{L}(char *t, char *p, integer cs, integer s, integer i) =
      i <= s ? 0 :
      (cs_m(t, p, cs, s, i - 1) ?
         ((cs_cons(t, p, cs, s, i - 1) == 0 || cs_b(t, i - 1) == 8) ? cs_b(t, i - 1) : cs_fb(t, p, cs, s, i - 1))
       : 0);
    logic integer cs_gap{L}(char *t, char *p, integer cs, integer s, integer i) =
      i <= s ? 0 : (cs_m(t, p, cs, s, i - 1) ? 0 : 1);
    logic integer imax(integer a, integer b) = a > b ? a : b;
    // bonus of a matched byte t[i]: its own bonus at the start of a run, else the
    // largest of its own, the run's first bonus (8 if this one is 8) and BonusConsecutive
    logic integer cs_eb{L}(char *t, char *p, integer cs, integer s, integer i) =
      cs_cons(t, p, cs, s, i) == 0 ? cs_b(t, i) :
      imax(imax(cs_b(t, i), cs_b(t, i) == 8 ? 8 : cs_fb(t, p, cs, s, i)), 4);
    logic integer cs_score{L}(char *t, char *p, integer cs, integer s, integer i) =
      i <= s ? 0 :
      cs_score(t, p, cs, s, i - 1) +
      (cs_m(t, p, cs, s, i - 1) ?
         16 + (cs_pidx(t, p, cs, s, i - 1) == 0 ? 2 : 1) * cs_eb(t, p, cs, s, i - 1)
       : (cs_gap(t, p, cs, s, i - 1) == 1 ? -1 : -3));

    // a position array: size <= cap and room for cap entries
    predicate pos_ok{L}(fzf_position_t *pos) =
      \valid(pos) && pos->size <= pos->cap && pos->cap <= 0x1000000000000000 &&
      \valid(pos->data + (0 .. pos->cap - 1));
*/
"""


def PA(lo=None, hi=None, post=True):
    """Assigns of a position array that may be NULL: nothing when pos is NULL."""
    g = "pos != \\null"
    out = [f"{{ pos->{f} | integer k0; k0 == 0 && {g} }}" for f in ("cap", "data", "size")]
    if lo is not None:
        d = "\\at(pos->data, Post)" if post else "pos->data"
        out.append(f"{{ {d}[j0] | integer j0; {lo} <= j0 < {hi} && {g} }}")
    return ", ".join(out)

POSPRE = r"""requires pos == \null || pos_ok(pos);"""

CONTRACTS = {
"resize_pos": POSPRE + r"""
    requires pos != \null ==> pos->size + comp <= 0x1000000000000000 && pos->cap + add_len + 1 <= 0x1000000000000000;
    assigns """ + PA() + r""";
    behavior none:
      assumes pos == \null;
    behavior some:
      assumes pos != \null;
      ensures pos_ok(pos) && pos->size == \old(pos->size);
      ensures \old(pos->size) + comp > \old(pos->cap) ==> pos->cap == \old(pos->cap) + (add_len > 0 ? add_len : 1);
      ensures \old(pos->size) + comp <= \old(pos->cap) ==> pos->cap == \old(pos->cap) && pos->data == \old(pos->data);
      ensures \forall integer j; 0 <= j < pos->size ==> pos->data[j] == \old(pos->data[j]);
    complete behaviors; disjoint behaviors;""",

"unsafe_append_pos": r"""requires pos_ok(pos) && pos->size < 0x0800000000000000 && pos->cap < 0x0800000000000000;
    assigns pos->cap, pos->data, pos->size, \at(pos->data, Post)[pos->size];
    ensures pos_ok(pos) && pos->size == \old(pos->size) + 1 && pos->cap >= \old(pos->cap);
    ensures \old(pos->size) < \old(pos->cap) ==> pos->cap == \old(pos->cap) && pos->data == \old(pos->data);
    ensures pos->data[\old(pos->size)] == (uint32_t)value;
    ensures \forall integer j; 0 <= j < \old(pos->size) ==> pos->data[j] == \old(pos->data[j]);""",

"append_pos": POSPRE + r"""
    requires pos != \null ==> pos->size < 0x0800000000000000 && pos->cap < 0x0800000000000000;
    assigns """ + PA("pos->size", "pos->size + 1") + r""";
    behavior none:
      assumes pos == \null;
    behavior some:
      assumes pos != \null;
      ensures pos_ok(pos) && pos->size == \old(pos->size) + 1 && pos->cap >= \old(pos->cap);
      ensures \old(pos->size) < \old(pos->cap) ==> pos->cap == \old(pos->cap) && pos->data == \old(pos->data);
      ensures pos->data[\old(pos->size)] == (uint32_t)value;
      ensures \forall integer j; 0 <= j < \old(pos->size) ==> pos->data[j] == \old(pos->data[j]);
    complete behaviors; disjoint behaviors;""",

# start..end-1 appended (as uint32_t) when 0 < end - start, both below 2^31
"insert_range": POSPRE + r"""
    requires start <= end <= 2147483647;
    requires pos != \null ==> pos->size + (end - start) <= 0x0800000000000000 && pos->cap <= 0x0800000000000000;
    assigns """ + PA("pos->size", "pos->size + (end - start)") + r""";
    behavior none:
      assumes pos == \null || end == start;
      ensures pos != \null ==> pos->size == \old(pos->size) && pos->cap == \old(pos->cap) && pos->data == \old(pos->data);
    behavior some:
      assumes pos != \null && start < end;
      ensures pos_ok(pos) && pos->size == \old(pos->size) + (end - start);
      ensures \forall integer j; 0 <= j < \old(pos->size) ==> pos->data[j] == \old(pos->data[j]);
      ensures \forall integer k; 0 <= k < end - start ==> pos->data[\old(pos->size) + k] == start + k;
    complete behaviors; disjoint behaviors;""",

# Callers pass windows where no byte is compared against pattern[M] (cs_pidx < M before
# every byte of the window); the window is below 700 million bytes and the pattern below
# 60 million, so the int32_t score cannot overflow.
"calculate_score": r"""requires \valid_read(text) && \valid_read(text->data + (0 .. text->size - 1));
    requires \valid_read(pattern) && \valid_read(pattern->data + (0 .. pattern->size - 1));
    requires sidx <= eidx <= text->size && eidx - sidx <= 700000000 && pattern->size <= 60000000;
    requires eidx <= 4294967295;
    requires \forall integer i; sidx <= i < eidx ==>
               cs_pidx((char *)text->data, (char *)pattern->data, case_sensitive, sidx, i) < pattern->size;
    requires pos == \null || (pos_ok(pos) && pos->size + pattern->size <= 0x0400000000000000
                              && pos->cap <= 0x0400000000000000);
    requires pos != \null ==> \separated(pos, text, pattern);
    ensures \result == cs_score((char *)text->data, (char *)pattern->data, case_sensitive, sidx, eidx);
    assigns """ + PA("pos->size", "pos->size + pattern->size") + r""";
    behavior none:
      assumes pos == \null;
    behavior some:
      assumes pos != \null;
      ensures pos_ok(pos);
      ensures pos->size == \old(pos->size) + cs_pidx((char *)text->data, (char *)pattern->data, case_sensitive, sidx, eidx);
      ensures \forall integer j; 0 <= j < \old(pos->size) ==> pos->data[j] == \old(pos->data[j]);
      ensures \forall integer i; sidx <= i < eidx && cs_m((char *)text->data, (char *)pattern->data, case_sensitive, sidx, i) ==>
                pos->data[\old(pos->size) + cs_pidx((char *)text->data, (char *)pattern->data, case_sensitive, sidx, i)] == i;
    complete behaviors; disjoint behaviors;""",
}

CS = r"""(char *)text->data, (char *)pattern->data, case_sensitive, sidx"""

LOOPS = {
"insert_range": [("  for (size_t k = start; k < end; k++) {",
    r"""loop invariant start <= k <= end;
      loop invariant pos_ok(pos) && pos->size == \at(pos->size, Pre) + (k - start);
      loop invariant pos->cap >= \at(pos->size, Pre) + (end - start);
      loop invariant \forall integer j; 0 <= j < \at(pos->size, Pre) ==> pos->data[j] == \at(pos->data[j], Pre);
      loop invariant \forall integer j; 0 <= j < k - start ==> pos->data[\at(pos->size, Pre) + j] == start + j;
      loop assigns k, pos->size, pos->data[\at(pos->size, Pre) .. \at(pos->size, Pre) + (end - start) - 1];
      loop variant end - k;""")],
"calculate_score": [("  for (size_t idx = sidx; idx < eidx; idx++) {",
    r"""loop invariant sidx <= idx <= eidx;
      loop invariant pidx == cs_pidx(""" + CS + r""", idx) && pidx <= pattern->size;
      loop invariant consecutive == cs_cons(""" + CS + r""", idx) && 0 <= consecutive <= idx - sidx;
      loop invariant first_bonus == cs_fb(""" + CS + r""", idx) && 0 <= first_bonus <= 8;
      loop invariant in_gap == cs_gap(""" + CS + r""", idx);
      loop invariant score == cs_score(""" + CS + r""", idx);
      loop invariant -3 * (idx - sidx) <= score <= 32 * pidx;
      loop invariant prev_class == pc((char *)text->data, idx);
      loop invariant pos != \null ==> pos_ok(pos) && pos->size == \at(pos->size, Pre) + pidx
                       && pos->cap >= \at(pos->size, Pre) + pattern->size;
      loop invariant pos != \null ==> \forall integer j; 0 <= j < \at(pos->size, Pre) ==> pos->data[j] == \at(pos->data[j], Pre);
      loop invariant pos != \null ==> pos->data == \at(pos->data, LoopEntry) && pos->cap == \at(pos->cap, LoopEntry);
      loop invariant pos != \null ==> pos->cap <= 0x0400000000000000 + pattern->size;
      loop invariant \forall integer i; sidx <= i < idx && cs_m(""" + CS + r""", i) ==> cs_pidx(""" + CS + r""", i) < pidx;
      loop invariant pos != \null ==> \forall integer i; sidx <= i < idx && cs_m(""" + CS + r""", i) ==>
                       pos->data[\at(pos->size, Pre) + cs_pidx(""" + CS + r""", i)] == i;
      loop assigns idx, pidx, score, consecutive, in_gap, first_bonus, prev_class,
                   """ + PA("\\at(pos->size, Pre)", "\\at(pos->size, Pre) + pattern->size", post=False) + r""";
      loop variant eidx - idx;""")],
}

# ---------------------------------------------------------------- prefix, suffix, equal
LOGIC += r"""
/*@ // pattern p[0..m) equals the folded text t[s..s+m)
    predicate eq_at{L}(char *t, char *p, integer cs, integer s, integer m) =
      \forall integer k; 0 <= k < m ==> fold(t[s + k], cs) == p[k];
    // t[0..w) is the maximal white prefix / t[n-w..n) the maximal white suffix of t[0..n)
    predicate lead_w{L}(char *t, integer n, integer w) =
      0 <= w <= n && (\forall integer j; 0 <= j < w ==> white(t[j])) && (w == n || !white(t[w]));
    predicate trail_w{L}(char *t, integer n, integer w) =
      0 <= w <= n && (\forall integer j; n - w <= j < n ==> white(t[j])) && (w == n || !white(t[n - w - 1]));
    predicate res_none(fzf_result_t r) = r.start == -1 && r.end == -1 && r.score == 0;
*/
"""

MATCHPRE = r"""requires \valid_read(text) && \valid_read(text->data + (0 .. text->size - 1));
    requires \valid_read(pattern) && \valid_read(pattern->data + (0 .. pattern->size - 1));
    requires text->size <= 2147483647 && pattern->size <= 60000000;
    requires pos == \null || (pos_ok(pos) && pos->size + text->size <= 0x0400000000000000
                              && pos->cap <= 0x0400000000000000);
    requires pos != \null ==> \separated(pos, text, pattern);"""

POSRANGE = r"""
      ensures pos != \null ==> pos_ok(pos);
      ensures pos != \null ==> pos->size == \old(pos->size) + (\result.end - \result.start);
      ensures pos != \null ==> \forall integer j; 0 <= j < \old(pos->size) ==> pos->data[j] == \old(pos->data[j]);
      ensures pos != \null ==> \forall integer k; 0 <= k < \result.end - \result.start ==> pos->data[\old(pos->size) + k] == \result.start + k;"""
NOPOS = r"""
      ensures pos != \null ==> pos->size == \old(pos->size);"""

TD = r"""(char *)text->data"""
PD = r"""(char *)pattern->data"""

CONTRACTS["fzf_prefix_match"] = MATCHPRE + r"""
    assigns """ + PA("pos->size", "pos->size + pattern->size") + r""";
    behavior empty:
      assumes pattern->size == 0;
      ensures \result.start == 0 && \result.end == 0 && \result.score == 0;""" + NOPOS + r"""
    behavior match:
      assumes pattern->size > 0;
      assumes \exists integer s; (white(pattern->data[0]) ? s == 0 : lead_w(""" + TD + r""", text->size, s))
                && s + pattern->size <= text->size && eq_at(""" + TD + ", " + PD + r""", case_sensitive, s, pattern->size);
      ensures white(pattern->data[0]) ? \result.start == 0 : lead_w(""" + TD + r""", text->size, \result.start);
      ensures \result.end == \result.start + pattern->size;
      ensures \result.score == cs_score(""" + TD + ", " + PD + r""", case_sensitive, \result.start, \result.end);""" + POSRANGE + r"""
    behavior nomatch:
      assumes pattern->size > 0;
      assumes !\exists integer s; (white(pattern->data[0]) ? s == 0 : lead_w(""" + TD + r""", text->size, s))
                && s + pattern->size <= text->size && eq_at(""" + TD + ", " + PD + r""", case_sensitive, s, pattern->size);
      ensures res_none(\result);""" + NOPOS + r"""
    complete behaviors; disjoint behaviors;"""

CONTRACTS["fzf_suffix_match"] = MATCHPRE + r"""
    assigns """ + PA("pos->size", "pos->size + pattern->size") + r""";
    behavior empty:
      assumes pattern->size == 0;
      ensures \exists integer w; trail_w(""" + TD + r""", text->size, w) && \result.start == text->size - w && \result.end == \result.start;
      ensures \result.score == 0;""" + NOPOS + r"""
    behavior match:
      assumes pattern->size > 0;
      assumes \exists integer e; (white(pattern->data[pattern->size - 1]) ? e == text->size
                                  : \exists integer w; trail_w(""" + TD + r""", text->size, w) && e == text->size - w)
                && pattern->size <= e && eq_at(""" + TD + ", " + PD + r""", case_sensitive, e - pattern->size, pattern->size);
      ensures white(pattern->data[pattern->size - 1]) ? \result.end == text->size
              : \exists integer w; trail_w(""" + TD + r""", text->size, w) && \result.end == text->size - w;
      ensures \result.start == \result.end - pattern->size;
      ensures \result.score == cs_score(""" + TD + ", " + PD + r""", case_sensitive, \result.start, \result.end);""" + POSRANGE + r"""
    behavior nomatch:
      assumes pattern->size > 0;
      assumes !\exists integer e; (white(pattern->data[pattern->size - 1]) ? e == text->size
                                   : \exists integer w; trail_w(""" + TD + r""", text->size, w) && e == text->size - w)
                && pattern->size <= e && eq_at(""" + TD + ", " + PD + r""", case_sensitive, e - pattern->size, pattern->size);
      ensures res_none(\result);""" + NOPOS + r"""
    complete behaviors; disjoint behaviors;"""

# fzf's EqualMatch: the text without its white prefix and suffix equals the pattern; the
# score is the closed form (ScoreMatch + BonusBoundary) * M + (BonusFirstCharMultiplier - 1) * BonusBoundary.
CONTRACTS["fzf_equal_match"] = MATCHPRE + r"""
    assigns """ + PA("pos->size", "pos->size + pattern->size") + r""";
    behavior empty:
      assumes pattern->size == 0;
      ensures res_none(\result);""" + NOPOS + r"""
    behavior match:
      assumes pattern->size > 0;
      assumes \exists integer a, b; lead_w(""" + TD + r""", text->size, a) && trail_w(""" + TD + r""", text->size, b)
                && text->size - a - b == pattern->size && eq_at(""" + TD + ", " + PD + r""", case_sensitive, a, pattern->size);
      ensures lead_w(""" + TD + r""", text->size, \result.start) && \result.end == \result.start + pattern->size;
      ensures \result.score == 24 * pattern->size + 8;""" + POSRANGE + r"""
    behavior nomatch:
      assumes pattern->size > 0;
      assumes !\exists integer a, b; lead_w(""" + TD + r""", text->size, a) && trail_w(""" + TD + r""", text->size, b)
                && text->size - a - b == pattern->size && eq_at(""" + TD + ", " + PD + r""", case_sensitive, a, pattern->size);
      ensures res_none(\result);""" + NOPOS + r"""
    complete behaviors; disjoint behaviors;"""

LOOPS["fzf_prefix_match"] = [("  for (size_t i = 0; i < M; i++) {",
    r"""loop invariant 0 <= i <= M && trimmed_len + M <= text->size;
      loop invariant eq_at(""" + TD + ", " + PD + r""", case_sensitive, trimmed_len, i);
      loop invariant cs_pidx(""" + TD + ", " + PD + r""", case_sensitive, trimmed_len, trimmed_len + i) == i;
      loop invariant \forall integer x; trimmed_len <= x <= trimmed_len + i ==> cs_pidx(""" + TD + ", " + PD + r""", case_sensitive, trimmed_len, x) == x - trimmed_len;
      loop assigns i; loop variant M - i;"""),
    ("  size_t start = trimmed_len;",
    r"""assert \forall integer x; trimmed_len <= x < trimmed_len + M ==>
               cs_pidx(""" + TD + ", " + PD + r""", case_sensitive, trimmed_len, x) == x - trimmed_len;""")]
LOOPS["fzf_suffix_match"] = [("  for (size_t idx = 0; idx < M; idx++) {",
    r"""loop invariant 0 <= idx <= M && diff + M == trimmed_len && trimmed_len <= text->size;
      loop invariant eq_at(""" + TD + ", " + PD + r""", case_sensitive, diff, idx);
      loop invariant cs_pidx(""" + TD + ", " + PD + r""", case_sensitive, diff, diff + idx) == idx;
      loop invariant \forall integer x; diff <= x <= diff + idx ==> cs_pidx(""" + TD + ", " + PD + r""", case_sensitive, diff, x) == x - diff;
      loop assigns idx; loop variant M - idx;"""),
    ("  size_t start = trimmed_len - M;",
    r"""assert \forall integer x; diff <= x < diff + M ==>
               cs_pidx(""" + TD + ", " + PD + r""", case_sensitive, diff, x) == x - diff;""")]
LOOPS["fzf_equal_match"] = [
    ("    for (size_t idx = 0; idx < M; idx++) {\n      char pchar = pattern->data[idx];\n      char c = text->data[trimmed_len + idx];\n      if (!case_sensitive) {\n        c = (char)tolower((uint8_t)c);\n      }\n      if (normalize_rune(c)",
     r"""loop invariant 0 <= idx <= M && match == \true;
        loop invariant eq_at(""" + TD + ", " + PD + r""", case_sensitive, trimmed_len, idx);
        loop assigns idx, match; loop variant M - idx;"""),
    ("    for (size_t idx = 0; idx < M; idx++) {\n      char pchar = pattern->data[idx];\n      char c = text->data[trimmed_len + idx];\n      if (!case_sensitive) {\n        c = (char)tolower((uint8_t)c);\n      }\n      if (c != pchar)",
     r"""loop invariant 0 <= idx <= M && match == \true;
        loop invariant eq_at(""" + TD + ", " + PD + r""", case_sensitive, trimmed_len, idx);
        loop assigns idx, match; loop variant M - idx;"""),
]
