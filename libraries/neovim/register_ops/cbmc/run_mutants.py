"""Planted bugs for the CBMC-proved register.c helpers (chosen by the proving session).
Each edits the extracted code and the harness must fail. op_reg_iter runs take ~10 min each.
Usage: python3 -I run_mutants.py <upstream checkout> [quick]   (quick: skip op_reg_iter ones)"""
import os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
COMMON = ["--bounds-check", "--pointer-check", "--signed-overflow-check", "--unsigned-overflow-check",
          "--pointer-overflow-check", "--undefined-shift-check", "--unwind", "40", "--unwinding-assertions"]
MUTANTS = [  # (harness file, harness function, old, new)
    ("harness.c", "harness_get_unname_register", "  return y_previous == NULL ? -1 : (int)(y_previous - &y_regs[0]);",
     "  return y_previous == NULL ? 0 : (int)(y_previous - &y_regs[0]);"),
    ("harness.c", "harness_get_unname_register", "  return y_previous == NULL ? -1 : (int)(y_previous - &y_regs[0]);",
     "  return y_previous == NULL ? -1 : (int)(y_previous - &y_regs[1]);"),
    ("harness_vyr.c", "harness_valid_yank_reg", '      || (!writing && vim_strchr("/#.%:=", regname) != NULL)',
     '      || (!writing && vim_strchr("/#.%:", regname) != NULL)'),
    ("harness_vyr.c", "harness_valid_yank_reg", '      || (!writing && vim_strchr("/#.%:=", regname) != NULL)',
     '      || (vim_strchr("/#.%:=", regname) != NULL)'),
    ("harness_vyr.c", "harness_valid_yank_reg", "  if ((regname > 0 && ASCII_ISALNUM(regname))",
     "  if ((regname > 0 && ASCII_ISALPHA(regname))"),
    ("harness_vyr.c", "harness_valid_yank_reg", "      || regname == '_'", "      || regname == '~'"),
    ("harness_vyr.c", "harness_valid_yank_reg", "  if (c <= 0) {", "  if (c < 0) {"),
    ("harness.c", "harness_op_reg_iter", "  *is_unnamed = (iter_reg == y_previous);", "  *is_unnamed = false;"),
    ("harness.c", "harness_op_reg_iter", "  while (++iter_reg - &(regs[0]) < NUM_SAVED_REGISTERS) {",
     "  while (++iter_reg - &(regs[0]) < NUM_SAVED_REGISTERS - 1) {"),
]


def main():
    nv = sys.argv[1]; quick = "quick" in sys.argv; w = tempfile.mkdtemp()
    subprocess.run([sys.executable, "-I", f"{HERE}/../wp/build.py", nv, f"{w}/base.c"], check=True)
    base = open(f"{w}/base.c").read(); caught = n = 0
    for hf, fn, old, new in MUTANTS:
        if quick and fn == "harness_op_reg_iter":
            continue
        if base.count(old) != 1:
            sys.exit(f"anchor not found once: {old}")
        open(f"{w}/ro.c", "w").write(base.replace(old, new))
        subprocess.run(["cp", f"{HERE}/{hf}", w], check=True)
        out = subprocess.run(["cbmc", hf, "--function", fn] + COMMON, cwd=w, capture_output=True, text=True).stdout
        bad = "VERIFICATION FAILED" in out; n += 1; caught += bad
        print(f"{'caught' if bad else 'MISSED'}  {fn}: {new.strip()}", flush=True)
    print(f"{caught}/{n} caught"); sys.exit(0 if caught == n else 1)


main()
