"""ACSL for mark.c functions, from their doc comments."""

LOGIC = r"""
/*@ predicate has_mark{L}(xfmark_T *a, integer k) = a[k].fmark.mark.lnum != 0;
    // name of global mark k: 'A'..'Z' for 0..25, '0'..'9' for 26..35
    logic integer gname(integer k) = k < NMARKS ? 'A' + k : '0' + (k - NMARKS);
*/
"""


def contracts():
    return {
        "mark_view_make": r"""requires \valid_read(wp);
    requires 0 <= pos.lnum <= MAXLNUM && 0 <= wp->w_topline <= MAXLNUM;   // line numbers
    assigns \nothing;
    ensures \result.topline_offset == pos.lnum - wp->w_topline;
    ensures \result.skipcol == wp->w_skipcol;""",
        "mark_check_line_bounds": r"""requires buf == \null || \valid_read(buf);
    requires \valid_read(fm) && \valid(errormsg);
    assigns *errormsg;
    ensures \result <==> !(buf != \null && fm->mark.lnum > buf->b_ml.ml_line_count);
    ensures !\result ==> *errormsg == (char *)e_markinval;
    ensures \result ==> *errormsg == \old(*errormsg);""",
        "next_buffer_mark": r"""requires \valid_read(buf) && \valid(mark_name);
    // "Current mark name must either be NUL, '"', '^', '.' or 'a' .. 'z'."
    requires *mark_name == 0 || *mark_name == '"' || *mark_name == '^' || *mark_name == '.'
             || ('a' <= *mark_name <= 'z');
    assigns *mark_name;
    ensures \old(*mark_name) == 0 ==> *mark_name == '"' && \result == &buf->b_last_cursor;
    ensures \old(*mark_name) == '"' ==> *mark_name == '^' && \result == &buf->b_last_insert;
    ensures \old(*mark_name) == '^' ==> *mark_name == '.' && \result == &buf->b_last_change;
    ensures \old(*mark_name) == '.' ==> *mark_name == 'a' && \result == &buf->b_namedm[0];
    ensures \old(*mark_name) == 'z' ==> *mark_name == 'z' && \result == \null;
    ensures 'a' <= \old(*mark_name) < 'z' ==>
      *mark_name == \old(*mark_name) + 1 && \result == &buf->b_namedm[*mark_name - 'a'];""",
        "mark_jumplist_iter": r"""requires \valid_read(win) && 0 <= win->w_jumplistlen <= JUMPLISTSIZE;
    requires \valid(fm) && \separated(fm, win);
    // iter is NULL or what the previous call returned: an entry of the active jump list
    requires iter == \null || (win->w_jumplistlen > 0 &&
      \exists integer k; 0 <= k < win->w_jumplistlen && (xfmark_T *)iter == &win->w_jumplist[k]);
    assigns *fm;
    ensures iter == \null && win->w_jumplistlen == 0 ==> \result == \null
      && fm->fmark.mark.lnum == 0 && fm->fmark.mark.col == 0 && fm->fmark.mark.coladd == 0
      && fm->fmark.fnum == 0 && fm->fmark.timestamp == 0 && fm->fmark.view.topline_offset == MAXLNUM
      && fm->fmark.view.skipcol == 0 && fm->fmark.additional_data == \null && fm->fname == \null;
    ensures \forall integer k; 0 <= k < win->w_jumplistlen &&
        (iter == \null ? k == 0 : (xfmark_T *)iter == &win->w_jumplist[k]) ==>
      *fm == win->w_jumplist[k]
      && \result == (k == win->w_jumplistlen - 1 ? \null : (void *)&win->w_jumplist[k + 1]);""",
        "mark_global_iter": r"""requires \valid(name) && \valid(fm) && \separated(name, fm, namedfm + (0 .. NGLOBALMARKS - 1));
    // iter is NULL or what the previous call returned: an entry of namedfm
    requires iter == \null || \exists integer k; 0 <= k < NGLOBALMARKS && (xfmark_T *)iter == &namedfm[k];
    assigns *name, *fm;
    ensures \forall integer s; (iter == \null ? s == 0 : (xfmark_T *)iter == &namedfm[s]) ==>
      // no set mark from s on: name is NUL, result NULL
      ((\forall integer j; s <= j < NGLOBALMARKS ==> !has_mark(&namedfm[0], j)) ==>
         *name == NUL && \result == \null)
      // j = first set mark from s: its name and value, and the next set mark after it (or NULL)
      && (\forall integer j; s <= j < NGLOBALMARKS && has_mark(&namedfm[0], j)
            && (\forall integer i; s <= i < j ==> !has_mark(&namedfm[0], i)) ==>
          *name == gname(j) && *fm == namedfm[j]
          && ((\forall integer i; j < i < NGLOBALMARKS ==> !has_mark(&namedfm[0], i)) ==> \result == \null)
          && (\forall integer n; j < n < NGLOBALMARKS && has_mark(&namedfm[0], n)
                && (\forall integer i; j < i < n ==> !has_mark(&namedfm[0], i)) ==> \result == (void *)&namedfm[n]));""",
    }


def annotations():
    return {
        "mark_global_iter": [
            ("  while ((size_t)(iter_mark - &(namedfm[0])) < ARRAY_SIZE(namedfm)\n",
             r"""loop invariant \forall integer s; (iter == \null ? s == 0 : (xfmark_T *)iter == &namedfm[s]) ==>
        s <= iter_mark - &namedfm[0] <= NGLOBALMARKS
        && \forall integer i; s <= i < iter_mark - &namedfm[0] ==> !has_mark(&namedfm[0], i);
      loop invariant &namedfm[0] <= iter_mark <= &namedfm[NGLOBALMARKS];
      loop assigns iter_mark; loop variant NGLOBALMARKS - (iter_mark - &namedfm[0]);"""),
            ("  while ((size_t)(++iter_mark - &(namedfm[0])) < ARRAY_SIZE(namedfm)) {",
             r"""loop invariant iter_off <= iter_mark - &namedfm[0] < NGLOBALMARKS;
      loop invariant \forall integer i; iter_off < i <= iter_mark - &namedfm[0] ==> !has_mark(&namedfm[0], i);
      loop assigns iter_mark; loop variant NGLOBALMARKS - (iter_mark - &namedfm[0]);"""),
        ],
    }
