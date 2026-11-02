"""Declared tool patches: rewrites of upstream text that Frama-C WP cannot read.

backslash_halve jumps into its loop body (`goto start;` to a label inside the
`if` branch of the loop), a non-natural loop that WP refuses. The patch replaces
the goto by a copy of the two statements at the label; control then falls into the
loop condition, exactly where the original continues after those statements (they
end the if-branch, which ends the loop body). The label stays (now unused).
equiv/equiv_backslash_halve.c checks the two versions give identical results.
"""
PATCHES = {
    "backslash_halve": [(
        "    char *dst = p;\n    goto start;\n",
        "    char *dst = p;\n    *dst++ = *(p + 1);\n    p += 2;\n",
    )],
}


def apply(name, text):
    for old, new in PATCHES.get(name, []):
        if text.count(old) != 1:
            raise SystemExit(f"tool_patches: {name}: patch anchor not found once")
        text = text.replace(old, new)
    return text
