"""Planted bugs in the proved code: each must make its function's proof fail.
Usage: python3 -I mutants.py <neovim checkout>   (frama-c on PATH)"""
import os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
M = [  # (function, original text, mutant text)
    ("tv_blob_check_index", "n1 > bloblen", "n1 >= bloblen"),
    ("tv_blob_check_index", "if (!quiet) {\n      semsg(_(e_blobidx), n1);", "if (quiet) {\n      semsg(_(e_blobidx), n1);"),
    ("tv_blob_check_range", "n2 < n1", "n2 <= n1"),
    ("tv_blob_check_range", "n2 >= bloblen", "n2 > bloblen"),
    ("tv_blob_equal", "if (len1 != len2) {", "if (len1 < len2) {"),
    ("tv_blob_equal", "for (int i = 0; i < b1->bv_ga.ga_len; i++) {", "for (int i = 1; i < b1->bv_ga.ga_len; i++) {"),
    ("tv_list_uidx", "n >= tv_list_len(l)", "n > tv_list_len(l)"),
    ("tv_check_num", "  case VAR_SPECIAL:\n  case VAR_STRING:\n    return true;\n  case VAR_FUNC:", "  case VAR_STRING:\n    return true;\n  case VAR_SPECIAL:\n  case VAR_FUNC:"),
    ("tv_check_str", "  case VAR_FLOAT:\n    return true;", "  case VAR_FLOAT:\n    return false;"),
    ("tv_islocked", "(tv_list_locked(tv->vval.v_list) == VAR_LOCKED)", "(tv_list_locked(tv->vval.v_list) != VAR_UNLOCKED)"),
    ("tv_check_for_bool_arg", "args[idx].vval.v_number == 1", "args[idx].vval.v_number == 2"),
    ("tv_check_for_nonempty_string_arg", "*args[idx].vval.v_string == NUL", "args[idx].vval.v_string[1] == NUL"),
    ("tv_check_for_string_or_func_arg", "args[idx].v_type != VAR_FUNC\n", "args[idx].v_type != VAR_LIST\n"),
]
nv = sys.argv[1]; caught = 0
for f, a, b in M:
    w = tempfile.mkdtemp()
    subprocess.run(["python3", "-I", f"{HERE}/build.py", nv, f"{w}/tv.c"], check=True)
    t = open(f"{w}/tv.c").read()
    assert t.count(a) >= 1, (f, a)
    open(f"{w}/tv.c", "w").write(t.replace(a, b, 1))
    r = subprocess.run(["frama-c", "-machdep", "x86_64", "tv.c", "-wp", "-wp-fct", f, "-wp-rte",
                        "-warn-signed-downcast", "-warn-signed-overflow", "-wp-model", "Typed+Cast",
                        "-wp-prover", "z3,cvc5", "-wp-timeout", "10", "-wp-cache", "none"],
                       cwd=w, capture_output=True, text=True).stdout
    line = [l for l in r.splitlines() if "Proved goals" in l]
    ok = bool(line) and line[0].split(":")[1].split("/")[0].strip() != line[0].split("/")[1].strip()
    caught += ok
    print(("caught " if ok else "MISSED ") + f, "|", (line[0].strip() if line else "no result"))
print(f"{caught}/{len(M)} caught"); sys.exit(0 if caught == len(M) else 1)
