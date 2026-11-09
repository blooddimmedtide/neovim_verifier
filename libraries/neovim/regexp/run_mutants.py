"""Run the reviewer's planted bugs (mutants.toml) against the regexp number-reader proofs.

Usage: python3 -I run_mutants.py <upstream checkout> <fixed checkout>   (writes mutants_result.tsv)
For each mutant: copy the three source files the builds read (regexp.c, charset.c,
ascii_defs.h) from the mutant's checkout into a temporary tree, apply the mutation
inside the named function (text must occur exactly once there), copy wp/, cbmc/ and
difftest/ next to a link to tools/, and re-pin the function's sha256 in the copied
build.py to the mutated text. The proof scripts themselves are run unchanged:
getdecchrs -> wp/run_wp.sh, gethexchrs/getoctchrs -> cbmc/run_cbmc.sh (ONLY=<harness>).
caught = the proof script exits nonzero for a reason other than the build refusing
the input. The differential test is also run, for information (column difftest).
Fails when a mutant expected "caught" survives, or a mutant does not apply/build.
IDS=a,b runs only those mutants and leaves mutants_result.tsv alone.
"""
import hashlib, os, re, shutil, subprocess, sys, tempfile, tomllib
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, "..", "..", "..", "tools"))
sys.path.insert(0, TOOLS)
from extract_c import find

TREES = {"upstream": os.path.abspath(sys.argv[1]), "fixed": os.path.abspath(sys.argv[2])}
FILES = ["src/nvim/regexp.c", "src/nvim/charset.c", "src/nvim/ascii_defs.h"]
PROOF = {"getdecchrs": ("wp", None), "gethexchrs": ("cbmc", "h_gethexchrs"), "getoctchrs": ("cbmc", "h_getoctchrs")}
WP_TIMEOUT = os.environ.get("WP_TIMEOUT", "60")


def piece_sha(lines, name):
    s, e = find(lines, name)
    return hashlib.sha256("\n".join(lines[s:e + 1]).encode()).hexdigest(), s, e


def run_one(m, W):
    tree = TREES[m.get("checkout", "fixed")]
    nv = os.path.join(W, "nv")
    for f in FILES:
        os.makedirs(os.path.dirname(os.path.join(nv, f)), exist_ok=True)
        shutil.copy(os.path.join(tree, f), os.path.join(nv, f))
    rc = os.path.join(nv, FILES[0])
    lines = open(rc).read().split("\n")
    old_sha, s, e = piece_sha(lines, m["function"])
    piece = "\n".join(lines[s:e + 1])
    if piece.count(m["original"]) != 1:
        return "not-applied", ""
    lines[s:e + 1] = piece.replace(m["original"], m["mutated"]).split("\n")
    open(rc, "w").write("\n".join(lines))
    new_sha = piece_sha(lines, m["function"])[0]
    # Copy of the proof scripts with the function re-pinned to the mutated text.
    lib = os.path.join(W, "repo", "libraries", "neovim", "regexp")
    for d in ("wp", "cbmc", "difftest"):
        shutil.copytree(os.path.join(HERE, d), os.path.join(lib, d), ignore=shutil.ignore_patterns("__pycache__"))
    os.symlink(TOOLS, os.path.join(W, "repo", "tools"))
    kind, harness = PROOF[m["function"]]
    bp = os.path.join(lib, kind, "build.py")
    text = open(bp).read()
    if text.count(old_sha) != 1:
        return "pin-not-found", ""
    open(bp, "w").write(text.replace(old_sha, new_sha))
    env = dict(os.environ)
    if kind == "wp":
        cmd = ["bash", os.path.join(lib, "wp", "run_wp.sh"), nv, WP_TIMEOUT]
    else:
        cmd = ["bash", os.path.join(lib, "cbmc", "run_cbmc.sh"), nv]
        env["ONLY"] = harness
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    out = r.stdout + r.stderr
    if re.search(r"^(build|extract): ", out, re.M) or "Traceback" in out:
        return "build-error", out
    if kind == "cbmc" and re.search(r"(PARSING|CONVERSION) ERROR|error:", out) and "FAILURE" not in out:
        return "build-error", out
    res = "caught" if r.returncode else "survived"
    # Differential test, for information only (its exit status is not trusted: see REVIEW.md).
    d = subprocess.run(["bash", os.path.join(lib, "difftest", "run_difftest.sh"), nv], capture_output=True, text=True)
    mism = re.findall(r"(\d+) mismatches", d.stdout)
    dt = f"exit={d.returncode},mismatches={'/'.join(mism) or '?'}"
    return res, dt


def main():
    mutants = tomllib.load(open(os.path.join(HERE, "mutants.toml"), "rb"))["mutant"]
    ids = [i for i in os.environ.get("IDS", "").split(",") if i]
    if ids:
        mutants = [m for m in mutants if m["id"] in ids]
    ok, rows = True, ["id\tfunction\tcheckout\tresult\texpected\tdifftest"]
    for m in mutants:
        W = tempfile.mkdtemp(prefix="regexp_mut_")
        res, dt = run_one(m, W)
        if res not in ("caught", "survived"):
            print(m["id"], res, dt[-2000:]); ok = False
        elif res == "survived" and m["expect"] == "caught":
            ok = False
        shutil.rmtree(W, ignore_errors=True)
        rows.append(f"{m['id']}\t{m['function']}\t{m.get('checkout', 'fixed')}\t{res}\t{m['expect']}\t{dt}")
        print(rows[-1], flush=True)
    if not ids:
        open(os.path.join(HERE, "mutants_result.tsv"), "w").write("\n".join(rows) + "\n")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
