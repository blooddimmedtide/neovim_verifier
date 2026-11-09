"""ACSL contracts for garray.c, written from the doc comments and the growth policy
the comments in ga_grow describe. `fixed` selects the verified_neovim versions of
ga_grow and ga_concat_strings (and the callers' contracts that follow from them)."""

LOGIC = r"""
/*@ logic integer imax(integer a, integer b) = a >= b ? a : b;
    logic integer imin(integer a, integer b) = a <= b ? a : b;
    // bytes owned by the array: ga_maxlen items of ga_itemsize bytes
    logic integer ga_bytes{L}(garray_T *g) = g->ga_itemsize * g->ga_maxlen;
    // a well-formed growing array (what ga_init and ga_grow maintain)
    predicate ga_ok{L}(garray_T *g) =
      \valid(g) && 0 <= g->ga_len <= g->ga_maxlen && g->ga_itemsize >= 1
      && \valid((char *)g->ga_data + (0 .. ga_bytes(g) - 1))
      && \base_addr(g) != \base_addr((char *)g->ga_data);   // the items are not inside *g
    // ga_maxlen after growing for n more items (n > room): upstream policy
    // "at least n, at least growsize, at least half the current length"
    logic integer grown_up(integer len, integer gs, integer n) = len + imax(imax(n, gs), len / 2);
    // fixed policy: the same, but the extra growth stops at INT_MAX items
    logic integer grown_fix(integer len, integer gs, integer n) =
      len + imax(imax(n, imin(gs, INT_MAX - len)), imin(len / 2, INT_MAX - len));
    // number of non-NULL pointers among a[0 .. n-1]
    logic integer nn{L}(void **a, integer n) = n <= 0 ? 0 : nn(a, n - 1) + (a[n - 1] != \null ? 1 : 0);
    // integer division bound (the fixed ga_concat_strings overflow test uses it)
    lemma div_bound: \forall integer a, b, c; 0 <= a && 0 < b && 0 <= c ==> (c > a / b <==> c * b > a);
    // a string has one length (proved below)
    lemma str_len_unique{L}: \forall char *s, integer n, m; str_len(s, n) && str_len(s, m) ==> n == m;
*/
/*@ // ga_concat_strings: Ls[k] is the length of string k, m the length of sep
    logic integer sumL{L}(size_t *Ls, integer i) = i <= 0 ? 0 : sumL(Ls, i - 1) + Ls[i - 1];
    // where string k starts in the result
    logic integer off{L}(size_t *Ls, integer m, integer k) = k <= 0 ? 0 : off(Ls, m, k - 1) + Ls[k - 1] + m;
    // length of the result for n >= 1 strings
    logic integer total{L}(size_t *Ls, integer m, integer n) = sumL(Ls, n) + (n - 1) * m;
*/
/*@ ghost
  // induction facts about sumL and off, done by the loop
  /@ requires \valid_read(Ls + (0 .. n - 1));
     assigns \nothing;
     ensures \forall integer i; 0 <= i <= n ==> off(Ls, m, i) == sumL(Ls, i) + i * m;
     ensures \forall integer i, k; 0 <= i <= k <= n ==> 0 <= sumL(Ls, i) <= sumL(Ls, k);
     ensures \forall integer i, k; 0 <= i < k <= n ==> off(Ls, m, i) + Ls[i] + m <= off(Ls, m, k); @/
  void concat_facts(size_t *Ls, size_t m, size_t n) {
    size_t j = 0;
    /@ loop invariant 0 <= j <= n;
       loop invariant \forall integer i; 0 <= i <= j ==> off(Ls, m, i) == sumL(Ls, i) + i * m;
       loop invariant \forall integer i, k; 0 <= i <= k <= j ==> 0 <= sumL(Ls, i) <= sumL(Ls, k);
       loop invariant \forall integer i, k; 0 <= i < k <= j ==> off(Ls, m, i) + Ls[i] + m <= off(Ls, m, k);
       loop assigns j; loop variant n - j; @/
    while (j < n) j++;
  }
*/

/*@ // ga_remove_duplicate_strings on the n strings o[0 .. n-1], sorted as S(k) = vp_sorted(o, n, k):
    // entry k of the sorted order is kept iff it is the first or not path_equal to the one before
    predicate kept{L}(char **o, integer n, integer k) =
      k == 0 || !vp_path_eq(vp_sorted(o, n, k - 1), vp_sorted(o, n, k));
    // number of kept / removed entries among k in [a, b)
    logic integer ck{L}(char **o, integer n, integer a, integer b) =
      a >= b ? 0 : (kept(o, n, a) ? 1 : 0) + ck(o, n, a + 1, b);
    logic integer cr{L}(char **o, integer n, integer a, integer b) =
      a >= b ? 0 : (kept(o, n, a) ? 0 : 1) + cr(o, n, a + 1, b);
*/
/*@ ghost
  // ck and cr add up over adjacent ranges and count every entry once (induction by the loop)
  /@ requires 0 <= n;
     assigns \nothing;
     ensures \forall integer a, k, b; 0 <= a <= k <= b <= n ==>
       ck(o, n, a, b) == ck(o, n, a, k) + ck(o, n, k, b) && cr(o, n, a, b) == cr(o, n, a, k) + cr(o, n, k, b);
     ensures \forall integer a, b; 0 <= a <= b <= n ==>
       0 <= ck(o, n, a, b) && 0 <= cr(o, n, a, b) && ck(o, n, a, b) + cr(o, n, a, b) == b - a; @/
  void dedup_facts(char **o, int n) {
    int j = n;
    /@ loop invariant 0 <= j <= n;
       loop invariant \forall integer a, k, b; j <= a <= k <= b <= n ==>
         ck(o, n, a, b) == ck(o, n, a, k) + ck(o, n, k, b) && cr(o, n, a, b) == cr(o, n, a, k) + cr(o, n, k, b);
       loop invariant \forall integer a, b; j <= a <= b <= n ==>
         0 <= ck(o, n, a, b) && 0 <= cr(o, n, a, b) && ck(o, n, a, b) + cr(o, n, a, b) == b - a;
       loop assigns j; loop variant j; @/
    while (j > 0) j--;
  }
*/
"""


def contracts(fixed):
    grown = "grown_fix" if fixed else "grown_up"
    # upstream is proved where its growth fits in an int (outside that: findings/ga-grow-int-overflow.md)
    up_fits = lambda n: "" if fixed else f"""
      requires {grown}(gap->ga_len, gap->ga_growsize, {n}) <= INT_MAX;   // upstream only: see findings"""
    grow_post = lambda n: f"""
      ensures ga_ok(gap) && gap->ga_len == \\old(gap->ga_len);
      ensures gap->ga_maxlen == {grown}(\\old(gap->ga_len), \\old(gap->ga_growsize), {n});
      ensures gap->ga_maxlen - gap->ga_len >= {n};
      ensures \\forall integer i; 0 <= i < \\old(ga_bytes(gap)) ==>
                ((char *)gap->ga_data)[i] == \\old(((char *)gap->ga_data)[i]);
      ensures \\forall integer i; \\old(ga_bytes(gap)) <= i < ga_bytes(gap) ==> ((char *)gap->ga_data)[i] == 0;
      ensures \\base_addr((char *)gap->ga_data) != \\base_addr(a1);
      ensures vp_live == \\old(vp_live) + (\\old(gap->ga_data) == \\null ? 1 : 0);"""
    too_many = lambda cond: "" if not fixed else f"""
    behavior too_many:   // more than INT_MAX items: preserve_exit()
      assumes {cond};
      ensures \\false;"""
    room_ok = "" if fixed else ""
    C = {}
    C["ga_clear"] = r"""requires \valid(gap) && vp_nfree < 4294967296 && vp_live > LONG_MIN;
    assigns gap->ga_data, gap->ga_maxlen, gap->ga_len, vp_live, vp_nfree, vp_freelog[vp_nfree];
    ensures gap->ga_data == \null && gap->ga_maxlen == 0 && gap->ga_len == 0;
    ensures vp_nfree == \old(vp_nfree) + 1 && vp_freelog[\old(vp_nfree)] == \old(gap->ga_data);
    ensures vp_live == \old(vp_live) - (\old(gap->ga_data) == \null ? 0 : 1);"""

    C["ga_clear_strings"] = r"""requires \valid(gap) && 0 <= gap->ga_len;
    requires gap->ga_data != \null ==> \valid_read((void **)gap->ga_data + (0 .. gap->ga_len - 1));
    requires vp_nfree + gap->ga_len + 1 <= 4294967296;
    requires vp_live - gap->ga_len - 1 > LONG_MIN;
    assigns gap->ga_data, gap->ga_maxlen, gap->ga_len, vp_live, vp_nfree, vp_freelog[vp_nfree .. vp_nfree + gap->ga_len];
    ensures gap->ga_data == \null && gap->ga_maxlen == 0 && gap->ga_len == 0;
    behavior items:   // frees every stored pointer in order, then the array
      assumes gap->ga_data != \null;
      ensures vp_nfree == \old(vp_nfree) + \old(gap->ga_len) + 1;
      ensures \forall integer k; 0 <= k < \old(gap->ga_len) ==>
                vp_freelog[\old(vp_nfree) + k] == \old(((void **)gap->ga_data)[k]);
      ensures vp_freelog[\old(vp_nfree) + \old(gap->ga_len)] == \old(gap->ga_data);
      ensures vp_live == \old(vp_live) - \old(nn((void **)gap->ga_data, gap->ga_len)) - 1;
    behavior no_array:
      assumes gap->ga_data == \null;
      ensures vp_nfree == \old(vp_nfree) + 1 && vp_freelog[\old(vp_nfree)] == \null;
      ensures vp_live == \old(vp_live);
    complete behaviors; disjoint behaviors;"""

    C["ga_init"] = r"""requires \valid(gap);
    assigns *gap;
    ensures gap->ga_data == \null && gap->ga_maxlen == 0 && gap->ga_len == 0;
    ensures gap->ga_itemsize == itemsize;
    ensures gap->ga_growsize == (growsize < 1 ? 1 : growsize);"""

    C["ga_set_growsize"] = r"""requires \valid(gap);
    assigns gap->ga_growsize;
    ensures gap->ga_growsize == (growsize < 1 ? 1 : growsize);"""

    C["ga_grow"] = rf"""requires ga_ok(gap) && vp_live < LONG_MAX;
    // a1 (ghost): a live block the caller needs kept apart from the new array
    requires \valid_read(a1) && (gap->ga_data != \null ==> \base_addr(a1) != \base_addr((char *)gap->ga_data));
    exits vp_oom{' || \\old(gap->ga_maxlen - gap->ga_len < n && n > INT_MAX - gap->ga_len)' if fixed else ''};   // out of memory{', or preserve_exit() for too many items' if fixed else ''}
    assigns gap->ga_maxlen, gap->ga_data, vp_live,
            ((char *)\at(gap->ga_data, Post))[0 .. \at(ga_bytes(gap), Post) - 1];
    behavior room:
      assumes gap->ga_maxlen - gap->ga_len >= n;
      ensures gap->ga_maxlen == \old(gap->ga_maxlen) && gap->ga_data == \old(gap->ga_data);
      ensures vp_live == \old(vp_live);
      ensures \forall integer i; 0 <= i < ga_bytes(gap) ==> ((char *)gap->ga_data)[i] == \old(((char *)gap->ga_data)[i]);
    behavior grow:
      assumes gap->ga_maxlen - gap->ga_len < n{' && n <= INT_MAX - gap->ga_len' if fixed else ''};{up_fits('n')}{grow_post('n')}{too_many('gap->ga_maxlen - gap->ga_len < n && n > INT_MAX - gap->ga_len')}
    complete behaviors; disjoint behaviors;"""

    # ga_concat_len, ga_append: arrays of bytes (itemsize 1), as their doc comments say
    def append_post(n, src):
        return f"""
      ensures ga_ok(gap) && gap->ga_len == \\old(gap->ga_len) + {n};
      ensures gap->ga_maxlen == (\\old(gap->ga_maxlen - gap->ga_len) >= {n} ? \\old(gap->ga_maxlen)
                                 : {grown}(\\old(gap->ga_len), \\old(gap->ga_growsize), {n}));
      ensures \\forall integer i; 0 <= i < \\old(gap->ga_len) ==>
                ((char *)gap->ga_data)[i] == \\old(((char *)gap->ga_data)[i]);
      ensures {src};
      ensures \\forall integer i; \\old(gap->ga_len) + {n} <= i < ga_bytes(gap) ==>
                ((char *)gap->ga_data)[i] == (i < \\old(ga_bytes(gap)) ? \\old(((char *)gap->ga_data)[i]) : 0);
      ensures vp_live == \\old(vp_live) + (\\old(gap->ga_data) == \\null && \\old(gap->ga_maxlen - gap->ga_len) < {n} ? 1 : 0);"""
    unchanged = r"""ensures gap->ga_len == \old(gap->ga_len) && gap->ga_maxlen == \old(gap->ga_maxlen)
              && gap->ga_data == \old(gap->ga_data) && vp_live == \old(vp_live);"""
    up_fits_if = lambda n: "" if fixed else f"""
      requires gap->ga_maxlen - gap->ga_len < {n} ==> grown_up(gap->ga_len, gap->ga_growsize, {n}) <= INT_MAX;   // upstream only"""

    C["ga_concat_len"] = rf"""requires ga_ok(gap) && gap->ga_itemsize == 1 && vp_live < LONG_MAX;
    requires (void *)gap != capture_ga;   // emsg() appends to the capture array (see stubs)
    requires \valid_read(s + (0 .. len - 1));
    requires \base_addr(s) != \base_addr((char *)gap->ga_data);   // "may not overlap with the growing array"
    requires \separated(s + (0 .. len - 1), gap);
    exits vp_oom;   // only when memory runs out
    assigns gap->ga_len, gap->ga_maxlen, gap->ga_data, vp_live,
            ((char *)\at(gap->ga_data, Post))[0 .. \at(ga_bytes(gap), Post) - 1];
    behavior empty:
      assumes len == 0;
      {unchanged}
    behavior too_long:   // emsg(e_resulting_text_too_long)
      assumes len > 0 && len > INT_MAX - gap->ga_len;
      {unchanged}
    behavior append:
      assumes 0 < len <= INT_MAX - gap->ga_len;{up_fits_if('len')}{append_post('len', "\\forall integer i; 0 <= i < len ==> ((char *)gap->ga_data)[\\old(gap->ga_len) + i] == \\old(s[i])")}
    complete behaviors; disjoint behaviors;"""

    C["ga_concat"] = rf"""requires ga_ok(gap) && gap->ga_itemsize == 1 && vp_live < LONG_MAX;
    requires (void *)gap != capture_ga;   // emsg() appends to the capture array (see stubs)
    requires s != \null ==> str_len((char *)s, n);
    requires s != \null ==> \base_addr(s) != \base_addr((char *)gap->ga_data) && \separated(s + (0 .. n), gap);
    exits vp_oom;   // only when memory runs out
    assigns gap->ga_len, gap->ga_maxlen, gap->ga_data, vp_live,
            ((char *)\at(gap->ga_data, Post))[0 .. \at(ga_bytes(gap), Post) - 1];
    behavior nothing:   // NULL or the empty string
      assumes s == \null || n == 0;
      {unchanged}
    behavior too_long:
      assumes s != \null && n > 0 && n > INT_MAX - gap->ga_len;
      {unchanged}
    behavior append:   // the bytes of s, without its NUL
      assumes s != \null && 0 < n <= INT_MAX - gap->ga_len;{up_fits_if('n')}{append_post('n', "\\forall integer i; 0 <= i < n ==> ((char *)gap->ga_data)[\\old(gap->ga_len) + i] == \\old(s[i])")}
    complete behaviors; disjoint behaviors;"""

    full = "gap->ga_maxlen == gap->ga_len"
    C["ga_append"] = rf"""requires ga_ok(gap) && gap->ga_itemsize == 1 && vp_live < LONG_MAX;
    exits vp_oom{' || \\old(gap->ga_maxlen == gap->ga_len && gap->ga_len == INT_MAX)' if fixed else ''};
    assigns gap->ga_len, gap->ga_maxlen, gap->ga_data, vp_live,
            ((char *)\at(gap->ga_data, Post))[0 .. \at(ga_bytes(gap), Post) - 1];
    behavior append:
      assumes {'!(' + full + ' && gap->ga_len == INT_MAX)' if fixed else '\\true'};{up_fits_if('1')}{append_post('1', "((char *)gap->ga_data)[\\old(gap->ga_len)] == (char)c")}{too_many(full + ' && gap->ga_len == INT_MAX')}
    {'complete behaviors; disjoint behaviors;' if fixed else ''}"""

    C["ga_append_via_ptr"] = rf"""requires ga_ok(gap) && vp_live < LONG_MAX;
    requires 1 <= item_size <= gap->ga_itemsize;   // a different size is only logged (WLOG); a larger one would overrun
    exits vp_oom{' || \\old(gap->ga_maxlen == gap->ga_len && gap->ga_len == INT_MAX)' if fixed else ''};
    assigns gap->ga_len, gap->ga_maxlen, gap->ga_data, vp_live,
            ((char *)\at(gap->ga_data, Post))[0 .. \at(ga_bytes(gap), Post) - 1];
    behavior append:   // one more item; returns its address (its bytes are zero if the array grew)
      assumes {'!(' + full + ' && gap->ga_len == INT_MAX)' if fixed else '\\true'};{up_fits_if('1')}
      ensures ga_ok(gap) && gap->ga_len == \old(gap->ga_len) + 1;
      ensures gap->ga_maxlen == (\old(gap->ga_maxlen) > \old(gap->ga_len) ? \old(gap->ga_maxlen)
                                 : {grown}(\old(gap->ga_len), \old(gap->ga_growsize), 1));
      ensures (char *)\result == (char *)gap->ga_data + item_size * \old(gap->ga_len);
      ensures \valid((char *)\result + (0 .. item_size - 1));
      ensures \forall integer i; 0 <= i < \old(ga_bytes(gap)) ==>
                ((char *)gap->ga_data)[i] == \old(((char *)gap->ga_data)[i]);
      ensures \forall integer i; \old(ga_bytes(gap)) <= i < ga_bytes(gap) ==> ((char *)gap->ga_data)[i] == 0;
      ensures vp_live == \old(vp_live) + (\old(gap->ga_data) == \null && \old(gap->ga_maxlen) == \old(gap->ga_len) ? 1 : 0);{too_many(full + ' && gap->ga_len == INT_MAX')}
    {'complete behaviors; disjoint behaviors;' if fixed else ''}"""
    S = "((char **)gap->ga_data)"
    T = "total(Ls, m, gap->ga_len)"
    C["ga_concat_strings"] = rf"""requires \valid_read(gap) && 0 <= gap->ga_len && vp_live < LONG_MAX;
    requires \valid_read({S} + (0 .. gap->ga_len - 1)) && \valid_read(Ls + (0 .. gap->ga_len - 1));
    requires \forall integer k; 0 <= k < gap->ga_len ==> str_len({S}[k], Ls[k]) && Ls[k] < PTRDIFF_MAX;
    requires str_len((char *)sep, m) && m < PTRDIFF_MAX;{'' if fixed else f"""
    requires gap->ga_len > 0 ==> {T} <= SIZE_MAX;   // upstream only: the sum does not wrap (see findings)"""}
    exits vp_oom || \old(gap->ga_len > 0 && {T} >= SIZE_MAX);   // out of memory, or the length does not fit
    assigns vp_live, \at(\result, Post)[0 .. (gap->ga_len > 0 ? {T} : 0)];   // only the new string
    behavior empty:   // a new empty string
      assumes gap->ga_len == 0;
      ensures \valid(\result) && \result[0] == 0 && vp_live == \old(vp_live) + 1;
    behavior join:    // string 0, sep, string 1, sep, ..., string n-1, then NUL
      assumes gap->ga_len > 0 && {T} < SIZE_MAX;
      ensures vp_live == \old(vp_live) + 1;
      // the new string overlaps none of the inputs
      ensures \base_addr(\result) != \base_addr((char *)\old(gap->ga_data)) && \base_addr(\result) != \base_addr((char *)sep)
              && \forall integer k; 0 <= k < \old(gap->ga_len) ==> \base_addr(\result) != \base_addr(\old({S}[k]));
      ensures \valid(\result + (0 .. \old({T}))) && \result[\old({T})] == 0;
      ensures \forall integer k, j; 0 <= k < \old(gap->ga_len) && 0 <= j < \old(Ls[k]) ==>
                \result[\old(off(Ls, m, k)) + j] == \old({S}[k][j]);
      ensures \forall integer k, j; 0 <= k < \old(gap->ga_len) - 1 && 0 <= j < m ==>
                \result[\old(off(Ls, m, k) + Ls[k]) + j] == \old(sep[j]);
    behavior too_big:   // the result does not fit in a size_t: preserve_exit()
      assumes gap->ga_len > 0 && {T} >= SIZE_MAX;
      ensures \false;
    complete behaviors; disjoint behaviors;"""
    D, N = "((char **)gap->ga_data)", "gap->ga_len"
    C["ga_remove_duplicate_strings"] = rf"""requires \valid(gap) && 0 <= {N};
    requires \valid({D} + (0 .. {N} - 1)) && \base_addr(gap) != \base_addr({D});
    requires \forall integer k; 0 <= k < {N} ==> is_str({D}[k]);
    requires vp_nfree + {N} <= 4294967296 && vp_live - {N} > LONG_MIN;
    assigns gap->ga_len, {D}[0 .. {N} - 1], vp_live, vp_nfree, vp_freelog[vp_nfree .. vp_nfree + {N} - 1];
    // the sorted strings, each one kept unless it is path_equal to the one before it
    ensures gap->ga_len == \old(ck({D}, {N}, 0, {N}));
    ensures \forall integer k; 0 <= k < \old({N}) && \old(kept({D}, {N}, k)) ==>
              {D}[\old(ck({D}, {N}, 0, k))] == \old(vp_sorted({D}, {N}, k));
    // the dropped ones are freed (from the last to the first), nothing else is
    ensures vp_nfree == \old(vp_nfree) + \old(cr({D}, {N}, 0, {N}));
    ensures \forall integer k; 0 <= k < \old({N}) && !\old(kept({D}, {N}, k)) ==>
              vp_freelog[\old(vp_nfree) + \old(cr({D}, {N}, k + 1, {N}))] == \old(vp_sorted({D}, {N}, k));
    ensures vp_live == \old(vp_live) - \old(cr({D}, {N}, 0, {N}));"""
    return C


def annotations(fixed):
    """(kind, anchor, annotation): 'before' = own line above the anchor line,
    'after' = right after the anchor text, 'inline' = right before it."""
    A = {}
    A["ga_grow"] = [
        ("after", "void ga_grow(garray_T *gap, int n)", "ghost (char *a1)"),
        ("after", "char *pp = xrealloc(gap->ga_data, new_size)", "ghost (old_size, (char *)gap, a1)"),
        ("before", "  memset(pp + old_size, 0, new_size - old_size);",
         r"assert new_size == gap->ga_itemsize * new_maxlen && old_size == gap->ga_itemsize * gap->ga_maxlen;"),
        ("before", "  gap->ga_maxlen = new_maxlen;",
         r"assert \forall integer i; old_size <= i < new_size ==> pp[i] == 0;"),
    ]
    A["ga_clear_strings"] = [
        ("inline", "for (int i = 0; i < _gap->ga_len; i++)", r"""loop invariant 0 <= i <= _gap->ga_len && _gap == gap;
      loop invariant vp_nfree == \at(vp_nfree, Pre) + i;
      loop invariant \forall integer k; 0 <= k < i ==>
        vp_freelog[\at(vp_nfree, Pre) + k] == \at(((void **)gap->ga_data)[k], Pre);
      loop invariant 0 <= nn((void **)_gap->ga_data, i) <= i;
      loop invariant vp_live == \at(vp_live, Pre) - nn((void **)_gap->ga_data, i);
      loop assigns i, vp_nfree, vp_live, vp_freelog[\at(vp_nfree, Pre) .. \at(vp_nfree, Pre) + _gap->ga_len - 1];
      loop variant _gap->ga_len - i;"""),
    ]
    A["ga_concat"] = [("after", "void ga_concat(garray_T *gap, const char *restrict s)", "ghost (size_t n)")]
    S = "((char **)gap->ga_data)"
    A["ga_concat_strings"] = [
        ("after", "char *ga_concat_strings(const garray_T *gap, const char *sep)", "ghost (size_t *Ls, size_t m)"),
        ("after", 'return xstrdup("")', "ghost (0)"),
        ("before", "  size_t len = 0;", "ghost concat_facts(Ls, m, nelem);"),
        ("before", "  for (size_t i = 0; i < nelem; i++) {", r"""loop invariant 0 <= i <= nelem && len == sumL(Ls, i);
      loop assigns i, len; loop variant nelem - i;"""),
        ("before", "  for (size_t i = 0; i < nelem - 1; i++) {", rf"""loop invariant 0 <= i <= nelem - 1 && s == ret + off(Ls, m, i);
      loop invariant \forall integer k, j; 0 <= k < i && 0 <= j < Ls[k] ==> ret[off(Ls, m, k) + j] == \at({S}[k][j], Pre);
      loop invariant \forall integer k, j; 0 <= k < i && 0 <= j < m ==> ret[off(Ls, m, k) + Ls[k] + j] == \at(sep[j], Pre);
      loop assigns i, s, ret[0 .. len];
      loop variant nelem - 1 - i;"""),
        ("after", "s = xstpcpy(s, strings[i])", "ghost (Ls[i])"),
        ("after", "s = xstpcpy(s, sep)", "ghost (m)"),
    ] + ([] if not fixed else [
        ("before", "  len += (nelem - 1) * seplen;",
         r"assert seplen == m && (nelem - 1) * seplen <= SIZE_MAX - len;"),
        ("after", "    if (slen > SIZE_MAX - len) {",
         r"assert slen == Ls[i] && sumL(Ls, i + 1) > SIZE_MAX && total(Ls, m, nelem) >= SIZE_MAX;"),
        ("after", "  if (seplen != 0 && nelem - 1 > (SIZE_MAX - len) / seplen) {",
         r"assert total(Ls, m, nelem) >= SIZE_MAX;"),
        ("after", "  if (seplen != 0 && nelem - 1 > (SIZE_MAX - len) / seplen) {",
         r"assert seplen == m && len == sumL(Ls, nelem);"),
        ("after", "  if (seplen != 0 && nelem - 1 > (SIZE_MAX - len) / seplen) {",
         r"assert (nelem - 1) * seplen > SIZE_MAX - len;"),
        ("before", "  char *const ret = xmallocz(len);", r"assert len == total(Ls, m, nelem);"),
    ]) + [
        ("after", "strcpy(s, strings[nelem - 1])", "ghost (Ls[nelem - 1])"),
        ("after", "xmallocz(len)", "ghost ((char **)strings, nelem, (char *)sep)"),
    ]
    A["ga_concat_len"] = [
        ("after", "ga_grow(gap, (int)len)", "ghost ((char *)s)"),
        ("before", "  char *data = gap->ga_data;", r"assert \base_addr(s) != \base_addr((char *)gap->ga_data);"),
        ("before", "  char *data = gap->ga_data;", r"assert \forall integer i; 0 <= i < len ==> s[i] == \at(s[i], Pre);"),
        ("before", "  char *data = gap->ga_data;",
         r"assert \forall integer i; 0 <= i < gap->ga_len ==> ((char *)gap->ga_data)[i] == \at(((char *)gap->ga_data)[i], Pre);"),
    ]
    A["ga_append"] = [
        ("after", "ga_grow(gap, 1)", "ghost ((char *)gap)"),
        ("inline", "((char *)(gap)->ga_data)[(gap)->ga_len] = (char)((c) - ((c) > 127 ? 256 : 0));",
         r"assert \forall integer i; 0 <= i < gap->ga_len ==> ((char *)gap->ga_data)[i] == \at(((char *)gap->ga_data)[i], Pre);"),
    ]
    A["ga_append_via_ptr"] = [
        ("after", "ga_grow(gap, 1)", "ghost ((char *)gap)"),
        ("before", "  return ((char *)gap->ga_data) + (item_size * (size_t)gap->ga_len++);",
         r"assert \forall integer i; \at(ga_bytes(gap), Pre) <= i < ga_bytes(gap) ==> ((char *)gap->ga_data)[i] == 0;"),
    ]
    N0, nf0, lv0 = r"\at(gap->ga_len, Pre)", r"\at(vp_nfree, Pre)", r"\at(vp_live, Pre)"
    S = lambda k: rf"vp_sorted{{Pre}}(fnames, {N0}, {k})"
    KEPT = lambda k: rf"kept{{Pre}}(fnames, {N0}, {k})"
    CK = lambda a, b: rf"ck{{Pre}}(fnames, {N0}, {a}, {b})"
    CR = lambda a, b: rf"cr{{Pre}}(fnames, {N0}, {a}, {b})"
    A["ga_remove_duplicate_strings"] = [
        ("before", "  sort_strings(fnames, gap->ga_len);", "ghost dedup_facts(fnames, gap->ga_len);"),
        ("before", "  for (int i = gap->ga_len - 1; i > 0; i--) {", rf"""loop invariant -1 <= i <= {N0} - 1 && fnames == \at(gap->ga_data, Pre);
      loop invariant gap->ga_len == i + 1 + {CK('i + 1', N0)};
      loop invariant \forall integer k; 0 <= k <= i ==> fnames[k] == {S('k')};
      loop invariant \forall integer k; i < k < {N0} && {KEPT('k')} ==> fnames[i + 1 + {CK('i + 1', 'k')}] == {S('k')};
      loop invariant vp_nfree == {nf0} + {CR('i + 1', N0)} && vp_live == {lv0} - {CR('i + 1', N0)};
      loop invariant \forall integer k; i < k < {N0} && !{KEPT('k')} ==> vp_freelog[{nf0} + {CR('k + 1', N0)}] == {S('k')};
      loop assigns i, gap->ga_len, fnames[0 .. {N0} - 1], vp_live, vp_nfree, vp_freelog[{nf0} .. {nf0} + {N0} - 1];
      loop variant i;"""),
        ("before", "      for (int j = i + 1; j < gap->ga_len; j++) {", r"""loop invariant i + 1 <= j <= gap->ga_len;
        loop invariant \forall integer p; 0 <= p < i ==> fnames[p] == \at(fnames[p], LoopEntry);
        loop invariant \forall integer p; i <= p < j - 1 ==> fnames[p] == \at(fnames[p + 1], LoopEntry);
        loop invariant \forall integer p; j - 1 <= p < gap->ga_len ==> fnames[p] == \at(fnames[p], LoopEntry);
        loop assigns j, fnames[i .. gap->ga_len - 2];
        loop variant gap->ga_len - j;"""),
    ]
    return A
