"""ACSL for register.c / ops.c helpers. The reference is written from the documentation:
the operator names come from the comments on the OP_* enum in ops.h and :help operator;
"works on lines" / "changes text" from :help (linewise operators, text-changing operators);
register numbering from the comment above DELETION_REGISTER in register_defs.h and :help registers.
Nothing here reuses opchars[] or the code's helpers."""

LOGIC = r"""
/*@
  // Command characters of operator op (ops.h: "d" delete, "g~" switch case, ...).
  logic integer op_c1(integer op) =
    op == 0 ? 0 : op == 1 ? 'd' : op == 2 ? 'y' : op == 3 ? 'c' : op == 4 ? '<' :
    op == 5 ? '>' : op == 6 ? '!' : op == 7 ? 'g' : op == 8 ? '=' : op == 9 ? 'g' :
    op == 10 ? ':' : op == 11 ? 'g' : op == 12 ? 'g' : op == 13 ? 'J' : op == 14 ? 'g' :
    op == 15 ? 'g' : op == 16 ? 'r' : op == 17 ? 'I' : op == 18 ? 'A' : op == 28 ? 1 :
    op == 29 ? 24 : op == 27 ? 'g' : op == 26 ? 'g' : 'z';   // 19..25 and 30 are z-commands
  logic integer op_c2(integer op) =
    op == 7 ? '~' : op == 9 ? 'q' : op == 11 ? 'U' : op == 12 ? 'u' : op == 14 ? 'J' :
    op == 15 ? '?' : op == 19 ? 'f' : op == 20 ? 'o' : op == 21 ? 'O' : op == 22 ? 'c' :
    op == 23 ? 'C' : op == 24 ? 'd' : op == 25 ? 'D' : op == 26 ? 'w' : op == 27 ? '@' :
    op == 30 ? 'q' : 0;
  // Linewise operators (:help linewise): < > ! = gq gw : J gJ and the fold open/close/delete ops.
  predicate op_lines(integer op) =
    op == 4 || op == 5 || op == 6 || op == 8 || op == 9 || op == 10 || op == 13 ||
    op == 14 || (20 <= op <= 25) || op == 26;
  // Operators that change text: everything except no-op, yank, ':', the fold ops and zq.
  predicate op_changes(integer op) =
    !(op == 0 || op == 2 || op == 10 || (19 <= op <= 25) || op == 30);
  // The two flag bits of a value 0..3 (both lemmas are proved, see run_wp.sh "lemmas").
  lemma flag_bits: (0 & 1) == 0 && (1 & 1) == 1 && (2 & 1) == 0 && (3 & 1) == 1 &&
                   (0 & 2) == 0 && (1 & 2) == 0 && (2 & 2) == 2 && (3 & 2) == 2;
  predicate op_match(integer op, integer c1, integer c2) = op_c1(op) == c1 && op_c2(op) == c2;
  predicate op_valid_name(integer c1, integer c2) =
    c1 == 'r' || c1 == '~' || (c1 == 'g' && (c2 == 1 || c2 == 24)) || (c1 == 'z' && c2 == 'y') ||
    \exists integer k; 0 <= k <= 30 && op_match(k, c1, c2);

  // Register numbering (register_defs.h, :help registers): 0-9, a-z (A-Z append to a-z),
  // '-' = 36, '*' = 37, '+' = 38; anything else has no register.
  logic integer reg_index(integer c) =
    '0' <= c <= '9' ? c - '0' : 'a' <= c <= 'z' ? c - 'a' + 10 :
    'A' <= c <= 'Z' ? c - 'A' + 10 : c == '-' ? 36 : c == '*' ? 37 : c == '+' ? 38 : -1;
  logic integer reg_name(integer n) =
    n == -1 ? '"' : 0 <= n <= 9 ? '0' + n : n == 36 ? '-' : n == 37 ? '*' : n == 38 ? '+' :
    'a' + (n - 10);

  // An empty register holds no text: no lines, or one empty characterwise line.
  predicate empty{L}(yankreg_T *r) =
    r->y_array == \null || r->y_size == 0 ||
    (r->y_size == 1 && r->y_type == kMTCharWise && r->y_array[0].size == 0);
  predicate readable{L}(yankreg_T *r) =
    \valid_read(r) && (r->y_array != \null && r->y_size == 1 ==> \valid_read(r->y_array));
  predicate regs_readable{L} = \forall integer k; 0 <= k < NUM_REGISTERS ==> readable(&y_regs[k]);
  logic integer nonempty_count{L}(integer n) =
    n <= 0 ? 0 : nonempty_count(n - 1) + (empty(&y_regs[n - 1]) ? 0 : 1);
  predicate prev_ok{L} = y_previous == \null ||
    \exists integer k; 0 <= k < NUM_REGISTERS && y_previous == &y_regs[k];
*/
"""

CONTRACTS = {
    "ascii_isdigit": "/*@ assigns \\nothing; ensures \\result <==> '0' <= c <= '9'; */",
    "op_reg_index": "/*@ assigns \\nothing; ensures \\result == reg_index(regname); */",
    "get_register_name": """/*@ requires -1 <= num < NUM_REGISTERS; assigns \\nothing;
    ensures \\result == reg_name(num); */""",
    "reg_empty": """/*@ requires readable(reg); assigns \\nothing;
    ensures \\result <==> empty(reg); */""",
    "get_op_type": """/*@ requires op_valid_name(char1, char2);
    assigns \\nothing;
    ensures 0 <= \\result <= 30;
    ensures char1 == 'r' ==> \\result == OP_REPLACE;
    ensures char1 == '~' ==> \\result == OP_TILDE;
    ensures char1 == 'g' && char2 == 1 ==> \\result == OP_NR_ADD;
    ensures char1 == 'g' && char2 == 24 ==> \\result == OP_NR_SUB;
    ensures char1 == 'z' && char2 == 'y' ==> \\result == OP_YANK;
    ensures !(char1 == 'r' || char1 == '~' || (char1 == 'g' && (char2 == 1 || char2 == 24)) ||
              (char1 == 'z' && char2 == 'y')) ==>
      op_match(\\result, char1, char2) && \\forall integer k; 0 <= k < \\result ==> !op_match(k, char1, char2); */""",
    "op_on_lines": """/*@ requires 0 <= op <= 30; assigns \\nothing;
    ensures \\result == (op_lines(op) ? 1 : 0); */""",
    "op_is_change": """/*@ requires 0 <= op <= 30; assigns \\nothing;
    ensures \\result == (op_changes(op) ? 2 : 0); */""",
    "op_redoable": """/*@ requires 0 <= op <= 30; assigns \\nothing;
    ensures op == OP_YANK ==> \\result == redo_yank;
    ensures op != OP_YANK ==> (\\result == 1 <==> op_changes(op)) && (\\result == 0 || \\result == 1); */""",
    "get_op_char": """/*@ requires 0 <= optype <= 30; assigns \\nothing;
    ensures \\result == op_c1(optype); */""",
    "get_extra_op_char": """/*@ requires 0 <= optype <= 30; assigns \\nothing;
    ensures \\result == op_c2(optype); */""",
    "get_unname_register": """/*@ requires prev_ok; assigns \\nothing;
    ensures y_previous == \\null ==> \\result == -1;
    ensures y_previous != \\null ==> 0 <= \\result < NUM_REGISTERS && &y_regs[\\result] == y_previous; */""",
    "get_y_register": """/*@ requires 0 <= reg < NUM_REGISTERS; assigns \\nothing;
    ensures \\result == &y_regs[reg]; */""",
    "get_y_previous": "/*@ assigns \\nothing; ensures \\result == y_previous; */",
    "op_reg_amount": """/*@ requires regs_readable; assigns \\nothing;
    ensures \\result == nonempty_count(NUM_SAVED_REGISTERS); */""",
    "op_reg_get": """/*@ assigns \\nothing;
    ensures reg_index(name) == -1 ==> \\result == \\null;
    ensures reg_index(name) != -1 ==> \\result == &y_regs[reg_index(name)]; */""",
    "op_reg_set_previous": """/*@ assigns y_previous;
    ensures reg_index(name) == -1 ==> !\\result && y_previous == \\old(y_previous);
    ensures reg_index(name) != -1 ==> \\result && y_previous == &y_regs[reg_index(name)]; */""",
}

BITS = " ".join(f"/*@ assert opchars[op][2] == {k} ==> (opchars[op][2] & {m}) == {k & m}; */"
               for m in (1, 2) for k in range(4))
FLAGS = (BITS + " /*@ assert opchars[op][2] == (op_lines(op) ? 1 : 0) + (op_changes(op) ? 2 : 0); */ "
         "/*@ assert opchars[op][2] == 0 || opchars[op][2] == 1 || opchars[op][2] == 2 || opchars[op][2] == 3; */")
LOOPS = {
    "op_on_lines": [("  return opchars[op][2] & OPF_LINES;", FLAGS)],
    "op_is_change": [("  return opchars[op][2] & OPF_CHANGE;", FLAGS)],
    "get_op_type": [("  for (i = 0;; i++) {",
        "/*@ loop invariant 0 <= i <= 30; loop invariant \\forall integer k; 0 <= k < i ==> !op_match(k, char1, char2); loop assigns i; loop variant 30 - i; */")],
    "op_reg_amount": [("  for (size_t i = 0; i < NUM_SAVED_REGISTERS; i++) {",
        "/*@ loop invariant 0 <= i <= NUM_SAVED_REGISTERS; loop invariant ret == nonempty_count(i); loop invariant 0 <= ret <= i; loop assigns i, ret; loop variant NUM_SAVED_REGISTERS - i; */"),
        ("    if (!reg_empty(y_regs + i)) {",
        "/*@ assert nonempty_count(i + 1) == nonempty_count(i) + (empty(&y_regs[i]) ? 0 : 1); */")],
}
