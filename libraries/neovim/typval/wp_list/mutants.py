"""Planted bugs (code and spec) for the list proofs; each must make WP fail.
Usage: python3 -I mutants.py <neovim checkout> [timeout]   (frama-c on PATH)"""
import os, re, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
NV, T = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "20"
MUTANTS = [  # (function, exact text in the built file, replacement)
    ("tv_list_find", "      idx = l->lv_len - 1;\n    }\n  } else {", "      idx = l->lv_len - 2;\n    }\n  } else {"),
    ("tv_list_find", "    item = item->li_next;\n    idx++;", "    item = item->li_next;\n    idx += 2;"),
    ("tv_list_find", "  l->lv_idx = idx;", "  l->lv_idx = idx + 1;"),
    ("tv_list_find", "    item = item->li_prev;\n    idx--;", "    item = item->li_next;\n    idx--;"),
    ("tv_list_reverse", "  l->lv_idx = l->lv_len - l->lv_idx - 1;", "  l->lv_idx = l->lv_len - l->lv_idx;"),
    ("tv_list_reverse", "  SWAP(l->lv_first, l->lv_last);", "  l->lv_first = l->lv_last;"),
    ("tv_list_reverse", "  if (tv_list_len(l) <= 1) {", "  if (tv_list_len(l) <= 2) {"),
    ("tv_list_idx_of_item", "      return idx;", "      return idx + 1;"),
    ("tv_list_idx_of_item", "  return -1;\n}", "  return 0;\n}"),
    ("tv_list_find_index", "    *idx = 0;", "    *idx = 1;"),
    ("tv_list_check_range_index_one", "  if (!quiet) {\n    semsg(_(e_list_index_out_of_range_nr), (int64_t)(*n1));",
     "  if (quiet) {\n    semsg(_(e_list_index_out_of_range_nr), (int64_t)(*n1));"),
    ("tv_list_check_range_index_two", "  if (*n2 < *n1) {", "  if (*n2 <= *n1) {"),
    ("tv_list_check_range_index_two", "    *n1 = tv_list_idx_of_item(l, li1);", "    *n1 = tv_list_idx_of_item(l, li1) - 1;"),
    ("tv_list_uidx", "  if (n < 0 || n >= tv_list_len(l)) {", "  if (n < 0 || n > tv_list_len(l)) {"),
]
W = tempfile.mkdtemp()
subprocess.run(["python3", "-I", f"{HERE}/build.py", NV, f"{W}/base.c"], check=True)
base = open(f"{W}/base.c").read()
bad = 0
for i, (fn, old, new) in enumerate(MUTANTS):
    if base.count(old) != 1:
        print(f"m{i} {fn}: anchor not unique/absent"); bad += 1; continue
    open(f"{W}/m.c", "w").write(base.replace(old, new))
    r = subprocess.run(["frama-c", "-machdep", "x86_64", "m.c", "-wp", "-wp-fct", fn, "-wp-rte",
                        "-warn-signed-downcast", "-warn-signed-overflow", "-wp-model", "Typed+Cast",
                        "-wp-prover", "z3,cvc5", "-wp-timeout", T, "-wp-par", str(os.cpu_count()),
                        "-wp-cache", "none"], cwd=W, capture_output=True, text=True)
    m = re.search(r"Proved goals: +(\d+) / (\d+)", r.stdout)
    killed = not m or m.group(1) != m.group(2)
    print(f"m{i} {fn}: {'caught' if killed else 'SURVIVED'} ({m.group(0) if m else 'no result'})")
    bad += not killed
print(f"survivors: {bad}"); sys.exit(1 if bad else 0)
