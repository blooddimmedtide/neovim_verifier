"""Run the reviewer's planted bugs (mutants.toml) against the CBMC proof of sha256.c.

Usage: python3 -I run_mutants.py <neovim checkout>   (writes mutants_result.tsv)
For each mutant, a scratch copy of the four files the proofs read (src/nvim/sha256.c,
sha256.h, ascii_defs.h, memory.h) is made, `original` (and `original2` if given) is replaced
by `mutated` (`mutated2`), and the scripts named in `checks` are run one after another
(never two CBMC processes at once). A mutant is "caught" when some proof check fails;
difftest is reported separately (it is not a proof). The run fails when a result differs
from `expect`. IDS=a,b runs only those mutants (result file untouched).
"""
import os, shutil, subprocess, sys, tempfile, tomllib
HERE = os.path.dirname(os.path.abspath(__file__))
CB = os.path.join(HERE, "cbmc")
NV = os.path.abspath(sys.argv[1])
W = tempfile.mkdtemp(prefix="sha256_mut_")
src = open(os.path.join(NV, "src/nvim/sha256.c")).read()


def run(cmd, env=None):
    p = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, **(env or {})})
    return p.returncode == 0, (p.stdout + p.stderr).strip().replace("\n", " | ")[:300]


def check(name, tree, m):
    if name == "structure":
        return run([sys.executable, "-I", os.path.join(CB, "check_structure.py"), tree])
    if name == "cbmc":
        return run(["bash", os.path.join(CB, "run_cbmc.sh"), tree])
    if name in ("finish", "bytes"):
        return run(["bash", os.path.join(CB, f"run_{name}.sh"), tree])
    if name == "stream":
        return run(["bash", os.path.join(CB, "run_stream.sh"), tree], {"EXTRA": m.get("extra", "")})
    if name == "difftest":
        return run([sys.executable, "-I", os.path.join(HERE, "difftest", "difftest.py"), tree, "2000"])
    raise SystemExit(f"unknown check {name}")


mutants = tomllib.load(open(os.path.join(HERE, "mutants.toml"), "rb"))["mutant"]
ids = [i for i in os.environ.get("IDS", "").split(",") if i]
if ids:
    mutants = [m for m in mutants if m["id"] in ids]
ok, rows = True, ["id\tfunction\tresult\texpected\tdifftest\tdetails"]
for m in mutants:
    out = src
    for o, n in ((m["original"], m["mutated"]), (m.get("original2"), m.get("mutated2"))):
        if o is None:
            continue
        if out.count(o) != 1:
            print(m["id"], "original text not found exactly once"); ok = False; break
        out = out.replace(o, n)
    else:
        tree = os.path.join(W, m["id"])
        os.makedirs(os.path.join(tree, "src/nvim"))
        for f in ("sha256.h", "ascii_defs.h", "memory.h"):
            shutil.copy(os.path.join(NV, "src/nvim", f), os.path.join(tree, "src/nvim", f))
        open(os.path.join(tree, "src/nvim/sha256.c"), "w").write(out)
        proof_fail, dt, details = [], "-", []
        for c in m["checks"]:
            passed, msg = check(c, tree, m)
            if c == "difftest":
                dt = "passed" if passed else "caught"
            elif not passed:
                proof_fail.append(c)
            details.append(f"{c}: {'pass' if passed else 'FAIL'} ({msg})")
        res = "caught" if proof_fail else "survives"
        if m["checks"] == ["difftest"]:   # no proof covers it (sha256_self_test): report the native run
            res = dt if dt == "caught" else "survives"
        ok &= res == m["expect"]
        rows.append(f"{m['id']}\t{m['function']}\t{res}\t{m['expect']}\t{dt}\t{' ; '.join(details)}")
        print(rows[-1], flush=True)
if not ids:
    open(os.path.join(HERE, "mutants_result.tsv"), "w").write("\n".join(rows) + "\n")
print("work:", W)
sys.exit(0 if ok else 1)
