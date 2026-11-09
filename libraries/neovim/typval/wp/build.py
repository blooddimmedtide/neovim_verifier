"""Annotated standalone copy of typval.c / typval.h functions for Frama-C WP.

Usage: python3 -I build.py <neovim checkout> <out.c>
       python3 -I build.py --pin <neovim checkout>     (print sha256 of each piece)
Each function is the exact upstream text (sha256 pinned, via tools/extract_c.py).
Contracts sit on prototypes in the prelude (Frama-C joins them to the definition);
loop annotations are inserted as /*@ */ comments, and the build checks that
removing every /*@ ... */ gives back the pinned text exactly.
"""
import hashlib, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "tools"))
from extract_c import find
from contracts import PRELUDE, CHECKS, LOOPS

TV = "src/nvim/eval/typval.c"
TH = "src/nvim/eval/typval.h"
PIECES = [  # upstream 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
    (TH, "tv_list_len", "PIN"),
    (TH, "tv_list_uidx", "PIN"),
    (TH, "tv_blob_len", "PIN"),
    (TH, "tv_blob_get", "PIN"),
    (TH, "tv_list_locked", "PIN"),
    (TV, "tv_check_str_or_nr", "PIN"),
    (TV, "tv_check_num", "PIN"),
    (TV, "tv_check_str", "PIN"),
    (TV, "tv_islocked", "PIN"),
    (TV, "check_repeat_count", "PIN"),
    (TV, "tv_get_float", "PIN"),
    (TV, "tv2bool", "PIN"),
    (TV, "tv_get_number_chk", "PIN"),
    (TV, "tv_get_number", "PIN"),
    (TV, "tv_get_bool_chk", "PIN"),
    (TV, "tv_get_bool", "PIN"),
    (TV, "tv_callback_equal", "PIN"),
    (TV, "value_check_lock", "PIN"),
    (TV, "tv_check_lock", "PIN"),
    (TH, "tv_is_func", "PIN"),
    (TV, "tv_dict_wrong_func_name", "PIN"),
    (TV, "tv_get_string_buf_chk", "PIN"),
    (TV, "tv_get_string_buf", "PIN"),
    (TV, "tv_blob_check_index", "PIN"),
    (TV, "tv_blob_check_range", "PIN"),
    (TV, "tv_blob_equal", "PIN"),
    (TV, "tv_check_for_string_arg", "PIN"),
    (TV, "tv_check_for_nonempty_string_arg", "PIN"),
    (TV, "tv_check_for_opt_string_arg", "PIN"),
    (TV, "tv_check_for_number_arg", "PIN"),
    (TV, "tv_check_for_opt_number_arg", "PIN"),
    (TV, "tv_check_for_float_or_nr_arg", "PIN"),
    (TV, "tv_check_for_bool_arg", "PIN"),
    (TV, "tv_check_for_opt_bool_arg", "PIN"),
    (TV, "tv_check_for_blob_arg", "PIN"),
    (TV, "tv_check_for_list_arg", "PIN"),
    (TV, "tv_check_for_dict_arg", "PIN"),
    (TV, "tv_check_for_nonnull_dict_arg", "PIN"),
    (TV, "tv_check_for_opt_dict_arg", "PIN"),
    (TV, "tv_check_for_string_or_number_arg", "PIN"),
    (TV, "tv_check_for_buffer_arg", "PIN"),
    (TV, "tv_check_for_lnum_arg", "PIN"),
    (TV, "tv_check_for_string_or_list_arg", "PIN"),
    (TV, "tv_check_for_string_or_list_or_blob_arg", "PIN"),
    (TV, "tv_check_for_opt_string_or_list_arg", "PIN"),
    (TV, "tv_check_for_string_or_func_arg", "PIN"),
    (TV, "tv_check_for_list_or_blob_arg", "PIN"),
]
SHA = {}
exec(open(os.path.join(HERE, "pins.txt")).read())


def strip(t):
    return re.sub(r"[ \t]*/\*@.*?\*/\n?", "", t, flags=re.S)


def main():
    if sys.argv[1] == "--pin":
        tree = sys.argv[2]
        for path, name, _ in PIECES:
            lines = open(f"{tree}/{path}").read().split("\n")
            s, e = find(lines, name)
            print(f'SHA["{name}"] = "{hashlib.sha256(chr(10).join(lines[s:e + 1]).encode()).hexdigest()}"')
        return
    tree, out = sys.argv[1], sys.argv[2]
    for path, text in CHECKS:
        if text not in open(f"{tree}/{path}").read().split("\n"):
            sys.exit(f"build: {path} no longer contains: {text}")
    parts = [PRELUDE]
    for path, name, _ in PIECES:
        lines = open(f"{tree}/{path}").read().split("\n")
        s, e = find(lines, name)
        piece = "\n".join(lines[s:e + 1])
        h = hashlib.sha256(piece.encode()).hexdigest()
        if SHA.get(name) != h:
            sys.exit(f"build: {name} ({path}:{s + 1}) differs from the pinned text: {h}")
        ann = piece
        for anchor, text in LOOPS.get(name, []):
            if ann.count(anchor) != 1:
                sys.exit(f"build: anchor for {name} not unique: {anchor!r}")
            ann = ann.replace(anchor, text + anchor)
        if strip(ann) != piece:
            sys.exit(f"build: {name}: annotations changed the code")
        parts.append(f"// {path}:{s + 1} (verbatim, sha256 {h})\n{ann}\n")
    open(out, "w").write("\n".join(parts))


main()
