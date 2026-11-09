"""ACSL for mark.c functions, from their doc comments."""

LOGIC = r"""
/*@ predicate has_mark{L}(xfmark_T *a, integer k) = a[k].fmark.mark.lnum != 0;
    // name of global mark k: 'A'..'Z' for 0..25, '0'..'9' for 26..35
    // fm holds INIT_FMARK, except its timestamp
    predicate init_fmark{L}(fmark_T *fm) = fm->mark.lnum == 0 && fm->mark.col == 0 && fm->mark.coladd == 0
      && fm->fnum == 0 && fm->view.topline_offset == MAXLNUM && fm->view.skipcol == 0
      && fm->additional_data == \null;
    logic integer gname(integer k) = k < NMARKS ? 'A' + k : '0' + (k - NMARKS);
*/
"""


def contracts():
    return {
        "free_fmark": r"""requires 0 <= vp_nfreed < 1000;
    assigns vp_freed[vp_nfreed], vp_nfreed;
    ensures vp_nfreed == \old(vp_nfreed) + 1 && vp_freed[\old(vp_nfreed)] == fm.additional_data;""",
        "free_xfmark": r"""requires 0 <= vp_nfreed < 999;
    assigns vp_freed[vp_nfreed .. vp_nfreed + 1], vp_nfreed;
    ensures vp_nfreed == \old(vp_nfreed) + 2;
    ensures vp_freed[\old(vp_nfreed)] == fm.fname && vp_freed[\old(vp_nfreed) + 1] == fm.fmark.additional_data;""",
        "clear_fmark": r"""requires \valid(fm) && 0 <= vp_nfreed < 1000;
    assigns *fm, vp_freed[vp_nfreed], vp_nfreed;
    ensures vp_nfreed == \old(vp_nfreed) + 1 && vp_freed[\old(vp_nfreed)] == \old(fm->additional_data);
    ensures fm->mark.lnum == 0 && fm->mark.col == 0 && fm->mark.coladd == 0;
    ensures fm->fnum == 0 && fm->timestamp == timestamp;
    ensures fm->view.topline_offset == MAXLNUM && fm->view.skipcol == 0;
    ensures fm->additional_data == \null;""",
        "free_jumplist": r"""requires \valid(wp) && 0 <= wp->w_jumplistlen <= JUMPLISTSIZE;
    requires 0 <= vp_nfreed && vp_nfreed + 2 * wp->w_jumplistlen < 1000;
    assigns wp->w_jumplistlen, vp_freed[vp_nfreed .. vp_nfreed + 2 * wp->w_jumplistlen - 1], vp_nfreed;
    ensures wp->w_jumplistlen == 0 && vp_nfreed == \old(vp_nfreed) + 2 * \old(wp->w_jumplistlen);
    // each entry's file name, then its additional data, in list order
    ensures \forall integer i; 0 <= i < \old(wp->w_jumplistlen) ==>
      vp_freed[\old(vp_nfreed) + 2 * i] == \old(wp->w_jumplist[i].fname)
      && vp_freed[\old(vp_nfreed) + 2 * i + 1] == \old(wp->w_jumplist[i].fmark.additional_data);""",
        "clrallmarks": r"""requires \valid(buf) && 0 <= buf->b_changelistlen <= JUMPLISTSIZE;
    requires 0 <= vp_nfreed && vp_nfreed + NMARKS + 3 + buf->b_changelistlen < 1000;
    assigns *buf, vp_freed[vp_nfreed .. vp_nfreed + NMARKS + 2 + buf->b_changelistlen], vp_nfreed;
    ensures vp_nfreed == \old(vp_nfreed) + NMARKS + 3 + \old(buf->b_changelistlen);
    ensures \forall integer i; 0 <= i < NMARKS ==>
      init_fmark(&buf->b_namedm[i]) && buf->b_namedm[i].timestamp == timestamp
      && vp_freed[\old(vp_nfreed) + i] == \old(buf->b_namedm[i].additional_data);
    ensures init_fmark(&buf->b_last_insert) && buf->b_last_insert.timestamp == timestamp;
    ensures init_fmark(&buf->b_last_change) && buf->b_last_change.timestamp == timestamp;
    ensures buf->b_last_cursor.mark.lnum == 1 && buf->b_last_cursor.mark.col == 0 && buf->b_last_cursor.timestamp == timestamp
      && buf->b_last_cursor.fnum == 0 && buf->b_last_cursor.additional_data == \null;
    ensures vp_freed[\old(vp_nfreed) + NMARKS] == \old(buf->b_last_cursor.additional_data);
    ensures vp_freed[\old(vp_nfreed) + NMARKS + 1] == \old(buf->b_last_insert.additional_data);
    ensures vp_freed[\old(vp_nfreed) + NMARKS + 2] == \old(buf->b_last_change.additional_data);
    ensures \forall integer i; 0 <= i < \old(buf->b_changelistlen) ==>
      vp_freed[\old(vp_nfreed) + NMARKS + 3 + i] == \old(buf->b_changelist[i].additional_data);
    ensures buf->b_op_start.lnum == 0 && buf->b_op_end.lnum == 0 && buf->b_changelistlen == 0;""",
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
        "free_jumplist": [("  for (int i = 0; i < wp->w_jumplistlen; i++) {",
            r"""loop invariant 0 <= i <= wp->w_jumplistlen && vp_nfreed == \at(vp_nfreed, Pre) + 2 * i;
      loop invariant \forall integer j; 0 <= j < i ==>
        vp_freed[\at(vp_nfreed, Pre) + 2 * j] == wp->w_jumplist[j].fname
        && vp_freed[\at(vp_nfreed, Pre) + 2 * j + 1] == wp->w_jumplist[j].fmark.additional_data;
      loop assigns i, vp_nfreed, vp_freed[\at(vp_nfreed, Pre) .. \at(vp_nfreed, Pre) + 2 * wp->w_jumplistlen - 1];
      loop variant wp->w_jumplistlen - i;""")],
        "clrallmarks": [("  for (size_t i = 0; i < NMARKS; i++) {",
            r"""loop invariant 0 <= i <= NMARKS && vp_nfreed == \at(vp_nfreed, Pre) + i;
      loop invariant \forall integer j; 0 <= j < i ==>
        init_fmark(&buf->b_namedm[j]) && buf->b_namedm[j].timestamp == timestamp
        && vp_freed[\at(vp_nfreed, Pre) + j] == \at(buf->b_namedm[j].additional_data, Pre);
      loop invariant \forall integer j; i <= j < NMARKS ==> buf->b_namedm[j] == \at(buf->b_namedm[j], Pre);
      loop assigns i, vp_nfreed, buf->b_namedm[0 .. NMARKS - 1], vp_freed[\at(vp_nfreed, Pre) .. \at(vp_nfreed, Pre) + NMARKS - 1];
      loop variant NMARKS - i;"""),
            ("  for (int i = 0; i < buf->b_changelistlen; i++) {",
            r"""loop invariant 0 <= i <= buf->b_changelistlen && vp_nfreed == \at(vp_nfreed, Pre) + NMARKS + 3 + i;
      loop invariant buf->b_changelistlen == \at(buf->b_changelistlen, Pre);
      loop invariant \forall integer j; 0 <= j < NMARKS ==>
        init_fmark(&buf->b_namedm[j]) && buf->b_namedm[j].timestamp == timestamp
        && vp_freed[\at(vp_nfreed, Pre) + j] == \at(buf->b_namedm[j].additional_data, Pre);
      loop invariant init_fmark(&buf->b_last_insert) && buf->b_last_insert.timestamp == timestamp;
      loop invariant init_fmark(&buf->b_last_change) && buf->b_last_change.timestamp == timestamp;
      loop invariant buf->b_last_cursor.mark.lnum == 1 && buf->b_last_cursor.mark.col == 0 && buf->b_last_cursor.timestamp == timestamp
        && buf->b_last_cursor.fnum == 0 && buf->b_last_cursor.additional_data == \null;
      loop invariant vp_freed[\at(vp_nfreed, Pre) + NMARKS] == \at(buf->b_last_cursor.additional_data, Pre);
      loop invariant vp_freed[\at(vp_nfreed, Pre) + NMARKS + 1] == \at(buf->b_last_insert.additional_data, Pre);
      loop invariant vp_freed[\at(vp_nfreed, Pre) + NMARKS + 2] == \at(buf->b_last_change.additional_data, Pre);
      loop invariant buf->b_op_start.lnum == 0 && buf->b_op_end.lnum == 0;
      loop invariant \forall integer j; 0 <= j < i ==>
        vp_freed[\at(vp_nfreed, Pre) + NMARKS + 3 + j] == \at(buf->b_changelist[j].additional_data, Pre);
      loop invariant \forall integer j; i <= j < buf->b_changelistlen ==> buf->b_changelist[j] == \at(buf->b_changelist[j], Pre);
      loop assigns i, vp_nfreed, buf->b_changelist[0 .. JUMPLISTSIZE - 1],
        vp_freed[\at(vp_nfreed, Pre) + NMARKS + 3 .. \at(vp_nfreed, Pre) + NMARKS + 2 + buf->b_changelistlen];
      loop variant buf->b_changelistlen - i;""")],
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
