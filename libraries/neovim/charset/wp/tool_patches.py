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


def apply(name, text):
    if name == "vim_str2nr":
        text = expand_macro(text, "PARSE_NUMBER")
    for old, new in PATCHES.get(name, []):
        if text.count(old) != 1:
            raise SystemExit(f"tool_patches: {name}: patch anchor not found once")
        text = text.replace(old, new)
    return text
