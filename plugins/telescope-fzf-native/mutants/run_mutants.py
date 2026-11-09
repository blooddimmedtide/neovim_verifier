"""Apply each planted bug of mutants.toml to a copy of fzf.c and run its checks
until one fails (= caught). Usage: python3 -I run_mutants.py <fzf.c> [id-regex]
Writes mutants_result.tsv next to this file."""
import os, re, shutil, subprocess, sys, tempfile, tomllib
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
src = os.path.abspath(sys.argv[1]); only = sys.argv[2] if len(sys.argv) > 2 else None
muts = tomllib.load(open(os.path.join(HERE, "mutants.toml", ), "rb"))["mutant"]
text = open(src).read()
rows = []
for m in muts:
    if only and not re.search(only, m["id"]):
        continue
    if text.count(m["old"]) != 1:
        sys.exit(f"{m['id']}: anchor occurs {text.count(m['old'])} times")
    d = tempfile.mkdtemp()
    shutil.copy(os.path.join(os.path.dirname(src), "fzf.h"), d)
    f = os.path.join(d, "fzf.c")
    open(f, "w").write(text.replace(m["old"], m["new"]))
    caught = None
    for c in m["checks"]:
        if c == "difftest":
            r = subprocess.run(["bash", f"{ROOT}/difftest/run_difftest.sh", f, "20000", "1"], capture_output=True, text=True)
            bad = r.returncode == 1   # 2 = only the stale-slab count, which this file no longer has
        elif c.startswith("wp:"):
            r = subprocess.run(["bash", f"{ROOT}/wp/run_wp.sh", f, "20"], capture_output=True, text=True,
                               env={**os.environ, "ONLY": c[3:], "FZF_WP_MUTANT": "1"})
            # caught = WP ran and some goal was not proved (not a build error)
            bad = r.returncode != 0 and re.search(r": \d+ / \d+", r.stdout) is not None
        elif c.startswith("cbmc:"):
            r = subprocess.run(["bash", f"{ROOT}/cbmc/run_cbmc.sh", f, f"^{c[5:]}$"], capture_output=True, text=True)
            # caught = a property fails; a tool error (out of memory, ...) is not a catch
            bad = r.returncode != 0 and "FAILURE" in r.stdout
            if r.returncode != 0 and not bad:
                print(f"{m['id']}: {c}: TOOL ERROR\n{r.stdout[-400:]}", flush=True)
        print(f"{m['id']}: {c}: {'CAUGHT' if bad else 'not caught'}", flush=True)
        if bad:
            caught = c
            break
    rows.append(f"{m['id']}\t{caught or 'NOT CAUGHT'}")
    shutil.rmtree(d)
open(os.path.join(HERE, "mutants_result.tsv"), "w").write("id\tcaught_by\n" + "\n".join(rows) + "\n")
print("\n".join(rows))
