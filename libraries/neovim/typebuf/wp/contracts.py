"""ACSL contracts for the typeahead (typebuf) and stuff buffer (readbuf1/2) functions of
input.c, written from the comments in input.c / input_defs.h (the typebuf layout comment
above `enum { RM_YES ...}` and each function's doc comment)."""

LOGIC = r"""
/*@ // a stuff buffer: bytes [0, size) live in items, [read, size) unread, read <= insert <= size
    predicate sb_ok{L}(StuffBuf *b) =
      \valid(b) && b->read <= b->insert <= b->keys.size <= b->keys.capacity
      && (b->keys.capacity > 0 ==> b->keys.items != \null
          && \valid(b->keys.items + (0 .. b->keys.capacity - 1)))
      && (b->keys.items == \null ==> b->keys.capacity == 0)
      && \base_addr(b->keys.items) != \base_addr(b);
    // the typeahead buffer, as the comment above enum RM_YES describes it:
    // tb_buf[tb_off .. tb_off + tb_len - 1] are the chars, tb_buf[tb_off + tb_len] is NUL;
    // tb_noremap has the same length; the counts are prefixes of the chars.
    predicate tb_ok{L} =
      typebuf.tb_buf != \null && typebuf.tb_noremap != \null
      && 0 < typebuf.tb_buflen
      && \valid(typebuf.tb_buf + (0 .. typebuf.tb_buflen - 1))
      && \valid(typebuf.tb_noremap + (0 .. typebuf.tb_buflen - 1))
      && \base_addr(typebuf.tb_buf) != \base_addr(typebuf.tb_noremap)
      && \base_addr(typebuf.tb_buf) != \base_addr(&typebuf)
      && \base_addr(typebuf.tb_noremap) != \base_addr(&typebuf)
      && 0 <= typebuf.tb_off && 0 <= typebuf.tb_len
      && typebuf.tb_off + typebuf.tb_len < typebuf.tb_buflen
      && 0 <= typebuf.tb_maplen <= typebuf.tb_len
      && 0 <= typebuf.tb_silent <= typebuf.tb_len
      && 0 <= typebuf.tb_no_abbr_cnt <= typebuf.tb_len
      && typebuf.tb_change_cnt != 0;
    // the change counter after one change: never zero
    logic integer next_cnt(integer c) = c + 1 == 0 ? 1 : c + 1;
    // a prefix count after deleting len chars at offset
    logic integer cnt_del(integer c, integer off, integer len) =
      c > off ? (c < off + len ? off : c - len) : c;
    // the flag ins_typebuf gives new char i (doc comment of ins_typebuf)
    logic integer nr_val(integer noremap) =
      noremap == REMAP_SCRIPT ? RM_SCRIPT : noremap == REMAP_SKIP ? RM_ABBR : RM_NONE;
    logic integer nr_count(integer noremap, integer n) =
      noremap == REMAP_SKIP ? 1 : noremap < 0 ? n : noremap;
    logic integer nr_flag(integer noremap, integer n, integer i) =
      i < nr_count(noremap, n) ? nr_val(noremap) : RM_YES;
*/
"""

FIXED = False


def contracts(fixed):
    # Upstream: `++typebuf.tb_change_cnt` overflows an int before the "== 0" test can wrap it
    # (findings/typebuf-change-cnt-overflow.md), so upstream is proved for counts below INT_MAX.
    cnt_ok = "" if fixed else "\n    requires typebuf.tb_change_cnt != INT_MAX;   // upstream only: see findings"
    C = {}
    C["free_buff"] = r"""requires sb_ok(buf) && (buf->keys.items != \null ==> vp_live > LONG_MIN);
    assigns *buf, vp_live;
    ensures buf->keys.size == 0 && buf->keys.capacity == 0 && buf->keys.items == \null;
    ensures buf->read == 0 && buf->insert == 0;
    ensures vp_live == \old(vp_live) - (\old(buf->keys.items) == \null ? 0 : 1);"""

    C["add_buff"] = r"""requires sb_ok(buf) && vp_live < LONG_MAX;
    requires slen >= 0 ==> \valid_read(s + (0 .. slen - 1));
    requires slen < 0 ==> is_str((char *)s);
    // "s must not point into buf->keys"
    requires \base_addr(s) != \base_addr(buf->keys.items) && \base_addr(s) != \base_addr(buf);
    // the buffer stays far from SIZE_MAX (kv_roundup32 would wrap to 0 near it)
    requires buf->keys.size <= SIZE_MAX / 4;
    requires slen < 0 ==> \forall integer n; str_len((char *)s, n) ==> n <= SIZE_MAX / 4;
    requires slen <= SIZE_MAX / 4;
    exits vp_oom;
    assigns buf->keys, buf->insert, vp_live, buf->keys.items[0 .. \at(buf->keys.capacity, Post) - 1],
            ((char *)\at(buf->keys.items, Post))[0 .. \at(buf->keys.capacity, Post) - 1];
    behavior add:
      assumes slen > 0 || (slen < 0 && !str_len((char *)s, 0));
      ensures sb_ok(buf) && buf->read == \old(buf->read);
      ensures \exists integer n; n > 0 && (\old(slen) > 0 ? n == \old(slen) : str_len{Pre}((char *)s, n))
        && buf->keys.size == \old(buf->keys.size) + n && buf->insert == \old(buf->insert) + n
        && (\forall integer i; 0 <= i < \old(buf->insert) ==> buf->keys.items[i] == \old(buf->keys.items[i]))
        && (\forall integer i; 0 <= i < n ==> buf->keys.items[\old(buf->insert) + i] == \at(s[i], Pre))
        && (\forall integer i; \old(buf->insert) <= i < \old(buf->keys.size) ==>
              buf->keys.items[i + n] == \old(buf->keys.items[i]));
    behavior empty:
      assumes slen == 0 || (slen < 0 && str_len((char *)s, 0));
      ensures buf->keys == \old(buf->keys) && buf->insert == \old(buf->insert) && vp_live == \old(vp_live);
    complete behaviors; disjoint behaviors;"""

    C["read_readbuf"] = r"""requires sb_ok(buf);
    assigns buf->read, buf->insert, buf->keys.size;
    ensures sb_ok(buf);
    behavior empty:
      assumes buf->read == buf->keys.size;
      ensures \result == NUL && buf->read == \old(buf->read) && buf->insert == \old(buf->insert)
              && buf->keys.size == \old(buf->keys.size);
    behavior peek:
      assumes buf->read < buf->keys.size && !advance;
      ensures \result == (uint8_t)buf->keys.items[buf->read];
      ensures buf->read == \old(buf->read) && buf->insert == \old(buf->insert) && buf->keys.size == \old(buf->keys.size);
    behavior last:
      assumes buf->read + 1 == buf->keys.size && advance;
      ensures \result == (uint8_t)buf->keys.items[\old(buf->read)];
      ensures buf->read == 0 && buf->insert == 0 && buf->keys.size == 0;
    behavior next:
      assumes buf->read + 1 < buf->keys.size && advance;
      ensures \result == (uint8_t)buf->keys.items[\old(buf->read)];
      ensures buf->read == \old(buf->read) + 1 && buf->keys.size == \old(buf->keys.size);
      ensures buf->insert == (\old(buf->insert) > buf->read ? \old(buf->insert) : buf->read);
    complete behaviors; disjoint behaviors;"""

    C["read_readbuffers"] = r"""requires sb_ok(&readbuf1) && sb_ok(&readbuf2);
    requires \base_addr(readbuf1.keys.items) != \base_addr(&readbuf2);
    requires \base_addr(readbuf2.keys.items) != \base_addr(&readbuf1);
    assigns readbuf1.read, readbuf1.insert, readbuf1.keys.size,
            readbuf2.read, readbuf2.insert, readbuf2.keys.size;
    ensures sb_ok(&readbuf1) && sb_ok(&readbuf2);
    behavior one:   // readbuf1 has an unread byte that is not NUL: it is read, readbuf2 untouched
      assumes readbuf1.read < readbuf1.keys.size && readbuf1.keys.items[readbuf1.read] != 0;
      ensures \result == (uint8_t)\old(readbuf1.keys.items[readbuf1.read]);
      ensures readbuf2.read == \old(readbuf2.read) && readbuf2.insert == \old(readbuf2.insert)
              && readbuf2.keys.size == \old(readbuf2.keys.size);
    behavior two:   // otherwise the byte comes from readbuf2 (NUL if both are empty)
      assumes !(readbuf1.read < readbuf1.keys.size && readbuf1.keys.items[readbuf1.read] != 0);
      ensures \result == (\old(readbuf2.read) == \old(readbuf2.keys.size) ? 0
                          : (uint8_t)\old(readbuf2.keys.items[readbuf2.read]));
    complete behaviors; disjoint behaviors;"""

    C["start_stuff"] = r"""requires \valid(&readbuf1) && \valid(&readbuf2);
    assigns readbuf1.insert, readbuf2.insert;
    ensures readbuf1.insert == readbuf1.read && readbuf2.insert == readbuf2.read;"""

    C["stuff_empty"] = r"""assigns \nothing;
    ensures \result <==> (readbuf1.keys.size == 0 && readbuf2.keys.size == 0);"""

    C["readbuf1_empty"] = r"""assigns \nothing;
    ensures \result <==> readbuf1.keys.size == 0;"""

    C["init_typebuf"] = r"""requires typebuf.tb_buf != \null ==> tb_ok;
    requires typebuf.tb_buf == \null ==> 0 <= typebuf.tb_maplen <= 0 && 0 <= typebuf.tb_silent <= 0
                                         && 0 <= typebuf.tb_no_abbr_cnt <= 0;
    requires typebuf.tb_buf == \null ==> typebuf_init[MAXMAPLEN + 4] == 0;
    assigns typebuf.tb_buf, typebuf.tb_noremap, typebuf.tb_buflen, typebuf.tb_len,
            typebuf.tb_off, typebuf.tb_change_cnt;
    ensures tb_ok;
    behavior ready:
      assumes typebuf.tb_buf != \null;
      ensures typebuf == \old(typebuf);
    behavior init:
      assumes typebuf.tb_buf == \null;
      ensures typebuf.tb_buf == &typebuf_init[0] && typebuf.tb_noremap == &noremapbuf_init[0];
      ensures typebuf.tb_buflen == TYPELEN_INIT && typebuf.tb_len == 0;
      ensures typebuf.tb_off == MAXMAPLEN + 4 && typebuf.tb_change_cnt == 1;
    complete behaviors; disjoint behaviors;"""

    C["typebuf_changed"] = r"""assigns \nothing;
    ensures \result <==> (tb_change_cnt != 0
                          && (typebuf.tb_change_cnt != tb_change_cnt || typebuf_was_filled));"""
    C["typebuf_typed"] = r"""assigns \nothing;
    ensures \result == (typebuf.tb_maplen == 0 ? 1 : 0);"""
    C["typebuf_maplen"] = r"""assigns \nothing;
    ensures \result == typebuf.tb_maplen;"""

    C["del_typebuf"] = r"""requires tb_ok;
    requires 0 <= offset && 0 <= len && offset + len <= typebuf.tb_len;""" + cnt_ok + r"""
    assigns typebuf.tb_len, typebuf.tb_off, typebuf.tb_maplen, typebuf.tb_silent,
            typebuf.tb_no_abbr_cnt, typebuf.tb_change_cnt, typebuf_was_filled,
            ((char *)typebuf.tb_buf)[0 .. typebuf.tb_buflen - 1],
            ((char *)typebuf.tb_noremap)[0 .. typebuf.tb_buflen - 1];
    behavior nothing:
      assumes len == 0;
      ensures typebuf == \old(typebuf) && typebuf_was_filled == \old(typebuf_was_filled);
    behavior del:
      assumes len > 0;
      ensures tb_ok && typebuf.tb_buf == \old(typebuf.tb_buf) && typebuf.tb_noremap == \old(typebuf.tb_noremap)
              && typebuf.tb_buflen == \old(typebuf.tb_buflen);
      ensures typebuf.tb_len == \old(typebuf.tb_len) - len;
      // chars before offset kept, the len chars at offset removed, the rest (and the NUL) moved up
      ensures \forall integer i; 0 <= i < offset ==>
        ((char *)typebuf.tb_buf)[typebuf.tb_off + i] == \old(((char *)typebuf.tb_buf)[typebuf.tb_off + i])
        && ((char *)typebuf.tb_noremap)[typebuf.tb_off + i] == \old(((char *)typebuf.tb_noremap)[typebuf.tb_off + i]);
      ensures \forall integer i; offset <= i < typebuf.tb_len ==>
        ((char *)typebuf.tb_buf)[typebuf.tb_off + i] == \old(((char *)typebuf.tb_buf)[typebuf.tb_off + i + len])
        && ((char *)typebuf.tb_noremap)[typebuf.tb_off + i] == \old(((char *)typebuf.tb_noremap)[typebuf.tb_off + i + len]);
      ensures ((char *)typebuf.tb_buf)[typebuf.tb_off + typebuf.tb_len]
              == \old(((char *)typebuf.tb_buf)[typebuf.tb_off + typebuf.tb_len]);
      ensures typebuf.tb_maplen == cnt_del(\old(typebuf.tb_maplen), offset, len);
      ensures typebuf.tb_silent == cnt_del(\old(typebuf.tb_silent), offset, len);
      ensures typebuf.tb_no_abbr_cnt == cnt_del(\old(typebuf.tb_no_abbr_cnt), offset, len);
      ensures typebuf_was_filled == \false;
      ensures typebuf.tb_change_cnt == next_cnt(\old(typebuf.tb_change_cnt));
    complete behaviors; disjoint behaviors;"""

    C["alloc_typebuf"] = r"""requires vp_live < LONG_MAX - 1;""" + cnt_ok + r"""
    exits vp_oom;
    assigns typebuf, typebuf_was_filled, vp_live;
    ensures typebuf.tb_buf != \null && typebuf.tb_noremap != \null;
    ensures \valid(typebuf.tb_buf + (0 .. TYPELEN_INIT - 1)) && \valid(typebuf.tb_noremap + (0 .. TYPELEN_INIT - 1));
    ensures \base_addr(typebuf.tb_buf) != \base_addr(typebuf.tb_noremap);
    ensures \forall char *q; \at(\valid_read(q), Pre) ==>
      \base_addr(q) != \base_addr((char *)typebuf.tb_buf) && \base_addr(q) != \base_addr((char *)typebuf.tb_noremap);
    ensures typebuf.tb_buflen == TYPELEN_INIT && typebuf.tb_off == MAXMAPLEN + 4 && typebuf.tb_len == 0;
    ensures typebuf.tb_maplen == 0 && typebuf.tb_silent == 0 && typebuf.tb_no_abbr_cnt == 0;
    ensures typebuf.tb_change_cnt == next_cnt(\old(typebuf.tb_change_cnt));
    ensures typebuf_was_filled == \false && vp_live == \old(vp_live) + 2;"""

    C["free_typebuf"] = r"""requires vp_live > LONG_MIN + 2;
    assigns typebuf.tb_buf, typebuf.tb_noremap, vp_live;
    // the static initial buffers are never freed (internal_error instead)
    ensures typebuf.tb_buf == (\old(typebuf.tb_buf) == &typebuf_init[0] ? &typebuf_init[0] : (uint8_t *)\null);
    ensures typebuf.tb_noremap == (\old(typebuf.tb_noremap) == &noremapbuf_init[0] ? &noremapbuf_init[0] : (uint8_t *)\null);
    ensures vp_live == \old(vp_live)
      - (\old(typebuf.tb_buf) == &typebuf_init[0] || \old(typebuf.tb_buf) == \null ? 0 : 1)
      - (\old(typebuf.tb_noremap) == &noremapbuf_init[0] || \old(typebuf.tb_noremap) == \null ? 0 : 1);"""

    # ins_typebuf. Upstream takes the length as (int)strlen(str): a string of 2^31 bytes or
    # more gives a negative length (findings/ins-typebuf-strlen-truncation.md), so upstream is
    # proved for strings shorter than 2^31.
    up_len = "" if fixed else "\n    requires n <= INT_MAX;   // upstream only: see findings"
    C["ins_typebuf"] = r"""requires typebuf.tb_buf != \null ==> tb_ok;
    requires typebuf.tb_buf == \null ==> typebuf.tb_maplen == 0 && typebuf.tb_silent == 0
                                         && typebuf.tb_no_abbr_cnt == 0 && typebuf_init[MAXMAPLEN + 4] == 0;
    requires str_len(str, n);""" + up_len + cnt_ok + r"""
    requires 0 <= offset && (typebuf.tb_buf != \null ==> offset <= typebuf.tb_len)
             && (typebuf.tb_buf == \null ==> offset == 0);
    requires \base_addr(str) != \base_addr(typebuf.tb_buf) && \base_addr(str) != \base_addr(typebuf.tb_noremap);
    requires \base_addr(str) != \base_addr(&typebuf_init[0]) && \base_addr(str) != \base_addr(&noremapbuf_init[0]);
    requires vp_live < LONG_MAX - 2 && vp_live > LONG_MIN + 2;
    exits vp_oom;
    assigns typebuf, cmd_silent, typebuf_was_filled, vp_live,
            ((char *)\at(typebuf.tb_buf, Post))[0 .. \at(typebuf.tb_buflen, Post) - 1],
            ((char *)\at(typebuf.tb_noremap, Post))[0 .. \at(typebuf.tb_buflen, Post) - 1],
            \at(typebuf.tb_noremap, Post)[0 .. \at(typebuf.tb_buflen, Post) - 1],
            typebuf.tb_buf[0 .. typebuf.tb_buflen - 1], typebuf.tb_noremap[0 .. typebuf.tb_buflen - 1];
    behavior too_long:   // E74 "Command too complex": FAIL
      assumes !(offset == 0 && n <= (typebuf.tb_buf == \null ? MAXMAPLEN + 4 : typebuf.tb_off))
           && !((typebuf.tb_buf == \null || typebuf.tb_len == 0)
                && (typebuf.tb_buf == \null ? TYPELEN_INIT : typebuf.tb_buflen) >= n + 3 * (MAXMAPLEN + 4))
           && (typebuf.tb_buf == \null ? 0 : typebuf.tb_len) > INT_MAX - (n + 5 * (MAXMAPLEN + 4));
      ensures \result == FAIL;
    behavior ok:
      assumes (offset == 0 && n <= (typebuf.tb_buf == \null ? MAXMAPLEN + 4 : typebuf.tb_off))
           || ((typebuf.tb_buf == \null || typebuf.tb_len == 0)
                && (typebuf.tb_buf == \null ? TYPELEN_INIT : typebuf.tb_buflen) >= n + 3 * (MAXMAPLEN + 4))
           || (typebuf.tb_buf == \null ? 0 : typebuf.tb_len) <= INT_MAX - (n + 5 * (MAXMAPLEN + 4));
      ensures \result == OK && tb_ok;
      ensures typebuf.tb_len == (\old(typebuf.tb_buf) == \null ? 0 : \old(typebuf.tb_len)) + n;
      ensures \forall integer i; 0 <= i < n ==>
        ((char *)typebuf.tb_buf)[typebuf.tb_off + offset + i] == \old(str[i])
        && typebuf.tb_noremap[typebuf.tb_off + offset + i] == nr_flag(noremap, n, i);
      ensures \old(typebuf.tb_buf) != \null ==> \forall integer i; 0 <= i < offset ==>
        ((char *)typebuf.tb_buf)[typebuf.tb_off + i] == \old(((char *)typebuf.tb_buf)[typebuf.tb_off + i])
        && ((char *)typebuf.tb_noremap)[typebuf.tb_off + i] == \old(((char *)typebuf.tb_noremap)[typebuf.tb_off + i]);
      ensures \old(typebuf.tb_buf) != \null ==> \forall integer i; offset <= i < \old(typebuf.tb_len) ==>
        ((char *)typebuf.tb_buf)[typebuf.tb_off + n + i] == \old(((char *)typebuf.tb_buf)[typebuf.tb_off + i])
        && ((char *)typebuf.tb_noremap)[typebuf.tb_off + n + i] == \old(((char *)typebuf.tb_noremap)[typebuf.tb_off + i]);
      ensures typebuf.tb_maplen == \old(typebuf.tb_maplen) + (nottyped || \old(typebuf.tb_maplen) > offset ? n : 0);
      ensures typebuf.tb_silent == \old(typebuf.tb_silent) + (silent || \old(typebuf.tb_silent) > offset ? n : 0);
      ensures typebuf.tb_no_abbr_cnt == \old(typebuf.tb_no_abbr_cnt)
                                        + (\old(typebuf.tb_no_abbr_cnt) != 0 && offset == 0 ? n : 0);
      ensures cmd_silent == (silent || \old(typebuf.tb_silent) > offset ? \true : \old(cmd_silent));
      ensures typebuf.tb_change_cnt == next_cnt(\old(typebuf.tb_buf) == \null ? 1 : \old(typebuf.tb_change_cnt));
    complete behaviors; disjoint behaviors;"""
    return C


def annotations(fixed):
    A = {}
    A["ins_typebuf"] = [
        ("after", "int ins_typebuf(char *str, int noremap, int offset, bool nottyped, bool silent)", "ghost (size_t n)"),
        ("before", "  for (int i = 0; i < addlen; i++) {",
         r"""loop invariant 0 <= i <= addlen;
        loop invariant nrm == nr_count(noremap, addlen) - i;
        loop invariant \forall integer k; 0 <= k < i ==>
          typebuf.tb_noremap[typebuf.tb_off + k + offset] == nr_flag(noremap, addlen, k);
        loop assigns i, nrm, typebuf.tb_noremap[typebuf.tb_off + offset .. typebuf.tb_off + offset + addlen - 1];
        loop variant addlen - i;"""),
    ]
    return A
