"""ACSL for path.c (UNIX build), written from each function's doc comment.

C: function -> contract. GHOST: function -> ghost parameter declaration (the string
length the caller already knows). A: function -> annotations (kind, anchor, text).
Kinds: before = own line before the anchor line, after = inline after the anchor text.
"""
LOGIC = r"""
/*@ // every byte in [a, b) is c / is not c (pointer form, see vp_string.h)
    predicate allc{L}(char *a, char *b, integer c) =
      \forall char *q; \base_addr(q) == \base_addr(a) && a <= q < b ==> *q == c;
    predicate noc{L}(char *a, char *b, integer c) =
      \forall char *q; \base_addr(q) == \base_addr(a) && a <= q < b ==> *q != c;
    predicate within{L}(char *r, char *s, integer n) =
      \base_addr(r) == \base_addr(s) && s <= r <= s + n;
    predicate alpha(integer c) = ('a' <= c <= 'z') || ('A' <= c <= 'Z');
    // RFC 3986 scheme characters after the first: ALPHA / DIGIT / "+" / "-" / "."
    predicate schemec(integer c) = alpha(c) || ('0' <= c <= '9') || c == '+' || c == '-' || c == '.';
    // WHATWG "starts with a Windows drive letter", on the first len bytes
    predicate drive{L}(char *p, integer len) =
      len >= 2 && alpha(p[0]) && (p[1] == ':' || p[1] == '|')
      && (len == 2 || p[2] == '/' || p[2] == '\\' || p[2] == '?' || p[2] == '#');
    // what follows a URL scheme: ":/" is 1 (URL_SLASH), ":\\" is 2 (URL_BACKSLASH)
    logic integer urlk{L}(char *p) =
      p[0] == ':' && p[1] == '/' ? 1 : (p[0] == ':' && p[1] == '\\' && p[2] == '\\' ? 2 : 0);
    // the scheme run of f (f[1 .. k-1] scheme characters) ends at k
    predicate scheme_end{L}(char *f, integer n, integer k) =
      1 <= k <= n && (\forall integer i; 1 <= i < k ==> schemec(f[i])) && !schemec(f[k]);
    // f starts with "name:/" or "name:\\" (path_with_url's doc), not a drive letter
    predicate url_kind{L}(char *f, integer n, integer r) =
      (!alpha(f[0]) ==> r == 0) && (alpha(f[0]) && drive(f, n) ==> r == 0)
      && \forall integer k; alpha(f[0]) && !drive(f, n) && scheme_end(f, n, k) ==>
           r == (f[k - 1] == '+' || f[k - 1] == '-' || f[k - 1] == '.' ? 0 : urlk(f + k));
*/
"""

SEP = r"""assigns \nothing;
    ensures \result == (c == '/' ? 1 : 0);"""

C = {
"vim_ispathsep": SEP,
"vim_ispathsep_nocolon": SEP,
"vim_ispathlistsep": r"""assigns \nothing;
    ensures \result == (c == ':' ? 1 : 0);""",
"path_head_length": r"""assigns \nothing;
    ensures \result == 1;""",
"is_path_head": r"""requires \valid_read(path);
    assigns \nothing;
    ensures \result == (*path == '/' ? 1 : 0);""",
"path_skip_sep": r"""requires str_len((char *)path, n);
    assigns \nothing;
    ensures within(\result, (char *)path, n);
    ensures allc((char *)path, \result, '/') && *\result != '/';""",
"get_past_head": r"""requires str_len((char *)path, n);
    assigns \nothing;
    ensures within(\result, (char *)path, n);
    ensures allc((char *)path, \result, '/') && *\result != '/';""",
"path_tail": r"""requires fname == \null || str_len((char *)fname, n);
    assigns \nothing;
    ensures fname == \null ==> str_len(\result, 0);
    ensures fname != \null ==> within(\result, (char *)fname, n)
            && (\result == fname || \result[-1] == '/')
            && noc(\result, (char *)fname + n, '/');""",
"path_next_component": r"""requires str_len((char *)fname, n);
    assigns \nothing;
    ensures within((char *)\result, (char *)fname, n);
    ensures (\result == fname + n && noc((char *)fname, (char *)fname + n, '/'))
            || (fname < \result && \result[-1] == '/' && noc((char *)fname, (char *)\result - 1, '/'));""",
"path_is_absolute": r"""requires \valid_read(fname);
    assigns \nothing;
    ensures \result == ((*fname == '/' || *fname == '~') ? 1 : 0);""",
"path_has_drive_letter": r"""requires path_len <= 2 || \valid_read(p + (0 .. 2));
    requires path_len < 2 || \valid_read(p + (0 .. 1));
    assigns \nothing;
    ensures \result == ((path_len >= 2
             && (('a' <= p[0] && p[0] <= 'z') || ('A' <= p[0] && p[0] <= 'Z'))
             && (p[1] == ':' || p[1] == '|')
             && (path_len == 2 || p[2] == '/' || p[2] == '\\' || p[2] == '?' || p[2] == '#')) ? 1 : 0);""",
"path_is_url": r"""requires is_str((char *)p);
    assigns \nothing;
    ensures \result == urlk((char *)p);""",
"path_with_url": r"""requires str_len((char *)fname, n);
    assigns \nothing;
    ensures url_kind((char *)fname, n, \result);
    ensures alpha(fname[0]) && !drive((char *)fname, n) ==> \exists integer k; scheme_end((char *)fname, n, k);""",
"vim_isAbsName": r"""requires str_len((char *)name, n);
    assigns \nothing;
    ensures \result == ((name[0] == '/' || name[0] == '~'
                         || \forall integer r; url_kind((char *)name, n, r) ==> r != 0) ? 1 : 0);""",
"after_pathsep": r"""requires \base_addr(p) == \base_addr(b) && b <= p && \valid_read(b + (0 .. p - b));
    assigns \nothing;
    ensures \result == (p > b && p[-1] == '/' ? 1 : 0);""",
# fname's path_tail t (the unique t just past a '/' or at fname with no '/' after it),
# moved back over the '/' run before it, but not into the head (the leading '/'s).
"path_tail_with_sep": r"""requires str_len(fname, n);
    assigns \nothing;
    ensures within(\result, fname, n);
    ensures \forall char *t, char *h; within(t, fname, n) && (t == fname || t[-1] == '/') && noc(t, fname + n, '/')
              && within(h, fname, n) && allc(fname, h, '/') && *h != '/' ==>
              h <= \result <= t && allc(\result, t, '/') && (\result == h || \result[-1] != '/');""",
# Memory safety, termination and bounds only (not the quote rules): the result lies in
# the string after the head, just past a '/' (or at the head), and *len stays inside.
"invocation_path_tail": r"""requires str_len((char *)invocation, n);
    requires len == \null || (\valid(len) && \separated(len, (char *)invocation + (0 .. n)));
    assigns *len;
    ensures within((char *)\result, (char *)invocation, n);
    ensures \result == invocation || \result[-1] == '/';
    ensures len != \null ==> \result + *len <= invocation + n;""",
}

GHOST = {f: "size_t n" for f in ("path_skip_sep", "get_past_head", "path_tail", "path_with_url",
                                 "vim_isAbsName", "path_tail_with_sep",
                                 "path_next_component", "invocation_path_tail")}

SIG = {  # the signature line the ghost parameter goes after
"path_with_url": "int path_with_url(const char *fname)",
"vim_isAbsName": "bool vim_isAbsName(const char *name)",
"path_tail_with_sep": "char *path_tail_with_sep(char *fname)",
"path_skip_sep": "char *path_skip_sep(const char *path, bool colon)",
"get_past_head": "char *get_past_head(const char *path)",
"path_tail": "char *path_tail(const char *fname)",
"path_next_component": "const char *path_next_component(const char *fname)",
"invocation_path_tail": "const char *invocation_path_tail(const char *invocation, size_t *len)",
}


def annotations(fixed):
    inv = [
        ("after", "get_past_head(invocation)", "ghost (n)"),
        ("before", "  while (*p != NUL && (inquote || *p != ' ')) {",
         r"""loop invariant within((char *)p, (char *)invocation, n);
      loop invariant within((char *)tail, (char *)invocation, n) && within((char *)tail_end, (char *)invocation, n);
      loop invariant tail <= tail_end <= p;
      loop invariant tail == invocation || tail[-1] == '/';
      loop assigns p, tail, tail_end, inquote;
      loop variant invocation + n - p;"""),
        ("before", "    int l = utfc_ptr2len(p);", r"""assert str_len((char *)p, invocation + n - p);"""),
    ]
    if fixed:
        inv.append(("before", "      l = utfc_ptr2len(p);", r"""assert str_len((char *)p, invocation + n - p);"""))
    return {
    "path_skip_sep": [("before", "  while (colon ? vim_ispathsep(*path) : vim_ispathsep_nocolon(*path)) {",
        r"""loop invariant within((char *)path, (char *)\at(path, Pre), n);
      loop invariant allc((char *)\at(path, Pre), (char *)path, '/');
      loop assigns path;
      loop variant \at(path, Pre) + n - path;""")],
    "get_past_head": [("after", "path_skip_sep(retval, true)", "ghost (n)")],
    "path_tail": [
        ("after", "get_past_head(fname)", "ghost (n)"),
        ("before", "  for (const char *p = tail; *p != NUL; p++) {",
         r"""loop invariant within((char *)p, (char *)fname, n) && within((char *)tail, (char *)fname, n);
      loop invariant tail <= p;
      loop invariant tail == fname || tail[-1] == '/';
      loop invariant noc((char *)tail, (char *)p, '/');
      loop assigns p, tail;
      loop variant fname + n - p;""")],
    "path_next_component": [("before", "  while (*fname != NUL && !vim_ispathsep(*fname)) {",
        r"""loop invariant within((char *)fname, (char *)\at(fname, Pre), n);
      loop invariant noc((char *)\at(fname, Pre), (char *)fname, '/');
      loop assigns fname;
      loop variant \at(fname, Pre) + n - fname;""")],
    "invocation_path_tail": inv,
    "path_with_url": [
        ("before", "  for (p = fname + 1; (ASCII_ISALNUM(*p) || (*p == '+') || (*p == '-') || (*p == '.')); p++) {}",
         r"""loop invariant within((char *)p, (char *)fname, n) && fname + 1 <= p;
      loop invariant \forall integer i; 1 <= i < p - fname ==> schemec(fname[i]);
      loop assigns p;
      loop variant fname + n - p;"""),
        ("before", "  return path_is_url(p);", r"""assert scheme_end((char *)fname, n, p - fname);"""),
        ("before", "  return path_is_url(p);", r"""assert str_len((char *)p, fname + n - p);""")],
    "vim_isAbsName": [("after", "path_with_url(name)", "ghost (n)")],
    "path_tail_with_sep": [
        ("after", "get_past_head(fname)", "ghost (n)"),
        ("after", "path_tail(fname)", "ghost (n)"),
        ("before", "  while (tail > past_head && after_pathsep(fname, tail)) {", r"""ghost char *t0 = tail;"""),
        ("before", "  while (tail > past_head && after_pathsep(fname, tail)) {",
         r"""loop invariant past_head <= tail <= t0 && within(tail, fname, n);
      loop invariant allc(tail, t0, '/');
      loop assigns tail;
      loop variant tail - past_head;""")],
    }
