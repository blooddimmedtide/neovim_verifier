"""Adversarial-review planted bugs (see ../REVIEW.md). Planted bugs in the proved code: each must make its function's proof fail.
Usage: python3 -I mutants.py <neovim checkout>   (frama-c on PATH)"""
import os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
M = [  # (function, original text, mutant text) -- adversarial review mutants (REVIEW.md)
    # R1-R18: behaviour bugs, expected caught
    ("tv_list_uidx", "  if (n < 0) {\n    n += tv_list_len(l);", "  if (n <= 0) {\n    n += tv_list_len(l);"),
    ("tv_list_locked", "    return VAR_FIXED;", "    return VAR_LOCKED;"),
    ("tv_check_str_or_nr", '    emsg(_("E5300: Expected a Number or a String"));\n    return false;', "    return true;"),
    ("tv2bool", "return tv->vval.v_float != 0.0;", "return tv->vval.v_float > 0.0;"),
    ("tv2bool", "dv_hashtab.ht_used > 0;", "dv_hashtab.ht_filled > 0;"),
    ("tv2bool", "  case VAR_UNKNOWN:\n    break;\n  }\n  return false;", "  case VAR_UNKNOWN:\n    return true;\n  }\n  return false;"),
    ("tv_get_number_chk", "return (ret_error == NULL ? -1 : 0);", "return (ret_error == NULL ? 0 : -1);"),
    ("tv_get_number_chk", "  case VAR_SPECIAL:\n    return 0;", "  case VAR_SPECIAL:\n    return 1;"),
    ("tv_get_number_chk", "    varnumber_T n = 0;", "    varnumber_T n = 1;"),
    ("tv_get_float", 'semsg(_(e_intern2), "tv_get_float(UNKNOWN)");', ";"),
    ("tv_callback_equal", "  case kCallbackNone:\n    return true;", "  case kCallbackNone:\n    return false;"),
    ("tv_callback_equal", "return cb1->data.luaref == cb2->data.luaref;", "return cb1->data.luaref <= cb2->data.luaref;"),
    ("tv_check_lock", "return value_check_lock(tv->v_lock, name, name_len)\n         ||", "return value_check_lock(tv->v_lock, name, name_len)\n         |"),
    ("value_check_lock", "  case VAR_FIXED:\n    error_message = name == NULL ? N_(e_cannot_change_value)\n                                 : N_(e_cannot_change_value_of_str);\n    break;", "  case VAR_FIXED:\n    break;"),
    ("check_repeat_count", "if (n <= (varnumber_T)INT_MAX / slen) {", "if (n < (varnumber_T)INT_MAX / slen) {"),
    ("tv_islocked", "              && tv->vval.v_dict != NULL\n", ""),
    ("tv_blob_equal", "  if (b1 == b2) {\n    return true;", "  if (b1 == b2) {\n    return false;"),
    ("tv_check_for_opt_bool_arg", "  if (args[idx].v_type == VAR_UNKNOWN) {\n    return OK;\n  }\n  return tv_check_for_bool_arg", "  if (args[idx].v_type == VAR_UNKNOWN) {\n    return FAIL;\n  }\n  return tv_check_for_bool_arg"),
    ("tv_check_for_nonnull_dict_arg", "  if (args[idx].vval.v_dict == NULL) {", "  if (args[idx].vval.v_dict != NULL) {"),
    ("tv_blob_len", "    return 0;\n  }\n  return b->bv_ga.ga_len;", "    return 1;\n  }\n  return b->bv_ga.ga_len;"),
    # R21-R25: wrong message / message argument (observable to the user), expected MISSED by design
    ("tv_check_str_or_nr", "E805: Expected a Number or a String, Float found", "E745: Expected a Number or a String, List found"),
    ("value_check_lock", "error_message = name == NULL ? N_(e_value_is_locked)", "error_message = name == NULL ? N_(e_cannot_change_value)"),
    ("tv_blob_check_range", "      semsg(_(e_blobidx), n2);", "      semsg(_(e_blobidx), n1);"),
    ("tv_check_for_float_or_nr_arg", "float_or_number_required_for_argument_nr), idx + 1);", "float_or_number_required_for_argument_nr), idx);"),
    ("tv_check_for_opt_string_arg", "|| tv_check_for_string_arg(args, idx) != FAIL) ? OK : FAIL;", "|| tv_check_for_string_or_number_arg(args, idx) != FAIL) ? OK : FAIL;"),
    # R26: documented "Otherwise it is not touched" for ret_error (spec has no frame for *ret_error on success)
    ("tv_get_number_chk", "  case VAR_NUMBER:\n    return tv->vval.v_number;", "  case VAR_NUMBER:\n    if (ret_error != NULL) {\n      *ret_error = true;\n    }\n    return tv->vval.v_number;"),
]
nv = sys.argv[1]; caught = 0
for f, a, b in M:
    w = tempfile.mkdtemp()
    subprocess.run(["python3", "-I", f"{HERE}/build.py", nv, f"{w}/tv.c"], check=True)
    t = open(f"{w}/tv.c").read()
    assert t.count(a) >= 1, (f, a)
    import re
    mdef = re.search(r"\n[^\n;]*\b" + f + r"\([^;]*?\n\{", t)
    assert mdef and t.index(a) > mdef.start() and t.index(a) < t.index("\n}", mdef.end()), ("not in body", f, a)
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
