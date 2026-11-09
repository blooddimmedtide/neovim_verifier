"""Declared tool patches: rewrites of upstream text that Frama-C WP cannot read.

backslash_halve jumps into its loop body (`goto start;` to a label inside the
`if` branch of the loop), a non-natural loop that WP refuses. The patch replaces
the goto by a copy of the two statements at the label; control then falls into the
loop condition, exactly where the original continues after those statements (they
end the if-branch, which ends the loop body). The label stays (now unused).
equiv/equiv_backslash_halve.c checks the two versions give identical results.

vim_str2nr defines a statement macro PARSE_NUMBER holding a loop and uses it four
times; ACSL loop annotations cannot go inside a #define (the preprocessor removes
comments), so the uses are expanded in place (expand_macro). This is the
preprocessor's own substitution; equiv/ checks the token streams are identical.

vim_str2nr also gets flatten_str2nr: short-circuit `||` / `&&` between operands that are
side-effect free and always defined become `|` / `&` (STRING_ENDED, the prefix-letter tests,
the first conjuncts of the prefix checks). Reads of the string stay behind `&&`, so no read
happens that the original does not do. Why: CIL turns each `||` / `&&` into a nested `if`
whose branches jump, and WP copies the rest of the function for every such path (one
postcondition goal was 17.8 million lines; after the rewrite 39 thousand).
equiv/ checks with CBMC that the rewritten and original function agree.

vim_str2nr also gets outline_str2nr: each of the four expanded PARSE_NUMBER blocks moves,
unchanged, into its own static function vp_parse_<base>, which copies ptr and un in, runs the
block (with the same STRING_ENDED macro) and copies them back out; the block's place gets
the call. The block uses only start, ptr, un, what, maxlen and overflow. Why: WP treats a
call through its contract, so each digit loop is proved once instead of once for every path
through the prefix checks before it. Same CBMC check as above.
"""
import re
PATCHES = {
    "backslash_halve": [(
        "    char *dst = p;\n    goto start;\n",
        "    char *dst = p;\n    *dst++ = *(p + 1);\n    p += 2;\n",
    )],
}


def expand_macro(text, macro):
    """Replace each use `MACRO(a, b, c);` of a statement macro defined in the function by
    its body with the arguments substituted, as the C preprocessor does, and drop the
    #define. ACSL loop annotations can then be placed on each expanded loop (comments
    inside a #define are removed by the preprocessor). equiv/run_equiv.sh checks that
    gcc -E gives the same token stream for the original and the expanded text."""
    lines = text.split("\n")
    i = next(k for k, l in enumerate(lines) if l.startswith(f"#define {macro}("))
    j = i
    while lines[j].endswith("\\"):
        j += 1
    head = lines[i][len(f"#define {macro}("):]
    params = [p.strip() for p in head[:head.index(")")].split(",")]
    body = [l[:-1].rstrip() if l.endswith("\\") else l for l in lines[i + 1:j + 1]]
    del lines[i:j + 1]
    out = []
    for l in lines:
        st = l.strip()
        if st.startswith(macro + "(") and st.endswith(");"):
            args, depth, cur = [], 0, ""
            for ch in st[len(macro) + 1:-2]:
                if ch == "," and depth == 0:
                    args.append(cur.strip()); cur = ""; continue
                depth += ch == "("; depth -= ch == ")"; cur += ch
            args.append(cur.strip())
            assert len(args) == len(params), l
            for b in body:
                for p, a in zip(params, args):
                    b = re.sub(r"\b" + p + r"\b", lambda _m: a, b)
                out.append(b)
            out[-1] = out[-1] + ";"   # the use's own semicolon after `while (0)`
        else:
            out.append(l)
    return "\n".join(out)


FLATTEN = [
    # STRING_ENDED, upstream and fixed forms (exactly one is present)
    ("(!(maxlen == 0 || (int)((ptr) - start) < maxlen))",
     "(!((maxlen == 0) | ((int)((ptr) - start) < maxlen)))", (0, 1)),
    ("(!(maxlen == 0 ? (ptr) - start < INT_MAX : (ptr) - start < maxlen))",
     "(!(((maxlen == 0) & ((ptr) - start < INT_MAX)) | ((maxlen != 0) & ((ptr) - start < maxlen))))", (0, 1)),
    ("(ptr[1] == 'x' || ptr[1] == 'X')", "((ptr[1] == 'x') | (ptr[1] == 'X'))", (1,)),
    ("(ptr[1] == 'b' || ptr[1] == 'B')", "((ptr[1] == 'b') | (ptr[1] == 'B'))", (1,)),
    ("(ptr[1] == 'o' || ptr[1] == 'O')", "((ptr[1] == 'o') | (ptr[1] == 'O'))", (1,)),
    ("((*ptr == '0' || *ptr == '1'))", "(((*ptr == '0') | (*ptr == '1')))", (2,)),
    ("""  } else if ((what & (STR2NR_HEX | STR2NR_OCT | STR2NR_OOCT | STR2NR_BIN))
             && !STRING_ENDED(ptr + 1) && ptr[0] == '0' && ptr[1] != '8'
             && ptr[1] != '9') {""",
     """  } else if ((((what & (STR2NR_HEX | STR2NR_OCT | STR2NR_OOCT | STR2NR_BIN)) != 0)
              & !STRING_ENDED(ptr + 1)) && ptr[0] == '0' && ((ptr[1] != '8')
             & (ptr[1] != '9'))) {""", (1,)),
] + [(f"""    if ((what & STR2NR_{f})
        && !STRING_ENDED(ptr + 2)
        && (pre == '{u}' || pre == '{l}')
        && ascii""", f"""    if ((((what & STR2NR_{f}) != 0)
         & !STRING_ENDED(ptr + 2)
         & ((pre == '{u}') | (pre == '{l}')))
        && ascii""", (1,)) for f, u, l in (("HEX", "X", "x"), ("BIN", "B", "b"), ("OOCT", "O", "o"))]


# The values of `what` the vim_str2nr proof covers, one WP run each (see run_wp.sh): every
# combination of the STR2NR_* bits (1, 2, 4, 8, 16, 128); forced ones only with a kind the
# code accepts (other kinds call abort(), excluded by the contract).
STR2NR_WHAT = [w for w in range(256) if w & 96 == 0
               and (w & 128 == 0 or (w & ~144) in (0, 1, 2, 4, 8, 10))]


def flatten_str2nr(text):
    for old, new, counts in FLATTEN:
        if text.count(old) not in counts:
            raise SystemExit(f"tool_patches: vim_str2nr: flatten anchor count {text.count(old)}: {old[:50]}")
        text = text.replace(old, new)
    return text


PARSE_LABELS = ["bin", "oct", "dec", "hex"]   # source order of the four expanded blocks
HELPER_SIG = ("static void vp_parse_{lab}(const char *const start, const char **const pptr, "
              "uvarnumber_T *const pun,\n                          const int what, const int maxlen, "
              "bool *const overflow)")
HELPER_CALL = "vp_parse_{lab}(start, &ptr, &un, what, maxlen, overflow)"


def outline_str2nr(text):
    lines = text.split("\n")
    k = lines.index("#define STRING_ENDED(ptr) \\")
    macro = lines[k] + "\n" + lines[k + 1]
    helpers = []
    for lab in PARSE_LABELS:
        head = f"vim_str2nr_{lab}:\n  do {{\n"
        if text.count(head) != 1:
            raise SystemExit(f"tool_patches: vim_str2nr: block {lab} not found once")
        s = text.index(head) + len(f"vim_str2nr_{lab}:\n")
        e = text.index("  } while (0);\n", s) + len("  } while (0);")
        block = text[s:e]
        helpers.append(HELPER_SIG.format(lab=lab) + "\n{\n  const char *ptr = *pptr;\n  uvarnumber_T un = *pun;\n"
                       + macro + "\n" + block + "\n#undef STRING_ENDED\n  *pptr = ptr;\n  *pun = un;\n}\n")
        text = text[:s] + "  " + HELPER_CALL.format(lab=lab) + ";" + text[e:]
    return "\n".join(helpers) + "\n" + text


def apply(name, text):
    if name == "vim_str2nr":
        text = outline_str2nr(flatten_str2nr(expand_macro(text, "PARSE_NUMBER")))
    for old, new in PATCHES.get(name, []):
        if text.count(old) != 1:
            raise SystemExit(f"tool_patches: {name}: patch anchor not found once")
        text = text.replace(old, new)
    return text
