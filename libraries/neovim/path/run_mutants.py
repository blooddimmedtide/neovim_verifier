"""Run each planted bug in mutants.toml; every one must make its function's WP run fail.

Usage: python3 -I run_mutants.py <upstream checkout> <fixed checkout> [timeout]
(signed char only: the planted bugs do not depend on char signedness)
Writes mutants_result.tsv. Exit 0 = every mutant caught.
"""
import os, subprocess, sys, tomllib
HERE = os.path.dirname(os.path.abspath(__file__))
up, fx = sys.argv[1], sys.argv[2]
T = sys.argv[3] if len(sys.argv) > 3 else "20"
ms = tomllib.load(open(os.path.join(HERE, "mutants.toml"), "rb"))["mutant"]
only = os.environ.get("VP_MUTANTS_FROM")  # rerun from mutant N on (1-based)
start = int(only) if only else 1
rows, ok = [], True
for i, m in enumerate(ms, 1):
    if i < start:
        continue
    mode = m.get("mode", "upstream")
    env = dict(os.environ, VP_MACHDEPS="x86_64", VP_MUTANT="\x1f".join([m["fn"], m["old"], m["new"]]))
    r = subprocess.run(["bash", os.path.join(HERE, "wp", "run_wp.sh"), up if mode == "upstream" else fx,
                        mode, T, m["fn"]], env=env, capture_output=True, text=True)
    caught = r.returncode != 0 and "build:" not in (r.stdout + r.stderr)  # a build error is not a catch
    ok &= caught
    rows.append(f"{i}\t{m['fn']}\t{mode}\t{'caught' if caught else 'MISSED'}\t{m['old']} -> {m['new']}")
    print(rows[-1], flush=True)
out = os.path.join(HERE, "mutants_result.tsv")
if start > 1:  # a partial rerun adds its rows to the earlier result
    open(out, "a").write("\n".join(rows) + "\n")
else:
    open(out, "w").write("n\tfunction\tmode\tresult\tchange\n" + "\n".join(rows) + "\n")
sys.exit(0 if ok else 1)
