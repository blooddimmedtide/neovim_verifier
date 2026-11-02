"""Run the reviewer's planted bugs (mutants.toml) against the CBMC proof.

Usage: python3 -I run_mutants.py <neovim checkout>   (writes mutants_result.tsv)
Each mutant replaces text that occurs exactly once in the build.py output; it is
caught when run_cbmc.sh fails. Survivors must be marked "equivalent" by the
reviewer with a reason, or the run fails.
"""
import os, subprocess, sys, tempfile, tomllib
HERE = os.path.dirname(os.path.abspath(__file__))
NV = sys.argv[1]
W = tempfile.mkdtemp()
base = os.path.join(W, "base.c")
subprocess.run([sys.executable, "-I", os.path.join(HERE, "build.py"), NV, base], check=True)
src = open(base).read()
ok, rows = True, ["id\tfunction\tresult\texpected"]
files = [f for f in ("mutants.toml", "mutants_bounds.toml") if os.path.exists(os.path.join(HERE, f))]
mutants = [m for f in files for m in tomllib.load(open(os.path.join(HERE, f), "rb"))["mutant"]]
# IDS=a,b runs only those mutants and leaves mutants_result.tsv alone.
ids = [i for i in os.environ.get("IDS", "").split(",") if i]
if ids:
    mutants = [m for m in mutants if m["id"] in ids]
for m in mutants:
    if src.count(m["original"]) != 1:
        print(m["id"], "original text not found exactly once"); ok = False; continue
    path = os.path.join(W, m["id"] + ".c")
    open(path, "w").write(src.replace(m["original"], m["mutated"]))
    # Harnesses that can see the mutated function (the table feeds all of them).
    only = {"utf_cp_bounds_len": "cp_bounds", "utf_cp_bounds": "cp_bounds", "utf_is_trail_byte": "cp_bounds",
            "utf8len_tab": ""}.get(m["function"], "^h_(byte2len|char2|ptr2)")
    r = subprocess.run(["bash", os.path.join(HERE, "run_cbmc.sh"), NV, path], capture_output=True, text=True,
                       env=dict(os.environ, ONLY=only))
    res = "caught" if r.returncode else "survived"
    if res != m["expect"] and not (res == "survived" and m["expect"] == "equivalent"):
        ok = False
    rows.append(f"{m['id']}\t{m['function']}\t{res}\t{m['expect']}")
    print(rows[-1], flush=True)
if not ids: open(os.path.join(HERE, "mutants_result.tsv"), "w").write("\n".join(rows) + "\n")
sys.exit(0 if ok else 1)
