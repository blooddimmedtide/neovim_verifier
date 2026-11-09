"""ACSL for keycodes.c, written from the documented meaning of each function.

Table lookups are specified as "the first table entry that matches, else the
input unchanged", which is what the doc comments say; the specs do not restate
the table contents (75 shift/ctrl entries, 17 mouse entries).
"""

STUBS = r"""
/*@ requires \valid(buf + (0 .. 5));
    assigns buf[0 .. 5];
    ensures 1 <= \result <= 6;
    ensures c < 0x80 ==> \result == 1;
    ensures \forall integer i; 0 <= i < \result ==> c >= 0x80 ==> ((uint8_t)buf[i] != 0x80 || i > 0);
*/
int utf_char2bytes(const int c, char *const buf);
char *add_char2buf(int c, char *s);
"""

LOGIC = r"""
/*@
  logic integer up(integer c) = (c < 'a' || c > 'z') ? c : c - 32;
  predicate alpha(integer c) = ('A' <= c <= 'Z') || ('a' <= c <= 'z');

  // Documented modifier letters (keycodes.h MOD_MASK_*, :help <>).
  logic integer modbit(integer u) =
    (u == 'M' || u == 'A') ? 0x08 :
    u == 'T' ? 0x10 : u == 'C' ? 0x04 : u == 'S' ? 0x02 :
    u == '2' ? 0x20 : u == '3' ? 0x40 : u == '4' ? 0x60 : u == 'D' ? 0x80 : 0;

  logic integer tc0(integer k) = (-k) & 0xff;
  logic integer tc1(integer k) = (((-k) & 0xffffffff) >> 8) & 0xff;

  predicate mk_ok = modifier_keys_table[375] == 0 &&
    \forall integer j; 0 <= j < 75 ==> modifier_keys_table[5*j] != 0;
  // entry j is the first whose unshifted code is (a,b) and whose mask meets m
  predicate mk_hit(integer j, integer a, integer b, integer m) =
    modifier_keys_table[5*j+3] == a && modifier_keys_table[5*j+4] == b &&
    (m & modifier_keys_table[5*j]) != 0;
  predicate mk_rev(integer j, integer a, integer b) =
    modifier_keys_table[5*j+1] == a && modifier_keys_table[5*j+2] == b;

  predicate mt_ok = mouse_table[17].pseudo_code == 0 &&
    \forall integer j; 0 <= j < 17 ==> mouse_table[j].pseudo_code != 0;

  // vim_unescape_ks: output of unescaping the input from position i to the NUL at n.
  predicate esc3{L}(uint8_t *s, integer i) =
    s[i] == 0x80 && s[i+1] == 254 && s[i+2] == 'X';
  logic integer outlen{L}(uint8_t *s, integer i, integer n) =
    i >= n ? 0 : (esc3(s, i) ? 1 + outlen(s, i + 3, n) : 1 + outlen(s, i + 1, n));
  logic integer outbyte{L}(uint8_t *s, integer i, integer n, integer k) =
    i >= n ? 0 :
    (esc3(s, i) ? (k == 0 ? 0x80 : outbyte(s, i + 3, n, k - 1))
                : (k == 0 ? s[i] : outbyte(s, i + 1, n, k - 1)));
*/
"""

CONTRACTS = {
"name_to_mod_mask": r"""/*@ assigns \nothing;
    ensures \result == modbit(up(c));
*/
""",
"name_to_mod_mask.body": {
"  for (size_t i = 0; mod_mask_table[i].mod_mask != 0; i++) {":
"""  /*@ loop invariant 0 <= i <= 9;
      loop invariant c == up(\\at(c, Pre));
      loop invariant \\forall integer j; 0 <= j < i ==> c != (uint8_t)mod_mask_table[j].name;
      loop assigns i;
      loop variant 9 - i; */
"""},

"handle_x_keys": r"""/*@ assigns \nothing;
    ensures key == K_XUP ==> \result == K_UP;
    ensures key == K_XDOWN ==> \result == K_DOWN;
    ensures key == K_XLEFT ==> \result == K_LEFT;
    ensures key == K_XRIGHT ==> \result == K_RIGHT;
    ensures (key == K_XHOME || key == K_ZHOME) ==> \result == K_HOME;
    ensures (key == K_XEND || key == K_ZEND) ==> \result == K_END;
    ensures key == K_XF1 ==> \result == K_F1;
    ensures key == K_XF2 ==> \result == K_F2;
    ensures key == K_XF3 ==> \result == K_F3;
    ensures key == K_XF4 ==> \result == K_F4;
    ensures key == K_S_XF1 ==> \result == K_S_F1;
    ensures key == K_S_XF2 ==> \result == K_S_F2;
    ensures key == K_S_XF3 ==> \result == K_S_F3;
    ensures key == K_S_XF4 ==> \result == K_S_F4;
    ensures key != K_XUP && key != K_XDOWN && key != K_XLEFT && key != K_XRIGHT &&
            key != K_XHOME && key != K_ZHOME && key != K_XEND && key != K_ZEND &&
            key != K_XF1 && key != K_XF2 && key != K_XF3 && key != K_XF4 &&
            key != K_S_XF1 && key != K_S_XF2 && key != K_S_XF3 && key != K_S_XF4
            ==> \result == key;
*/
""",

"simplify_key": r"""/*@ requires \valid(modifiers);
    requires mk_ok;
    requires key != INT_MIN;  // see findings/keycodes-char-int-min.md
    assigns *modifiers;
    behavior none:
      assumes (*modifiers & (MOD_MASK_SHIFT | MOD_MASK_CTRL)) == 0;
      ensures \result == key && *modifiers == \old(*modifiers);
    behavior stab:
      assumes (*modifiers & (MOD_MASK_SHIFT | MOD_MASK_CTRL)) != 0;
      assumes key == TAB && (*modifiers & MOD_MASK_SHIFT) != 0;
      ensures \result == K_S_TAB && *modifiers == (\old(*modifiers) & ~MOD_MASK_SHIFT);
    behavior table:
      assumes (*modifiers & (MOD_MASK_SHIFT | MOD_MASK_CTRL)) != 0;
      assumes !(key == TAB && (*modifiers & MOD_MASK_SHIFT) != 0);
      ensures (\exists integer j; 0 <= j < 75 && mk_hit(j, tc0(key), tc1(key), \old(*modifiers))
                && (\forall integer k; 0 <= k < j ==> !mk_hit(k, tc0(key), tc1(key), \old(*modifiers)))
                && \result == -(modifier_keys_table[5*j+1] + modifier_keys_table[5*j+2] * 256)
                && *modifiers == (\old(*modifiers) & ~modifier_keys_table[5*j]))
           || ((\forall integer k; 0 <= k < 75 ==> !mk_hit(k, tc0(key), tc1(key), \old(*modifiers)))
                && \result == key && *modifiers == \old(*modifiers));
    complete behaviors; disjoint behaviors;
*/
""",
"simplify_key.body": {
"  for (int i = 0; modifier_keys_table[i] != NUL; i += MOD_KEYS_ENTRY_SIZE) {":
"""  /*@ loop invariant 0 <= i <= 375 && i % 5 == 0;
      loop invariant \\forall integer k; 0 <= k < i/5 ==> !mk_hit(k, key0, key1, *modifiers);
      loop invariant key0 == tc0(key) && key1 == tc1(key);
      loop invariant \\forall integer j; 0 <= j < 376 ==> 0 <= modifier_keys_table[j] <= 255;
      loop invariant *modifiers == \\at(*modifiers, Pre);
      loop assigns i;
      loop variant 375 - i; */
"""},

"unsimplify_key": r"""/*@ requires \valid(modifiers);
    requires mk_ok;
    requires c != INT_MIN;
    assigns *modifiers;
    behavior plain:
      assumes c >= 0;
      ensures \result == c && *modifiers == \old(*modifiers);
    behavior special:
      assumes c < 0;
      ensures (\exists integer j; 0 <= j < 75 && mk_rev(j, tc0(c), tc1(c))
                && (\forall integer k; 0 <= k < j ==> !mk_rev(k, tc0(c), tc1(c)))
                && \result == -(modifier_keys_table[5*j+3] + modifier_keys_table[5*j+4] * 256)
                && *modifiers == (\old(*modifiers) | modifier_keys_table[5*j]))
           || ((\forall integer k; 0 <= k < 75 ==> !mk_rev(k, tc0(c), tc1(c)))
                && \result == c && *modifiers == \old(*modifiers));
    complete behaviors; disjoint behaviors;
*/
""",
"unsimplify_key.body": {
"  for (int i = 0; modifier_keys_table[i] != NUL; i += MOD_KEYS_ENTRY_SIZE) {":
"""  /*@ loop invariant 0 <= i <= 375 && i % 5 == 0;
      loop invariant \\forall integer k; 0 <= k < i/5 ==> !mk_rev(k, tc0(c), tc1(c));
      loop invariant \\forall integer j; 0 <= j < 376 ==> 0 <= modifier_keys_table[j] <= 255;
      loop invariant *modifiers == \\at(*modifiers, Pre);
      loop assigns i;
      loop variant 375 - i; */
"""},

"get_mouse_button": r"""/*@ requires \valid(is_click) && \valid(is_drag) && \separated(is_click, is_drag);
    requires mt_ok;
    assigns *is_click, *is_drag;
    behavior found:
      assumes \exists integer j; 0 <= j < 17 && mouse_table[j].pseudo_code == code;
      ensures \exists integer j; 0 <= j < 17 && mouse_table[j].pseudo_code == code
        && (\forall integer k; 0 <= k < j ==> mouse_table[k].pseudo_code != code)
        && \result == mouse_table[j].button
        && *is_click == mouse_table[j].is_click && *is_drag == mouse_table[j].is_drag;
    behavior missing:
      assumes \forall integer j; 0 <= j < 17 ==> mouse_table[j].pseudo_code != code;
      ensures \result == 0 && *is_click == \old(*is_click) && *is_drag == \old(*is_drag);
    complete behaviors; disjoint behaviors;
*/
""",
"get_mouse_button.body": {
"  for (int i = 0; mouse_table[i].pseudo_code; i++) {":
"""  /*@ loop invariant 0 <= i <= 17;
      loop invariant \\forall integer k; 0 <= k < i ==> mouse_table[k].pseudo_code != code;
      loop assigns i;
      loop variant 17 - i; */
"""},

"extract_modifiers": r"""/*@ requires \valid(modp);
    requires did_simplify == \null || (\valid(did_simplify) && \separated(modp, did_simplify));
    assigns *modp, *did_simplify;
    // Shift on a letter becomes the upper-case letter; Shift kept only with Ctrl.
    // Ctrl on a letter always uses the upper-case letter.
    // With simplify, Ctrl on '?'..'_' or a letter becomes the control character
    // (Ctrl-@ becomes K_ZERO) and Ctrl is removed.
    ensures \let m = \old(*modp);
            \let k1 = ((m & 2) != 0 && alpha(key)) ? up(key) : key;
            \let m1 = ((m & 2) != 0 && alpha(key) && (m & 4) == 0) ? (m & ~2) : m;
            \let k2 = ((m1 & 4) != 0 && alpha(k1)) ? up(k1) : k1;
            \let s = simplify && (m1 & 4) != 0 && (('?' <= k2 <= '_') || alpha(k2));
            \let k3 = up(k2) ^ 0x40;
            (s ==> (\result == (k3 == 0 ? K_ZERO : k3) && *modp == (m1 & ~4)
                    && (did_simplify != \null ==> *did_simplify == \true)))
         && (!s ==> (\result == k2 && *modp == m1
                    && (did_simplify != \null ==> *did_simplify == \old(*did_simplify))));
*/
""",



"vim_unescape_ks": r"""/*@ requires \valid(p + (0 .. n)) && p[n] == 0;
    requires \forall integer k; 0 <= k < n ==> p[k] != 0;
    requires n < SIZE_MAX;
    assigns p[0 .. n];
    // Every K_SPECIAL KS_SPECIAL KE_FILLER triple becomes one K_SPECIAL byte,
    // scanning left to right; everything else is copied; result is the new length.
    ensures \result == outlen{Pre}((uint8_t *)p, 0, n);
    ensures \forall integer k; 0 <= k < \result ==>
              (uint8_t)p[k] == outbyte{Pre}((uint8_t *)p, 0, n, k);
    ensures p[\result] == 0;
*/
""",
"vim_unescape_ks.body": {
"\n{\n  uint8_t *s = (uint8_t *)p;": " /*@ ghost (size_t n) */",
"  while (*s != NUL) {":
"""  /*@ loop invariant (uint8_t *)p <= d <= s <= (uint8_t *)p + n;
      loop invariant \\forall integer j; s - (uint8_t *)p <= j <= n ==> p[j] == \\at(p[j], Pre);
      loop invariant outlen{Pre}((uint8_t *)p, 0, n)
                     == (d - (uint8_t *)p) + outlen{Pre}((uint8_t *)p, s - (uint8_t *)p, n);
      loop invariant \\forall integer k; 0 <= k < d - (uint8_t *)p ==>
                     (uint8_t)p[k] == outbyte{Pre}((uint8_t *)p, 0, n, k);
      loop invariant \\forall integer k; d - (uint8_t *)p <= k ==>
                     outbyte{Pre}((uint8_t *)p, 0, n, k)
                     == outbyte{Pre}((uint8_t *)p, s - (uint8_t *)p, n, k - (d - (uint8_t *)p));
      loop assigns s, d, p[0 .. n];
      loop variant (uint8_t *)p + n - s; */
"""},
}
