"""Copy exact upstream text of C functions into a standalone proof file.

Usage (from a target's build.py):
    from extract_c import build
    build(tree, out, prelude, prelude_checks, pieces, fixed={})
pieces: list of (file, name, sha256) in output order; name is a function
defined at column 0 whose body ends at a "}" in column 0. prelude_checks:
(file, exact line) pairs that must exist upstream, so the prelude's copies of
macros stay true. fixed: name -> (sha256, macro) for the fixed fork's version.
Any piece whose text differs from the reviewed sha256 stops the build.
"""
import hashlib, re, sys


def find(lines, name):
    pat = re.compile(r"^[A-Za-z_][\w \*]*\b" + re.escape(name) + r"\(")
    starts = [i for i, l in enumerate(lines) if pat.match(l)]
    if len(starts) != 1:
        sys.exit(f"extract: {name}: expected one definition, found {len(starts)}")
    e = starts[0]
    while not lines[e].startswith("}"):
        e += 1
    return starts[0], e


def build(tree, out, prelude, prelude_checks, pieces, fixed=None):
    fixed = fixed or {}
    for path, text in prelude_checks:
        if text not in open(f"{tree}/{path}").read().split("\n"):
            sys.exit(f"extract: {path} no longer contains: {text}")
    parts, cache = [prelude], {}
    for path, name, want in pieces:
        lines = cache.setdefault(path, open(f"{tree}/{path}").read().split("\n"))
        s, e = find(lines, name)
        piece = "\n".join(lines[s:e + 1])
        h = hashlib.sha256(piece.encode()).hexdigest()
        if name in fixed and h == fixed[name][0]:
            parts.append(f"#define {fixed[name][1]} 1  // fixed fork version")
        elif h != want:
            sys.exit(f"extract: {name} ({path}:{s + 1}) changed upstream: sha256 {h}")
        parts.append(f"// {path}:{s + 1} (verbatim)\n{piece}\n")
    open(out, "w").write("\n".join(parts))


def hashes(tree, pieces):
    """Print sha256 of each (file, name) piece, for review."""
    for path, name in pieces:
        lines = open(f"{tree}/{path}").read().split("\n")
        s, e = find(lines, name)
        print(name, f"{path}:{s + 1}", hashlib.sha256("\n".join(lines[s:e + 1]).encode()).hexdigest())


if __name__ == "__main__":
    hashes(sys.argv[1], [(sys.argv[2], n) for n in sys.argv[3:]])
