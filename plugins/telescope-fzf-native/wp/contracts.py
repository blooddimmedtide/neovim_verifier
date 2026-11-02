"""ACSL contracts for fzf.c's small helpers, from fzf's definitions (algo.go)."""

LOGIC = r"""
/*@ // fzf's character classes (numbered as fzf.c's char_types documents them:
    // 0 non-word, 1 lower, 2 upper, 4 number). Bytes >= 0x80 are non-word.
    logic integer cls(char c) =
      (97 <= c <= 122) ? 1 : (65 <= c <= 90) ? 2 : (48 <= c <= 57) ? 4 : 0;
    // fzf's bonusFor: 8 entering a word from a non-word char; 7 for
    // lower->Upper or non-digit->digit; 8 on a non-word char; else 0.
    logic integer bonus(integer p, integer c) =
      (p == 0 && c != 0) ? 8 :
      ((p == 1 && c == 2) || (p != 4 && c == 4)) ? 7 :
      (c == 0) ? 8 : 0;
    // C-locale whitespace, on the byte value
    predicate white(char c) = (unsigned char)c == 32 || 9 <= (unsigned char)c <= 13;
*/
"""

STR = r"""\valid_read(s) && \valid_read(s->data + (0 .. s->size - 1))"""

CONTRACTS = {
"index_byte": r"""requires \valid_read(string) && \valid_read(string->data + (0 .. string->size - 1));
    requires string->size <= 2147483647;   // texts below 2 GiB (the result is an int32_t)
    assigns \nothing;
    behavior found:
      assumes \exists integer i; 0 <= i < string->size && string->data[i] == b;
      ensures 0 <= \result < string->size && string->data[\result] == b;
      ensures \forall integer j; 0 <= j < \result ==> string->data[j] != b;
    behavior absent:
      assumes \forall integer i; 0 <= i < string->size ==> string->data[i] != b;
      ensures \result == -1;
    complete behaviors; disjoint behaviors;""",

"leading_whitespaces": r"""requires \valid_read(str) && \valid_read(str->data + (0 .. str->size - 1));
    assigns \nothing;
    ensures 0 <= \result <= str->size;
    ensures \forall integer j; 0 <= j < \result ==> white(str->data[j]);
    ensures \result == str->size || !white(str->data[\result]);""",

"trailing_whitespaces": r"""requires \valid_read(str) && \valid_read(str->data + (0 .. str->size - 1));
    assigns \nothing;
    ensures 0 <= \result <= str->size;
    ensures \forall integer j; str->size - \result <= j < str->size ==> white(str->data[j]);
    ensures \result == str->size || !white(str->data[str->size - \result - 1]);""",

"copy_runes": r"""requires \valid_read(src) && \valid_read(src->data + (0 .. src->size - 1));
    requires \valid_read(destination) && \valid(destination->data + (0 .. src->size - 1));
    requires \separated(destination->data + (0 .. src->size - 1), src, destination, src->data + (0 .. src->size - 1));
    assigns destination->data[0 .. src->size - 1];
    ensures \forall integer i; 0 <= i < src->size ==> destination->data[i] == src->data[i];""",

"copy_into_i16": r"""requires \valid_read(src) && \valid_read(src->data + (0 .. src->size - 1));
    requires \valid_read(dest) && \valid(dest->data + (0 .. src->size - 1));
    requires \separated(dest->data + (0 .. src->size - 1), src, dest, src->data + (0 .. src->size - 1));
    assigns dest->data[0 .. src->size - 1];
    ensures \forall integer i; 0 <= i < src->size ==> dest->data[i] == \old(src->data[i]);""",

# What the code does (findings/trim-whitespace-left.md): it skips leading ' '
# but stops after ceil(len/2) of them.
"trim_whitespace_left": r"""requires \valid(len) && \valid_read(str + (0 .. *len - 1)) && \separated(len, str + (0 .. *len - 1));
    assigns *len;
    ensures str <= \result <= str + \old(*len) && \result - str <= (\old(*len) + 1) / 2;
    ensures *len == \old(*len) - (\result - str);
    ensures \forall char *q; \base_addr(q) == \base_addr(str) && str <= q < \result ==> *q == ' ';
    ensures \result - str == (\old(*len) + 1) / 2 || *\result != ' ';""",

"max16": r"""assigns \nothing;
    ensures \result == (a > b ? a : b);""",
"min64u": r"""assigns \nothing;
    ensures \result == (a < b ? a : b);""",
"char_class_of_ascii": r"""assigns \nothing;
    ensures \result == cls(ch);""",
"char_class_of": r"""assigns \nothing;
    ensures \result == cls(ch);""",
"bonus_for": r"""requires 0 <= prev_class <= 4 && 0 <= class <= 4;
    assigns \nothing;
    ensures \result == bonus(prev_class, class);""",
"bonus_at": r"""requires \valid_read(input) && \valid_read(input->data + (0 .. input->size - 1));
    requires idx < input->size;
    assigns \nothing;
    ensures \result == (idx == 0 ? 8 : bonus(cls(input->data[idx - 1]), cls(input->data[idx])));""",
"normalize_rune": r"""assigns \nothing;
    ensures \result == r;""",
"is_ascii": r"""assigns \nothing;
    ensures \result == \true;""",
}

LOOPS = {
"index_byte": [("  for (size_t i = 0; i < string->size; i++) {",
    r"""loop invariant 0 <= i <= string->size;
      loop invariant \forall integer j; 0 <= j < i ==> string->data[j] != b;
      loop assigns i; loop variant string->size - i;""")],
"leading_whitespaces": [("  for (size_t i = 0; i < str->size; i++) {",
    r"""loop invariant 0 <= i <= str->size && whitespaces == i;
      loop invariant \forall integer j; 0 <= j < i ==> white(str->data[j]);
      loop assigns i, whitespaces; loop variant str->size - i;""")],
"trailing_whitespaces": [("  for (size_t i = str->size; i > 0; i--) {",
    r"""loop invariant 0 <= i <= str->size && whitespaces == str->size - i;
      loop invariant \forall integer j; i <= j < str->size ==> white(str->data[j]);
      loop assigns i, whitespaces; loop variant i;""")],
"copy_runes": [("  for (size_t i = 0; i < src->size; i++) {",
    r"""loop invariant 0 <= i <= src->size;
      loop invariant \forall integer j; 0 <= j < i ==> destination->data[j] == src->data[j];
      loop assigns i, destination->data[0 .. src->size - 1]; loop variant src->size - i;""")],
"copy_into_i16": [("  for (size_t i = 0; i < src->size; i++) {",
    r"""loop invariant 0 <= i <= src->size;
      loop invariant \forall integer j; 0 <= j < i ==> dest->data[j] == \at(src->data[j], Pre);
      loop assigns i, dest->data[0 .. src->size - 1]; loop variant src->size - i;""")],
"trim_whitespace_left": [("  for (size_t i = 0; i < *len; i++) {",
    r"""loop invariant 0 <= i <= (\at(*len, Pre) + 1) / 2 && str == \at(str, Pre) + i && *len == \at(*len, Pre) - i;
      loop invariant \forall char *q; \base_addr(q) == \base_addr(str) && \at(str, Pre) <= q < str ==> *q == ' ';
      loop assigns i, str, *len; loop variant \at(*len, Pre) - 2 * i;""")],
}
