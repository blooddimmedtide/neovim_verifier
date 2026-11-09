"""Planted bugs for the WP-proved register.c / ops.c helpers: each one edits the extracted
code (never the ACSL) and the proof of that function must fail.
Usage: python3 -I run_mutants.py <upstream checkout>
These mutants were picked by the proving session, not yet by an independent reviewer."""
import os, re, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
MUTANTS = [  # (function, exact old text, new text)
    ("get_op_type", "    return OP_REPLACE;", "    return OP_TILDE;"),
    ("get_op_type", "  if (char1 == 'g' && char2 == Ctrl_X) {", "  if (char1 == 'g' && char2 == Ctrl_A) {"),
    ("get_op_type", "  if (char1 == 'z' && char2 == 'y') {  // OP_YANK", "  if (char1 == 'z') {  // OP_YANK"),
    ("get_op_type", "    if (opchars[i][0] == char1 && opchars[i][1] == char2) {", "    if (opchars[i][0] == char1) {"),
    ("op_on_lines", "  return opchars[op][2] & OPF_LINES;", "  return opchars[op][2] & OPF_CHANGE;"),
    ("op_is_change", "  return opchars[op][2] & OPF_CHANGE;", "  return opchars[op][2] | OPF_CHANGE;"),
    ("op_redoable", "  return op == OP_YANK ? redo_yank : op_is_change(op);", "  return op == OP_YANK ? !redo_yank : op_is_change(op);"),
    ("get_op_char", "  return opchars[optype][0];", "  return opchars[optype][1];"),
    ("get_extra_op_char", "  return opchars[optype][1];", "  return opchars[optype + 1][1];"),
    ("get_vts", "  if (index < 1) {", "  if (index < 0) {"),
    ("get_vts", "    ts = vts_array[vts_array[0]];", "    ts = vts_array[1];"),
    ("get_vts_sum", "  for (i = 1; i <= index && i <= vts_array[0]; i++) {", "  for (i = 1; i < index && i <= vts_array[0]; i++) {"),
    ("get_vts_sum", "    sum += vts_array[vts_array[0]] * (index - vts_array[0]);", "    sum += vts_array[vts_array[0]] * (index - vts_array[0] - 1);"),
    ("get_y_register", "  return &y_regs[reg];", "  return &y_regs[reg ? reg - 1 : 0];"),
    ("op_reg_amount", "    if (!reg_empty(y_regs + i)) {", "    if (!reg_empty(y_regs + i) && i > 0) {"),
    ("op_reg_amount", "  for (size_t i = 0; i < NUM_SAVED_REGISTERS; i++) {", "  for (size_t i = 0; i < NUM_REGISTERS; i++) {"),
    ("op_reg_get", "    return NULL;\n  }\n  return &y_regs[i];", "    return &y_regs[0];\n  }\n  return &y_regs[i];"),
    ("op_reg_set_previous", "    return false;\n  }\n\n  y_previous = &y_regs[i];\n  return true;",
     "    return true;\n  }\n\n  y_previous = &y_regs[i];\n  return true;"),
    ("op_reg_index", "    return CHAR_ORD_UP(regname) + 10;", "    return CHAR_ORD_UP(regname) + 11;"),
    ("op_reg_index", "  } else if (regname == '*') {", "  } else if (regname == '+') {"),
    ("get_register_name", "    return '-';", "    return '_';"),
    ("reg_empty", "          || reg->y_size == 0", "          || reg->y_size == 2"),
]


def main():
    nv = sys.argv[1]; w = tempfile.mkdtemp()
    subprocess.run([sys.executable, "-I", f"{HERE}/wp/build.py", nv, f"{w}/base.c"], check=True)
    base = open(f"{w}/base.c").read(); caught = 0
    only = int(sys.argv[2]) if len(sys.argv) > 2 else 0   # start at mutant N (for reruns)
    for fn, old, new in MUTANTS[only:]:
        if base.count(old) != 1:
            sys.exit(f"mutant anchor not found once: {old}")
        open(f"{w}/ro.c", "w").write(base.replace(old, new))
        r = subprocess.run(["frama-c", "-machdep", "x86_64", "ro.c", "-wp", "-wp-fct", fn, "-wp-prop=-@lemma",
                            "-wp-rte", "-warn-signed-downcast", "-wp-init-const", "-wp-model", "Typed+Cast",
                            "-wp-prover", "z3,cvc5", "-wp-timeout", "10", "-wp-par", "4", "-wp-cache", "none"],
                           cwd=w, capture_output=True, text=True).stdout
        m = re.search(r"Proved goals: +(\d+) / (\d+)", r)
        ok = bool(m) and m.group(1) == m.group(2)
        caught += not ok
        print(f"{'caught' if not ok else 'MISSED'}  {fn}: {new.strip().splitlines()[0]}  ({m.group(0) if m else 'no result'})")
    n = len(MUTANTS) - only
    print(f"{caught}/{n} caught"); sys.exit(0 if caught == n else 1)


main()
