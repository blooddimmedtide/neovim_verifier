"""List every C function defined in Neovim's source, for the per-function tracker.

Usage: python3 -I tools/inventory.py <neovim checkout> > libraries/neovim/inventory.tsv

Neovim's style puts a function's opening brace alone at column 0, so a
definition is found by scanning back from each "{" line to the line holding
"name(". Output columns: file, line, function, static (yes/no).
This is a syntactic scan; the call-graph pass (tools/callgraph.py, needs a
configured build) refines it.
"""
import os, re, sys

NAME = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(")
SKIP = {"if", "for", "while", "switch", "return", "sizeof"}


def scan(path, rel):
    lines = open(path, errors="replace").read().split("\n")
    for i, line in enumerate(lines):
        if line != "{":
            continue
        j = i - 1
        while j >= 0 and (lines[j].startswith((" ", "\t")) or lines[j].startswith("FUNC_ATTR")
                          or lines[j].strip() == ""):
            j -= 1
        if j < 0:
            continue
        head = lines[j]
        if head.startswith(("#", "//", "/*", "}", "typedef", "struct", "enum", "union")) and "(" not in head:
            continue
        # The function name is the last "ident(" at paren depth 0, which skips
        # type macros such as "ArrayOf(String) nvim_list_bufs(".
        name, depth = None, 0
        for k, ch in enumerate(head):
            if ch == "(":
                if depth == 0:
                    m = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\s*$", head[:k])
                    if m and not m.group(1).startswith("FUNC_ATTR"):
                        name = m.group(1)
                depth += 1
            elif ch == ")":
                depth -= 1
        if not name or name in SKIP or "=" in head.split("(")[0]:
            continue
        yield rel, j + 1, name, "yes" if re.match(r"^(static|inline)\b", head) else "no"


def main(root):
    base = os.path.join(root, "src", "nvim")
    print("file\tline\tfunction\tstatic")
    for d, _, files in sorted(os.walk(base)):
        for f in sorted(files):
            if f.endswith(".c"):
                p = os.path.join(d, f)
                for row in scan(p, os.path.relpath(p, root)):
                    print("\t".join(map(str, row)))


if __name__ == "__main__":
    main(sys.argv[1])
