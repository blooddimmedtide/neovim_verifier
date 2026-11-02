"""Run the reviewer's planted bugs (mutants.toml) against the Frama-C WP proof.

Usage: python3 -I run_mutants.py <neovim checkout> [timeout_seconds]   (writes mutants_result.tsv)
Each mutant replaces C code (not ACSL) that occurs exactly once in the wp/build.py
output; WP is then run only on the mutated function (-wp-fct), with the same
options as wp/run_wp.sh except -wp-par 2. A mutant is caught when some goal of that
function is not proved. Survivors must be marked "equivalent" by the reviewer with
a reason, or the run fails. IDS=a,b runs only those mutants (result file untouched).
"""
import os, re, shutil, subprocess, sys, tempfile, tomllib
HERE = os.path.dirname(os.path.abspath(__file__))
NV = sys.argv[1]
T = sys.argv[2] if len(sys.argv) > 2 else "60"
W = tempfile.mkdtemp()
shutil.copytree(os.path.join(HERE, "wp", "stubs"), os.path.join(W, "stubs"))
base = os.path.join(W, "base.c")
subprocess.run([sys.executable, "-I", os.path.join(HERE, "wp", "build.py"), NV, base], check=True)
src = open(base).read()


def wp(cfile, fct):
    """Returns (all proved?, summary line, log path)."""
    log = cfile[:-2] + ".log"
    with open(log, "w") as fh:
        subprocess.run(["frama-c", "-machdep", "x86_64", "-cpp-extra-args=-I stubs", os.path.basename(cfile),
                        "-wp", "-wp-fct", fct, "-wp-rte", "-wp-model", "Typed+Cast", "-wp-prover", "z3,cvc5",
                        "-wp-timeout", T, "-wp-par", "2", "-wp-cache", "none"],
                       cwd=W, stdout=fh, stderr=subprocess.STDOUT)
    text = open(log).read()
    m = re.search(r"Proved goals:\s+(\d+) / (\d+)", text)
    return bool(m) and m.group(1) == m.group(2), (m.group(0) if m else "no result (frama-c error?)"), log


ok, rows = True, ["id\tfunction\tresult\texpected\tgoals"]
mutants = tomllib.load(open(os.path.join(HERE, "mutants.toml"), "rb"))["mutant"]
ids = [i for i in os.environ.get("IDS", "").split(",") if i]
if ids:
    mutants = [m for m in mutants if m["id"] in ids]
for m in mutants:
    if src.count(m["original"]) != 1:
        print(m["id"], "original text not found exactly once"); ok = False; continue
    mutated = src.replace(m["original"], m["mutated"])
    # the mutation must touch C code only: stripping ACSL comments must show a difference
    strip = lambda s: re.sub(r"/\*@.*?\*/", "", s, flags=re.S)
    if strip(mutated) == strip(src):
        print(m["id"], "mutation only touches annotations"); ok = False; continue
    path = os.path.join(W, m["id"] + ".c")
    open(path, "w").write(mutated)
    proved, summary, log = wp(path, m["function"])
    res = "survived" if proved else "caught"
    if res != m["expect"] and not (res == "survived" and m["expect"] == "equivalent"):
        ok = False
    rows.append(f"{m['id']}\t{m['function']}\t{res}\t{m['expect']}\t{summary}")
    print(rows[-1], flush=True)
if not ids:
    open(os.path.join(HERE, "mutants_result.tsv"), "w").write("\n".join(rows) + "\n")
print("logs:", W)
sys.exit(0 if ok else 1)
