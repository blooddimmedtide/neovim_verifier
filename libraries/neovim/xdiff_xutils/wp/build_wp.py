"""Annotated copy of the loop functions of src/xdiff/xutils.c for Frama-C WP.
Usage: python3 -I build_wp.py <xutils.c> <out.c>

The functions are copied verbatim; ACSL is inserted at anchors (each anchor must occur
exactly once). Tool patches (declared in ../CLAIM.md), text only:
  - the headers are replaced by the prelude below (the same types and macros);
  - XDL_ISSPACE(c) calls the model xsp(c) (isspace((unsigned char)c), see the prelude);
  - xdl_free(p) calls the model free_log(p), which records p.
"""
import sys
src = open(sys.argv[1]).read()

def piece(start, end):
    a = src.index(start); b = src.index(end, a)
    return src[a:b]

PRELUDE = r'''
#include <stddef.h>
#include <limits.h>
typedef struct s_mmfile { char *ptr; int size; } mmfile_t;
typedef struct s_chanode { struct s_chanode *next; long icurr; } chanode_t;
typedef struct s_chastore { chanode_t *head, *tail; long isize, nsize; chanode_t *ancur; chanode_t *sncur; long scurr; } chastore_t;
#define XDF_IGNORE_WHITESPACE (1 << 1)
#define XDF_IGNORE_WHITESPACE_CHANGE (1 << 2)
#define XDF_IGNORE_WHITESPACE_AT_EOL (1 << 3)
#define XDF_IGNORE_CR_AT_EOL (1 << 4)
#define XDF_WHITESPACE_FLAGS (XDF_IGNORE_WHITESPACE | XDF_IGNORE_WHITESPACE_CHANGE | XDF_IGNORE_WHITESPACE_AT_EOL | XDF_IGNORE_CR_AT_EOL)

/*@ // ---- isspace. XDL_ISSPACE(c) is isspace((unsigned char)c). C says which ASCII bytes are
    // spaces; for 128..255 it depends on the locale (LC_CTYPE), modelled as an unknown but
    // fixed set: Neovim does not change the locale during a diff.
    axiomatic Locale { predicate loc_space(integer c); }
    predicate sp(integer c) = (9 <= c <= 13) || c == 32 || (128 <= c <= 255 && loc_space(c));
    logic integer B{L}(char *l, integer i) = (unsigned char)l[i];
    predicate S{L}(char *l, integer i) = sp(B(l, i));
    // proved facts the provers need: a pointer is its base plus its offset; '\n' as unsigned
    lemma shift_back: \forall char *a, *p; \base_addr(a) == \base_addr(p) ==> a + (p - a) == p;
    lemma nl_char: \forall char c; ((unsigned char)c == 10) <==> (c == 10);
    lemma cr_char: \forall char c; ((unsigned char)c == 13) <==> (c == 13);
*/
/*@ assigns \nothing; ensures (\result != 0) <==> sp((unsigned char)c); */
int xsp(int c);
#define XDL_ISSPACE(c) xsp((c))

/*@ // ---- libc, as C specifies it
    requires \valid_read((char *)s + (0 .. n - 1));
    assigns \nothing;
    ensures \result == \null ==> (\forall integer k; 0 <= k < n ==> B((char *)s, k) != (unsigned char)c);
    ensures \result != \null ==> (\exists integer k; 0 <= k < n && \result == (char *)s + k &&
              B((char *)s, k) == (unsigned char)c && (\forall integer j; 0 <= j < k ==> B((char *)s, j) != (unsigned char)c));
*/
void *memchr(const void *s, int c, size_t n);
/*@ requires \valid_read((char *)a + (0 .. n - 1)) && \valid_read((char *)b + (0 .. n - 1));
    assigns \nothing;
    ensures (\result == 0) <==> (\forall integer k; 0 <= k < n ==> ((char *)a)[k] == ((char *)b)[k]);
*/
int memcmp(const void *a, const void *b, size_t n);

// ---- the model of xdl_free (xfree): it records each pointer it is given, in order
//@ ghost int nfreed;
//@ ghost chanode_t *freed_log[1000000];
/*@ requires 0 <= nfreed < 1000000;
    assigns nfreed, freed_log[nfreed];
    ensures nfreed == \old(nfreed) + 1 && freed_log[\old(nfreed)] == p; */
void free_log(void *p);
#define xdl_free(p) free_log((p))

/*@ // ---- lists of blocks: nth(p, k) is the k-th node from p
    logic chanode_t *nth{L}(chanode_t *p, integer k) = k <= 0 ? p : nth(p, k - 1)->next;
    predicate list{L}(chanode_t *p, integer n) =
      n >= 0 && nth(p, n) == \null && \forall integer k; 0 <= k < n ==> \valid(nth(p, k));
*/

/*@ // ---- lines. A line is l[0 .. s-1]; the mode is the strongest whitespace flag:
    // 1 = -w (ignore all whitespace), 2 = -b (ignore changes in amount of whitespace, and
    // whitespace at the end), 3 = --ignore-space-at-eol, 4 = --ignore-cr-at-eol, 0 = none.
    logic integer mode(integer f) =
      (f & 2) != 0 ? 1 : (f & 4) != 0 ? 2 : (f & 8) != 0 ? 3 : (f & 16) != 0 ? 4 : 0;
    // length without the trailing whitespace
    logic integer tr{L}(char *l, integer s) = s <= 0 ? 0 : S(l, s - 1) ? tr(l, s - 1) : s;
    // length without the line end "\n" or "\r\n" (a CR on an incomplete line stays)
    logic integer cre{L}(char *l, integer s) =
      (s > 0 && B(l, s - 1) == 10) ? ((s > 1 && B(l, s - 2) == 13) ? s - 2 : s - 1) : s;
    // the line as the mode sees it: the bytes i that count (el), and their value (ev):
    // -w: every non-space; -b: every non-space before the trailing whitespace, and one ' '
    // for each run of whitespace before it; no flag: every byte before a newline (hash).
    predicate el{L}(char *l, integer s, integer m, integer i) =
      m == 1 ? !S(l, i) :
      m == 2 ? (i < tr(l, s) && (!S(l, i) || i == 0 || !S(l, i - 1))) :
      m == 3 ? i < tr(l, s) :
      m == 4 ? i < cre(l, s) :
      (i < s && B(l, i) != 10);
    logic integer ev{L}(char *l, integer m, integer i) = (m == 2 && S(l, i)) ? 32 : l[i];
    logic integer cnt{L}(char *l, integer s, integer m, integer i) =
      i <= 0 ? 0 : cnt(l, s, m, i - 1) + (el(l, s, m, i - 1) ? 1 : 0);
    // two lines are equal in mode m (1 or 2): same number of counted bytes, equal in order
    predicate eqm{L}(char *a, integer sa, char *b, integer sb, integer m) =
      cnt(a, sa, m, sa) == cnt(b, sb, m, sb) &&
      \forall integer i, j; 0 <= i < sa ==> 0 <= j < sb ==> el(a, sa, m, i) ==> el(b, sb, m, j) ==>
        cnt(a, sa, m, i) == cnt(b, sb, m, j) ==> ev(a, m, i) == ev(b, m, j);
    predicate same{L}(char *a, char *b, integer n) = \forall integer k; 0 <= k < n ==> a[k] == b[k];
    predicate match{L}(char *a, integer sa, char *b, integer sb, integer f) =
      mode(f) == 0 ? (sa == sb && same(a, b, sa)) :
      mode(f) == 1 || mode(f) == 2 ? eqm(a, sa, b, sb, mode(f)) :
      mode(f) == 3 ? (tr(a, sa) == tr(b, sb) && same(a, b, tr(a, sa))) :
      (cre(a, sa) == cre(b, sb) && same(a, b, cre(a, sa)));
*/
'''

out = [PRELUDE]
import os, subprocess
out.append(subprocess.check_output([sys.executable, "-I", os.path.join(os.path.dirname(os.path.abspath(__file__)), "lemmas.py"), "--acsl", "ws_bits"], text=True))

# ---------------------------------------------------------------- xdl_cha_free
f = piece('void xdl_cha_free(chastore_t *cha) {', 'void *xdl_cha_alloc')
f = f.replace('void xdl_cha_free(chastore_t *cha) {', '''/*@ // frees every block of the list, each once, in list order (nothing else)
    requires \\valid_read(cha) && list(cha->head, n) && 0 <= nfreed && nfreed + n < 1000000;
    assigns nfreed, freed_log[nfreed .. nfreed + n - 1];
    ensures nfreed == \\old(nfreed) + n;
    ensures \\forall integer k; 0 <= k < n ==> freed_log[\\old(nfreed) + k] == nth{Pre}(cha->head, k);
*/
void xdl_cha_free(chastore_t *cha) /*@ ghost (int n) */ {''', 1)
f = f.replace('\tfor (cur = cha->head;', '''\t/*@ loop invariant 0 <= nfreed - \\at(nfreed, Pre) <= n && cur == nth(cha->head, nfreed - \\at(nfreed, Pre));
\t    loop invariant \\forall integer k; 0 <= k < nfreed - \\at(nfreed, Pre) ==> freed_log[\\at(nfreed, Pre) + k] == nth(cha->head, k);
\t    loop assigns cur, tmp, nfreed, freed_log[\\at(nfreed, Pre) .. \\at(nfreed, Pre) + n - 1];
\t    loop variant n - (nfreed - \\at(nfreed, Pre)); */
\tfor (cur = cha->head;''', 1)
out.append(f)

# ---------------------------------------------------------------- xdl_cha_init / xdl_cha_alloc
out.append(r"""
/*@ // xdl_cha_alloc is proved with CBMC (../cbmc/h_cha_alloc) from SLOTS, which needs no product.
    // This lemma is the arithmetic around it: the store invariant (nsize = k * isize,
    // icurr = j * isize, 0 <= j <= k) gives SLOTS, "icurr == nsize" is "j == k", and both kinds
    // of step (icurr + isize, or a new block with icurr = isize) keep the invariant.
    predicate slots(integer icurr, integer nsize, integer isize) =
      0 <= icurr <= nsize && (icurr == nsize || icurr + isize <= nsize);
    lemma cha_slots: \forall integer isize, k, j; isize >= 1 && k >= 1 && 0 <= j <= k ==>
      slots(j * isize, k * isize, isize) && (j * isize == k * isize <==> j == k) && k * isize >= isize &&
      (j < k ==> j * isize + isize == (j + 1) * isize && j + 1 <= k) && isize == 1 * isize;
*/
""")
f = piece('int xdl_cha_init(chastore_t *cha, long isize, long icount) {', 'void xdl_cha_free')
f = f.replace('int xdl_cha_init(chastore_t *cha, long isize, long icount) {', r"""/*@ // an empty store of items of isize bytes, icount items per block. The callers pass
    // isize = sizeof of a struct and icount = n / 4 + 1; the block size must fit in a long.
    requires \valid(cha) && isize >= 1 && icount >= 1 && isize * icount <= LONG_MAX;
    assigns *cha;
    ensures \result == 0 && cha->head == \null && cha->tail == \null && cha->ancur == \null && cha->sncur == \null;
    ensures cha->isize == isize && cha->nsize == icount * isize && cha->scurr == 0;
*/
int xdl_cha_init(chastore_t *cha, long isize, long icount) {""", 1)
out.append(f)
# ---------------------------------------------------------------- xdl_guess_lines
f = piece('long xdl_guess_lines(mmfile_t *mf, long sample) {', 'int xdl_blankline')
LOGIC_GL = r'''
/*@ // end of the line that starts at i, in a buffer of n bytes: after its '\n', or n
    logic integer endl{L}(char *d, integer n, integer i) = i >= n ? n : B(d, i) == 10 ? i + 1 : endl(d, n, i + 1);
    // where line k starts (k = 0, 1, ...): the first k lines are the bytes before it
    logic integer posk{L}(char *d, integer n, integer k) = k <= 0 ? 0 : endl(d, n, posk(d, n, k - 1));
    // how many of the first `sample` lines exist
    logic integer nlines{L}(char *d, integer n, integer sample, integer k) =
      (k >= sample || posk(d, n, k) >= n) ? k : nlines(d, n, sample, k + 1);
*/
'''
f = f.replace('long xdl_guess_lines(mmfile_t *mf, long sample) {', '''/*@ // an estimate of the number of lines: the size divided by the mean length of the first
    // `sample` lines (+ 1); 1 for an empty file, nl + 1 when the sample has nl lines and no bytes
    requires \\valid_read(mf) && 0 <= mf->size && (mf->ptr == \\null || \\valid_read(mf->ptr + (0 .. mf->size - 1)));
    requires 0 <= sample <= LONG_MAX - 1;
    assigns \\nothing;
    ensures mf->ptr == \\null ==> \\result == 1;
    ensures mf->ptr != \\null ==> \\let nl = nlines(mf->ptr, mf->size, sample, 0); \\let ts = posk(mf->ptr, mf->size, nl);
       \\result == ((nl != 0 && ts != 0) ? mf->size / (ts / nl) + 1 : nl + 1);
*/
long xdl_guess_lines(mmfile_t *mf, long sample) {''', 1)
f = f.replace('\t\tfor (top = data + size; nl < sample && cur < top; ) {', '''\t\t/*@ loop invariant top == data + size && size == mf->size && data == mf->ptr;
\t\t    loop invariant 0 <= nl <= sample && data <= cur <= top && cur - data >= nl;
\t\t    loop invariant cur == data + posk(data, size, nl) && nlines(data, size, sample, 0) == nlines(data, size, sample, nl);
\t\t    loop assigns nl, cur;
\t\t    loop variant top - cur; */
\t\tfor (top = data + size; nl < sample && cur < top; ) {''', 1)
f = f.replace('\t\t\tnl++;\n', '\t\t\t//@ ghost char const *c0 = cur;\n\t\t\tnl++;\n', 1)
# proof only (ghost): the line that started at c0 ends at cur, one step of endl per byte
GHOST = r'''				cur++;
			/*@ ghost
			  long g = (cur - data > c0 - data && cur[-1] == '\n') ? cur - data - 1 : cur - data;
			  /@ assert same_base: \forall integer j; c0 - data <= j < cur - data ==> B(data, j) == B((char *)c0, j - (c0 - data)); @/
			  /@ assert no_nl: \forall integer j; c0 - data <= j < g ==> B((char *)c0, j - (c0 - data)) != 10; @/
			  /@ loop invariant c0 - data <= g <= cur - data && endl(data, size, g) == cur - data;
			     loop invariant \forall integer j; c0 - data <= j < g ==> B(data, j) != 10;
			     loop assigns g; loop variant g; @/
			  while (g > c0 - data) g--;
			*/
		}'''
assert f.count('\t\t\t\tcur++;\n\t\t}') == 1
f = f.replace('\t\t\t\tcur++;\n\t\t}', GHOST, 1)
out.append(piece('void *xdl_mmfile_first(mmfile_t *mmf, long *size)', 'int xdl_cha_init').replace(
    'void *xdl_mmfile_first(mmfile_t *mmf, long *size)', '''/*@ requires \\valid_read(mmf) && \\valid(size); assigns *size;
    ensures *size == mmf->size && \\result == mmf->ptr; */
void *xdl_mmfile_first(mmfile_t *mmf, long *size)''', 1).replace(
    'long xdl_mmfile_size(mmfile_t *mmf)', '''/*@ requires \\valid_read(mmf); assigns \\nothing; ensures \\result == mmf->size; */
long xdl_mmfile_size(mmfile_t *mmf)''', 1))
out.append(LOGIC_GL)
out.append(f)

# ---------------------------------------------------------------- xdl_blankline
f = piece('int xdl_blankline(const char *line, long size, long flags)', '/*\n * ')
f = f.replace('int xdl_blankline(const char *line, long size, long flags)', '''/*@ // blank: with a whitespace flag, nothing but whitespace; without, an empty line ("" or "\\n")
    requires 0 <= size && \\valid_read(line + (0 .. size - 1));
    assigns \\nothing;
    ensures (flags & XDF_WHITESPACE_FLAGS) != 0 ==> (\\result != 0 <==> \\forall integer i; 0 <= i < size ==> S((char *)line, i));
    ensures (flags & XDF_WHITESPACE_FLAGS) == 0 ==> (\\result != 0 <==> (size == 0 || (size == 1 && B((char *)line, 0) == 10)));
*/
int xdl_blankline(const char *line, long size, long flags)''', 1)
f = f.replace('\tfor (i = 0; i < size && XDL_ISSPACE(line[i]); i++)', '''\t/*@ loop invariant 0 <= i <= size && \\forall integer k; 0 <= k < i ==> S((char *)line, k);
\t    loop assigns i; loop variant size - i; */
\tfor (i = 0; i < size && XDL_ISSPACE(line[i]); i++)''', 1)
out.append(f)


# ---------------------------------------------------------------- xdl_recmatch
LEMMAS = r"""
/*@ predicate allsp{L}(char *l, integer a, integer b) = \forall integer j; a <= j < b ==> S(l, j); */
/*@ ghost
  // proof only: what tr is (by induction over the length)
  /@ requires 0 <= s; assigns \nothing;
     ensures 0 <= tr(l, s) <= s && allsp(l, tr(l, s), s) && (tr(l, s) > 0 ==> !S(l, tr(l, s) - 1)); @/
  void lem_tr(char *l, long s) {
    long i = 0;
    /@ loop invariant 0 <= i <= s && 0 <= tr(l, i) <= i && allsp(l, tr(l, i), i) && (tr(l, i) > 0 ==> !S(l, tr(l, i) - 1));
       loop assigns i; loop variant s - i; @/
    while (i < s) i++;
  }
*/
/*@ ghost
  // proof only: cnt counts (by induction): it never decreases, grows at each counted byte,
  // and stays the same over bytes that do not count
  /@ requires 0 <= s; assigns \nothing;
     ensures cnt(l, s, m, 0) == 0;
     ensures \forall integer a, b; 0 <= a <= b <= s ==> cnt(l, s, m, a) <= cnt(l, s, m, b);
     ensures \forall integer a, b; 0 <= a < b <= s ==> el(l, s, m, a) ==> cnt(l, s, m, a) < cnt(l, s, m, b);
     ensures \forall integer a, b; 0 <= a <= b <= s ==> (\forall integer j; a <= j < b ==> !el(l, s, m, j)) ==> cnt(l, s, m, a) == cnt(l, s, m, b); @/
  void lem_cnt(char *l, long s, int m) {
    long b = 0;
    /@ loop invariant 0 <= b <= s;
       loop invariant \forall integer a, c; 0 <= a <= c <= b ==> cnt(l, s, m, a) <= cnt(l, s, m, c);
       loop invariant \forall integer a, c; 0 <= a < c <= b ==> el(l, s, m, a) ==> cnt(l, s, m, a) < cnt(l, s, m, c);
       loop invariant \forall integer a, c; 0 <= a <= c <= b ==> (\forall integer j; a <= j < c ==> !el(l, s, m, j)) ==> cnt(l, s, m, a) == cnt(l, s, m, c);
       loop assigns b; loop variant s - b; @/
    while (b < s) b++;
  }
*/
/*@ ghost
  // proof only: two lines with the same bytes count the same
  /@ requires 0 <= s; assigns \nothing;
     ensures same(a, b, s) ==> tr(a, s) == tr(b, s) && cre(a, s) == cre(b, s);
     ensures same(a, b, s) ==> \forall integer i; 0 <= i <= s ==> cnt(a, s, m, i) == cnt(b, s, m, i); @/
  void lem_cnt_same(char *a, char *b, long s, int m) {
    long t = 0;
    /@ loop invariant 0 <= t <= s && (same(a, b, s) ==> \forall integer k; 0 <= k <= t ==> tr(a, k) == tr(b, k));
       loop assigns t; loop variant s - t; @/
    while (t < s) t++;
    long i = 0;
    /@ loop invariant 0 <= i <= s && (same(a, b, s) ==> \forall integer k; 0 <= k <= i ==> cnt(a, s, m, k) == cnt(b, s, m, k));
       loop assigns i; loop variant s - i; @/
    while (i < s) i++;
  }
*/
"""
out.append(LEMMAS)
f = piece('static long len_without_eol(const char *l, long s)', 'static unsigned long xdl_hash_record_with_whitespace')
f = f.replace('static long len_without_eol(const char *l, long s)', """/*@ requires 0 <= s && \\valid_read(l + (0 .. s - 1)); assigns \\nothing;
    ensures \\result == cre((char *)l, s); */
static long len_without_eol(const char *l, long s)""", 1)
f = f.replace('int xdl_recmatch(const char *l1, long s1, const char *l2, long s2, long flags)', """/*@ // 1 when the two lines are equal in the mode of the flags (see match), else 0
    requires 0 <= s1 && 0 <= s2 && \\valid_read(l1 + (0 .. s1 - 1)) && \\valid_read(l2 + (0 .. s2 - 1));
    assigns \\nothing;
    ensures \\result == 0 || \\result == 1;
    ensures \\result == 1 <==> match((char *)l1, s1, (char *)l2, s2, flags);
*/
int xdl_recmatch(const char *l1, long s1, const char *l2, long s2, long flags)""", 1)
f = f.replace('\tlong i1, i2;\n', """\tlong i1, i2;
\t//@ ghost int m = (flags & 2) ? 1 : (flags & 4) ? 2 : (flags & 8) ? 3 : (flags & 16) ? 4 : 0;
\t//@ assert m == mode(flags);
\t//@ ghost lem_tr((char *)l1, s1);
\t//@ ghost lem_tr((char *)l2, s2);
\t//@ ghost lem_cnt((char *)l1, s1, m);
\t//@ ghost lem_cnt((char *)l2, s2, m);
\t//@ ghost lem_cnt_same((char *)l1, (char *)l2, s1, m);
""", 1)
SYNC = "0 <= i1 <= s1 && 0 <= i2 <= s2 && cnt((char *)l1, s1, MODE, i1) == cnt((char *)l2, s2, MODE, i2) && \\forall integer i, j; 0 <= i < i1 ==> 0 <= j < i2 ==> el((char *)l1, s1, MODE, i) ==> el((char *)l2, s2, MODE, j) ==> cnt((char *)l1, s1, MODE, i) == cnt((char *)l2, s2, MODE, j) ==> ev((char *)l1, MODE, i) == ev((char *)l2, MODE, j)"
W = SYNC.replace('MODE', '1')
# tool patch (declared in CLAIM.md): WP needs natural loops, so the -w loop, which is
# entered by "goto skip_ws" in its middle, is rotated: the same statements in the same
# order (skip both, test, compare), as a loop that starts at skip_ws.
GOTO = """		goto skip_ws;
		while (i1 < s1 && i2 < s2) {
			if (l1[i1++] != l2[i2++])
				return 0;
		skip_ws:
			while (i1 < s1 && XDL_ISSPACE(l1[i1]))
				i1++;
			while (i2 < s2 && XDL_ISSPACE(l2[i2]))
				i2++;
		}
"""
ROT = f"""		/*@ loop invariant {W};
		    loop assigns i1, i2; loop variant (s1 - i1) + (s2 - i2); */
		for (;;) {{
			//@ ghost long w1 = i1;
			/*@ loop invariant w1 <= i1 <= s1 && allsp((char *)l1, w1, i1); loop assigns i1; loop variant s1 - i1; */
			while (i1 < s1 && XDL_ISSPACE(l1[i1]))
				i1++;
			//@ ghost long w2 = i2;
			/*@ loop invariant w2 <= i2 <= s2 && allsp((char *)l2, w2, i2); loop assigns i2; loop variant s2 - i2; */
			while (i2 < s2 && XDL_ISSPACE(l2[i2]))
				i2++;
			if (!(i1 < s1 && i2 < s2))
				break;
			if (l1[i1++] != l2[i2++])
				return 0;
		}}
"""
assert f.count(GOTO) == 1
f = f.replace(GOTO, ROT, 1)
f = f.replace("\t} else if (flags & XDF_IGNORE_WHITESPACE_CHANGE) {", """\t\t//@ assert tail_w: match((char *)l1, s1, (char *)l2, s2, flags) <==> (allsp((char *)l1, i1, s1) && allsp((char *)l2, i2, s2));
\t} else if (flags & XDF_IGNORE_WHITESPACE_CHANGE) {""", 1)

# -b: in step (same counted bytes so far, i1 and i2 not inside a run of whitespace), or
# already known to differ with one side at its end and the other at a non-space
L1, L2 = '(char *)l1', '(char *)l2'
SB = SYNC.replace('MODE', '2')
BOUND = f"(i1 == 0 || i1 == s1 || !S({L1}, i1 - 1) || !S({L1}, i1)) && (i2 == 0 || i2 == s2 || !S({L2}, i2 - 1) || !S({L2}, i2))"
MATCH = f"match({L1}, s1, {L2}, s2, flags)"
DOOM = f"!{MATCH} && ((i1 == s1 && i2 < s2 && !S({L2}, i2)) || (i2 == s2 && i1 < s1 && !S({L1}, i1)))"
BLOOP = "\t\twhile (i1 < s1 && i2 < s2) {\n\t\t\tif (XDL_ISSPACE(l1[i1]) && XDL_ISSPACE(l2[i2])) {"
assert f.count(BLOOP) == 1
f = f.replace(BLOOP, f"""\t\t/*@ loop invariant 0 <= i1 <= s1 && 0 <= i2 <= s2;
\t\t    loop invariant ({SB} && {BOUND}) || ({DOOM});
\t\t    loop assigns i1, i2; loop variant (s1 - i1) + (s2 - i2); */
""" + BLOOP, 1)
SKIPB = "\t\t\t\twhile (i1 < s1 && XDL_ISSPACE(l1[i1]))\n\t\t\t\t\ti1++;\n\t\t\t\twhile (i2 < s2 && XDL_ISSPACE(l2[i2]))\n\t\t\t\t\ti2++;\n\t\t\t\tcontinue;"
assert f.count(SKIPB) == 1
f = f.replace(SKIPB, f"""\t\t\t\t//@ assert sk_0: i1 < s1 && i2 < s2 && S({L1}, i1) && S({L2}, i2);
\t\t\t\t//@ assert sk_nd: !({DOOM});
\t\t\t\t//@ assert sk_inv: ({SB} && {BOUND}) || ({DOOM});
\t\t\t\t//@ assert sk_bd: {BOUND};
\t\t\t\t//@ assert sk_01: (i1 == 0 || !S({L1}, i1 - 1)) && (i2 == 0 || !S({L2}, i2 - 1));
\t\t\t\t//@ ghost long r1 = i1;
\t\t\t\t/*@ loop invariant r1 <= i1 <= s1 && allsp({L1}, r1, i1); loop assigns i1; loop variant s1 - i1; */
\t\t\t\twhile (i1 < s1 && XDL_ISSPACE(l1[i1]))
\t\t\t\t\ti1++;
\t\t\t\t//@ ghost long r2 = i2;
\t\t\t\t/*@ loop invariant r2 <= i2 <= s2 && allsp({L2}, r2, i2); loop assigns i2; loop variant s2 - i2; */
\t\t\t\twhile (i2 < s2 && XDL_ISSPACE(l2[i2]))
\t\t\t\t\ti2++;
\t\t\t\t//@ assert run_ends: (i1 == s1 || !S({L1}, i1)) && (i2 == s2 || !S({L2}, i2));
\t\t\t\tcontinue;""", 1)
f = f.replace("\t} else if (flags & XDF_IGNORE_WHITESPACE_AT_EOL) {", f"""\t\t//@ assert tail_b: {MATCH} <==> (allsp({L1}, i1, s1) && allsp({L2}, i2, s2));
\t}} else if (flags & XDF_IGNORE_WHITESPACE_AT_EOL) {{""", 1)

# --ignore-space-at-eol: the common prefix
ELOOP = "\t\twhile (i1 < s1 && i2 < s2 && l1[i1] == l2[i2]) {\n\t\t\ti1++;\n\t\t\ti2++;\n\t\t}\n\t} else if (flags & XDF_IGNORE_CR_AT_EOL) {"
assert f.count(ELOOP) == 1
f = f.replace(ELOOP, f"""\t\t/*@ loop invariant 0 <= i1 <= s1 && i1 == i2 && i2 <= s2 && same({L1}, {L2}, i1);
\t\t    loop assigns i1, i2; loop variant s1 - i1; */
\t\twhile (i1 < s1 && i2 < s2 && l1[i1] == l2[i2]) {{
\t\t\ti1++;
\t\t\ti2++;
\t\t}}
\t\t//@ assert tail_e: {MATCH} <==> (allsp({L1}, i1, s1) && allsp({L2}, i2, s2));
\t}} else if (flags & XDF_IGNORE_CR_AT_EOL) {{""", 1)

# the end, shared by -w, -b and --ignore-space-at-eol: the rest must be whitespace
TAIL1 = "\tif (i1 < s1) {\n\t\twhile (i1 < s1 && XDL_ISSPACE(l1[i1]))\n\t\t\ti1++;\n"
TAIL2 = "\tif (i2 < s2) {\n\t\twhile (i2 < s2 && XDL_ISSPACE(l2[i2]))\n\t\t\ti2++;\n"
assert f.count(TAIL1) == 1 and f.count(TAIL2) == 1
f = f.replace(TAIL1, f"""\t//@ assert tail: {MATCH} <==> (allsp({L1}, i1, s1) && allsp({L2}, i2, s2));
\t//@ ghost long t1 = i1;
\tif (i1 < s1) {{
\t\t/*@ loop invariant t1 <= i1 <= s1 && allsp({L1}, t1, i1); loop assigns i1; loop variant s1 - i1; */
\t\twhile (i1 < s1 && XDL_ISSPACE(l1[i1]))
\t\t\ti1++;
""", 1)
f = f.replace(TAIL2, f"""\t//@ ghost long t2 = i2;
\tif (i2 < s2) {{
\t\t/*@ loop invariant t2 <= i2 <= s2 && allsp({L2}, t2, i2); loop assigns i2; loop variant s2 - i2; */
\t\twhile (i2 < s2 && XDL_ISSPACE(l2[i2]))
\t\t\ti2++;
""", 1)

# proof hints for xdl_recmatch: one assert per return and per case, so each goal is small
T1, T2 = f"tr({L1}, s1)", f"tr({L2}, s2)"
def C(l, s, i, mo='2'): return f"cnt({l}, {s}, {mo}, {i})"
# the whitespace flags are bits 1..4 (lemma ws_bits, lemmas.py)
FIRST = "\tif (s1 == s2 && !memcmp(l1, l2, s1))\n\t\treturn 1;\n\tif (!(flags & XDF_WHITESPACE_FLAGS))\n\t\treturn 0;\n"
assert f.count(FIRST) == 1
f = f.replace(FIRST, f"""\t//@ assert r_eq: s1 == s2 && same({L1}, {L2}, s1) ==> {MATCH};
\tif (s1 == s2 && !memcmp(l1, l2, s1))
\t\treturn 1;
\t//@ assert r_ne: !(s1 == s2 && same({L1}, {L2}, s1));
\t//@ assert wsf: ((flags & XDF_WHITESPACE_FLAGS) != 0) <==> (m != 0);
\t//@ assert r_nows: (flags & XDF_WHITESPACE_FLAGS) == 0 ==> !{MATCH};
\tif (!(flags & XDF_WHITESPACE_FLAGS))
\t\treturn 0;
""", 1)
# -w: a differing pair of counted bytes at the same count
WCMP = "\t\t\tif (!(i1 < s1 && i2 < s2))\n\t\t\t\tbreak;\n\t\t\tif (l1[i1++] != l2[i2++])\n\t\t\t\treturn 0;\n"
assert f.count(WCMP) == 1
f = f.replace(WCMP, f"""\t\t\t//@ assert w_end: (i1 == s1 || !S({L1}, i1)) && (i2 == s2 || !S({L2}, i2));
\t\t\tif (!(i1 < s1 && i2 < s2))
\t\t\t\tbreak;
\t\t\t//@ assert w_el: el({L1}, s1, 1, i1) && el({L2}, s2, 1, i2) && {C(L1,'s1','i1 + 1','1')} == {C(L1,'s1','i1','1')} + 1 && {C(L2,'s2','i2 + 1','1')} == {C(L2,'s2','i2','1')} + 1;
\t\t\t//@ assert r_w0: {MATCH} ==> ev({L1}, 1, i1) == ev({L2}, 1, i2);
\t\t\t//@ assert r_w1: ev({L1}, 1, i1) == l1[i1] && ev({L2}, 1, i2) == l2[i2];
\t\t\t//@ assert r_w: l1[i1] != l2[i2] ==> !{MATCH};
\t\t\tif (l1[i1++] != l2[i2++])
\t\t\t\treturn 0;
""", 1)
TW = "\t\t//@ assert tail_w:"
assert f.count(TW) == 1
f = f.replace(TW, f"""\t\t//@ assert w_x: (i1 == s1 || i2 == s2) && (i1 == s1 || !S({L1}, i1)) && (i2 == s2 || !S({L2}, i2));
\t\t//@ assert w_both: i1 == s1 && i2 == s2 ==> {MATCH};
\t\t//@ assert w_2: i1 == s1 && i2 < s2 ==> {C(L2,'s2','i2','1')} < {C(L2,'s2','s2','1')} && !{MATCH} && !allsp({L2}, i2, s2);
\t\t//@ assert w_1a: i2 == s2 && i1 < s1 ==> el({L1}, s1, 1, i1) && !allsp({L1}, i1, s1);
\t\t//@ assert w_1b: i2 == s2 && i1 < s1 ==> {C(L1,'s1','i1','1')} < {C(L1,'s1','s1','1')};
\t\t//@ assert w_1c: i2 == s2 && i1 < s1 ==> {C(L2,'s2','s2','1')} == {C(L2,'s2','i2','1')};
\t\t//@ assert w_1: i2 == s2 && i1 < s1 ==> {C(L1,'s1','i1','1')} < {C(L1,'s1','s1','1')} && !{MATCH} && !allsp({L1}, i1, s1);
""" + TW, 1)
# -b
G = f"({SB} && {BOUND})"
SKIPS = "\t\t\t\t//@ assert run_ends: "
assert f.count(SKIPS) == 1
f = f.replace(SKIPS, f"""\t\t\t\t//@ assert sk_r: r1 < i1 && r2 < i2 && S({L1}, r1) && S({L2}, r2) && (r1 == 0 || !S({L1}, r1 - 1)) && (r2 == 0 || !S({L2}, r2 - 1));
\t\t\t\t//@ assert sk_el: (el({L1}, s1, 2, r1) <==> r1 < {T1}) && (el({L2}, s2, 2, r2) <==> r2 < {T2});
\t\t\t\t//@ assert sk_a1: {C(L1,'s1','r1 + 1')} == {C(L1,'s1','r1')} + (el({L1}, s1, 2, r1) ? 1 : 0);
\t\t\t\t//@ assert sk_b1: \\forall integer j; r1 + 1 <= j < i1 ==> !el({L1}, s1, 2, j);
\t\t\t\t//@ assert sk_d1: {C(L1,'s1','i1')} == {C(L1,'s1','r1 + 1')};
\t\t\t\t//@ assert sk_c1: {C(L1,'s1','i1')} == {C(L1,'s1','r1')} + (r1 < {T1} ? 1 : 0);
\t\t\t\t//@ assert sk_a2: {C(L2,'s2','r2 + 1')} == {C(L2,'s2','r2')} + (el({L2}, s2, 2, r2) ? 1 : 0);
\t\t\t\t//@ assert sk_b2: \\forall integer j; r2 + 1 <= j < i2 ==> !el({L2}, s2, 2, j);
\t\t\t\t//@ assert sk_d2: {C(L2,'s2','i2')} == {C(L2,'s2','r2 + 1')};
\t\t\t\t//@ assert sk_c2: {C(L2,'s2','i2')} == {C(L2,'s2','r2')} + (r2 < {T2} ? 1 : 0);
\t\t\t\t//@ assert sk_t1: r1 >= {T1} ==> i1 == s1;
\t\t\t\t//@ assert sk_t2: r2 >= {T2} ==> i2 == s2;
\t\t\t\t//@ assert sk_n1: r1 < {T1} ==> i1 < {T1} && !S({L1}, i1) && el({L1}, s1, 2, i1);
\t\t\t\t//@ assert sk_n2: r2 < {T2} ==> i2 < {T2} && !S({L2}, i2) && el({L2}, s2, 2, i2);
""" + SKIPS, 1)
BCMP = "\t\t\t\tcontinue;\n\t\t\t}\n\t\t\tif (l1[i1++] != l2[i2++])\n\t\t\t\treturn 0;\n"
assert f.count(BCMP) == 1
f = f.replace(BCMP, f"""\t\t\t\tcontinue;
\t\t\t}}
\t\t\t//@ assert b_g: {G};
\t\t\t//@ assert b_ns: !(S({L1}, i1) && S({L2}, i2));
\t\t\t//@ assert b_eq: l1[i1] == l2[i2] ==> !S({L1}, i1) && !S({L2}, i2) && i1 < {T1} && i2 < {T2} && el({L1}, s1, 2, i1) && el({L2}, s2, 2, i2) && {C(L1,'s1','i1 + 1')} == {C(L1,'s1','i1')} + 1 && {C(L2,'s2','i2 + 1')} == {C(L2,'s2','i2')} + 1;
\t\t\t//@ assert b_nn: !S({L1}, i1) && !S({L2}, i2) && l1[i1] != l2[i2] ==> !{MATCH};
\t\t\t//@ assert b_sn_in: S({L1}, i1) && !S({L2}, i2) && i1 < {T1} ==> el({L1}, s1, 2, i1) && el({L2}, s2, 2, i2) && ev({L1}, 2, i1) == 32 && ev({L2}, 2, i2) != 32 && !{MATCH};
\t\t\t//@ assert b_sn_out: S({L1}, i1) && !S({L2}, i2) && i1 >= {T1} ==> {C(L1,'s1','s1')} == {C(L1,'s1','i1')} && {C(L2,'s2','i2')} < {C(L2,'s2','s2')} && !{MATCH};
\t\t\t//@ assert b_ns_in: !S({L1}, i1) && S({L2}, i2) && i2 < {T2} ==> el({L1}, s1, 2, i1) && el({L2}, s2, 2, i2) && ev({L2}, 2, i2) == 32 && ev({L1}, 2, i1) != 32 && !{MATCH};
\t\t\t//@ assert b_ns_out: !S({L1}, i1) && S({L2}, i2) && i2 >= {T2} ==> {C(L2,'s2','s2')} == {C(L2,'s2','i2')} && {C(L1,'s1','i1')} < {C(L1,'s1','s1')} && !{MATCH};
\t\t\tif (l1[i1++] != l2[i2++])
\t\t\t\treturn 0;
""", 1)
TB = "\t\t//@ assert tail_b:"
assert f.count(TB) == 1
f = f.replace(TB, f"""\t\t//@ assert b_x: i1 == s1 || i2 == s2;
\t\t//@ assert b_2a: {G} && i1 == s1 && i2 < {T2} ==> !S({L2}, {T2} - 1) && el({L2}, s2, 2, {T2} - 1) && {C(L2,'s2','i2')} < {C(L2,'s2','s2')} && !{MATCH} && !allsp({L2}, i2, s2);
\t\t//@ assert b_2b: {G} && i1 == s1 && i2 >= {T2} ==> allsp({L2}, i2, s2) && {C(L2,'s2','i2')} == {C(L2,'s2','s2')} && {MATCH};
\t\t//@ assert b_1a: {G} && i2 == s2 && i1 < {T1} ==> !S({L1}, {T1} - 1) && el({L1}, s1, 2, {T1} - 1) && {C(L1,'s1','i1')} < {C(L1,'s1','s1')} && !{MATCH} && !allsp({L1}, i1, s1);
\t\t//@ assert b_1b: {G} && i2 == s2 && i1 >= {T1} ==> allsp({L1}, i1, s1) && {C(L1,'s1','i1')} == {C(L1,'s1','s1')} && {MATCH};
""" + TB, 1)
out.append(f)

# ---------------------------------------------------------------- the hash functions
out.append(r"""
/*@ // ---- hash of a line: ha = 5381, then ha = (ha * 33) ^ c (mod 2^64) for each byte c that
    // counts in the mode (el), with the value ev; c is the char value, as unsigned long
    logic integer u64c(integer c) = c < 0 ? c + 18446744073709551616 : c;
    logic integer step(integer h, integer c) = ((h * 33) % 18446744073709551616) ^ u64c(c);
    logic integer hacc{L}(char *l, integer s, integer m, integer i) =
      i <= 0 ? 5381 : el(l, s, m, i - 1) ? step(hacc(l, s, m, i - 1), ev(l, m, i - 1)) : hacc(l, s, m, i - 1);
    // the record that starts at d and ends at top: up to and with its first '\n'; e = its length
    predicate record{L}(char *d, integer n, integer e) =
      0 <= e <= n && (\forall integer j; 0 <= j < e - 1 ==> B(d, j) != 10) && (e < n ==> e > 0 && B(d, e - 1) == 10);
*/
/*@ ghost
  // proof only: bytes that do not count do not change the hash (by induction)
  /@ requires 0 <= s; assigns \nothing;
     ensures \forall integer a, b; 0 <= a <= b <= s ==> (\forall integer j; a <= j < b ==> !el(l, s, m, j)) ==> hacc(l, s, m, a) == hacc(l, s, m, b); @/
  void lem_hacc(char *l, long s, int m) {
    long b = 0;
    /@ loop invariant 0 <= b <= s;
       loop invariant \forall integer a, c; 0 <= a <= c <= b ==> (\forall integer j; a <= j < c ==> !el(l, s, m, j)) ==> hacc(l, s, m, a) == hacc(l, s, m, c);
       loop assigns b; loop variant s - b; @/
    while (b < s) b++;
  }
*/
""")
import os, subprocess
out.append(subprocess.check_output([sys.executable, "-I", os.path.join(os.path.dirname(os.path.abspath(__file__)), "lemmas.py"), "--acsl", "hash_step"], text=True))
HASH_REQ = r"""requires \valid(data) && *data <= top && \base_addr(*data) == \base_addr(top) && top - *data < LONG_MAX;
    requires \valid_read(*data + (0 .. top - *data - 1)) && \separated(data, *data + (0 .. top - *data - 1));
    assigns *data;
    ensures record((char *)\old(*data), top - \old(*data), *data - \old(*data));
    ensures \result == hacc((char *)\old(*data), *data - \old(*data), mode(flags), *data - \old(*data));"""
# proof only: find where the record ends (ge = index of its '\n', or its length)
GE = r"""	char const *ptr = *data;
	/*@ ghost long ge = 0;
	  /@ loop invariant 0 <= ge <= top - ptr && (\forall integer j; 0 <= j < ge ==> B((char *)ptr, j) != 10);
	     loop assigns ge; loop variant (top - ptr) - ge; @/
	  while (ge < top - ptr && ptr[ge] != '\n') ge++;
	*/
	//@ assert ge_end: ge == top - ptr || B((char *)ptr, ge) == 10;
	//@ ghost long sh = ge < top - ptr ? ge + 1 : ge;
	//@ ghost int m = (flags & 2) ? 1 : (flags & 4) ? 2 : (flags & 8) ? 3 : (flags & 16) ? 4 : 0;
	//@ assert m == mode(flags);
"""
f = piece('static unsigned long xdl_hash_record_with_whitespace(char const **data,', 'unsigned long xdl_hash_record(char const **data')
f = f.replace('static unsigned long xdl_hash_record_with_whitespace(char const **data,', "/*@ requires (flags & XDF_WHITESPACE_FLAGS) != 0;\n    " + HASH_REQ + "\n*/\nstatic unsigned long xdl_hash_record_with_whitespace(char const **data,", 1)
assert f.count('\tchar const *ptr = *data;\n') == 1
f = f.replace('\tchar const *ptr = *data;\n', GE + '\t//@ ghost lem_hacc((char *)ptr, sh, m);\n\t//@ ghost lem_tr((char *)ptr, sh);\n', 1)
D = '(char *)\\at(*data, Pre)'
HL = f"hacc({D}, sh, m, ptr - \\at(*data, Pre))"
WSLOOP = "\tfor (; ptr < top && *ptr != '\\n'; ptr++) {\n\t\tif (cr_at_eol_only) {"
assert f.count(WSLOOP) == 1
f = f.replace(WSLOOP, f"""\t/*@ loop invariant \\at(*data, Pre) <= ptr <= \\at(*data, Pre) + ge && *data == \\at(*data, Pre) && \\base_addr(ptr) == \\base_addr(\\at(*data, Pre)) && ptr == \\at(*data, Pre) + (ptr - \\at(*data, Pre));
\t    loop invariant cr_at_eol_only != 0 <==> m == 4;
\t    loop invariant ha == {HL};
\t    loop invariant m == 2 ==> (ptr == \\at(*data, Pre) || ptr == \\at(*data, Pre) + ge || !S({D}, ptr - \\at(*data, Pre) - 1) || !S({D}, ptr - \\at(*data, Pre)));
\t    loop assigns ptr, ha; loop variant top - ptr; */
""" + WSLOOP, 1)
RUN = "\t\t\twhile (ptr + 1 < top && XDL_ISSPACE(ptr[1])\n\t\t\t\t\t&& ptr[1] != '\\n')\n\t\t\t\tptr++;\n"
assert f.count(RUN) == 1
f = f.replace(RUN, f"""\t\t\t/*@ loop invariant ptr2 <= ptr < \\at(*data, Pre) + ge && allsp({D}, ptr2 - \\at(*data, Pre), ptr - \\at(*data, Pre) + 1);
\t\t\t    loop assigns ptr; loop variant top - ptr; */
""" + RUN, 1)
EOLLOOP = "\t\t\t\twhile (ptr2 != ptr + 1) {\n"
assert f.count(EOLLOOP) == 1
f = f.replace(EOLLOOP, f"""\t\t\t\t//@ ghost char const *r0 = ptr2;
\t\t\t\t/*@ loop invariant r0 <= ptr2 <= ptr + 1 && ha == hacc({D}, sh, m, ptr2 - \\at(*data, Pre));
\t\t\t\t    loop assigns ptr2, ha; loop variant ptr + 1 - ptr2; */
""" + EOLLOOP, 1)
out.append(f)
f = piece('unsigned long xdl_hash_record(char const **data', 'unsigned int xdl_hashbits')
f = f.replace('unsigned long xdl_hash_record(char const **data, char const *top, long flags) {', "/*@ " + HASH_REQ + "\n*/\nunsigned long xdl_hash_record(char const **data, char const *top, long flags) {", 1)
assert f.count('\tchar const *ptr = *data;\n') == 1
f = f.replace('\tchar const *ptr = *data;\n', GE, 1)
HRET = "\t\treturn xdl_hash_record_with_whitespace(data, top, flags);\n\n"
assert f.count(HRET) == 1
f = f.replace(HRET, HRET + "\t//@ assert h_m0: m == 0;\n", 1)
HSTEP = f"\t\t//@ assert h_el: el({D}, sh, 0, ptr - \\at(*data, Pre)) && ev({D}, 0, ptr - \\at(*data, Pre)) == *ptr && hacc({D}, sh, 0, ptr - \\at(*data, Pre) + 1) == step(ha, *ptr);\n"
NLOOP = "\tfor (; ptr < top && *ptr != '\\n'; ptr++) {\n\t\tha += (ha << 5);"
assert f.count(NLOOP) == 1
f = f.replace(NLOOP, f"""\t/*@ loop invariant \\at(*data, Pre) <= ptr <= \\at(*data, Pre) + ge && *data == \\at(*data, Pre) && \\base_addr(ptr) == \\base_addr(\\at(*data, Pre)) && ptr == \\at(*data, Pre) + (ptr - \\at(*data, Pre));
\t    loop invariant ha == {HL};
\t    loop assigns ptr, ha; loop variant top - ptr; */
""" + NLOOP.replace("\t\tha += (ha << 5);", "\t\t//@ assert here: ptr - \\at(*data, Pre) < ge && B((char *)\\at(*data, Pre), ptr - \\at(*data, Pre)) == (unsigned char)*ptr;\n" + HSTEP + "\t\tha += (ha << 5);"), 1)
f = f.replace("\t*data = ptr < top ? ptr + 1: ptr;\n", f"""\t//@ assert h_x: ptr >= top || *ptr == '\\n';
\t//@ assert h_x1: ptr < top && *ptr == '\\n' ==> B({D}, ptr - \\at(*data, Pre)) == 10;
\t//@ assert h_x2: ptr - \\at(*data, Pre) >= ge;
\t//@ assert h_end0: ptr - \\at(*data, Pre) == ge;
\t//@ assert h_end1: ge < sh ==> B({D}, ge) == 10;
\t//@ assert h_end: ptr == \\at(*data, Pre) + ge && (ge < sh ==> !el({D}, sh, 0, ge));
\t//@ assert h_last: hacc({D}, sh, 0, sh) == hacc({D}, sh, 0, ge);
\t*data = ptr < top ? ptr + 1: ptr;
""", 1)
out.append(f)

open(sys.argv[2], 'w').write('\n'.join(out))
