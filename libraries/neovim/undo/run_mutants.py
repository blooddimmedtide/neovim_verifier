"""Run the planted bugs of mutants.toml against the undo-file proofs.

Usage: python3 -I run_mutants.py [upstream tree] [fixed tree] [--only m01,m02]
Defaults: /home/user/nvim-upstream and /home/user/verified_neovim.
For each mutant: check `find` occurs exactly once in the base tree's source file and exactly once
in the pristine build.py output (build.py's sha pin would reject an edited tree), apply the
replacement to the built undo_io.c, then run the mutant's harness (ONLY=^h$ run_cbmc.sh with the
prebuilt file) or, for "wp", annotate.py + frama-c with the run_wp.sh flags. A mutant is caught
when the run exits non-zero. Writes mutants_result.tsv next to this script.
"""
import os, re, subprocess, sys, tempfile, tomllib

HERE = os.path.dirname(os.path.abspath(__file__))

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)

def build(tree, out):
    r = run([sys.executable, "-I", os.path.join(HERE, "cbmc/build.py"), tree, out])
    if r.returncode: sys.exit(f"pristine build failed for {tree}:\n{r.stderr}")
    return open(out).read()

def wp(c_file, w):
    ann = os.path.join(w, "undo_wp.c")
    r = run([sys.executable, "-I", os.path.join(HERE, "wp/annotate.py"), c_file, ann])
    if r.returncode: return 1, "annotate failed (anchor hit by mutant): " + r.stderr
    env = dict(os.environ, PATH=os.path.expanduser("~/.nix-profile/bin") + ":" + os.environ["PATH"])
    r = run(["frama-c", f"-cpp-extra-args=-I{HERE}/cbmc", ann, "-wp", "-wp-rte", "-wp-model",
             "Typed+Cast", "-wp-fct", "uhp_table_find", "-wp-prover", "z3,cvc5",
             "-wp-timeout", "30", "-wp-cache", "none"], env=env, timeout=1800)
    out = r.stdout + r.stderr
    m = re.search(r"Proved goals:\s+(\d+)\s*/\s*(\d+)", out)
    ok = m is not None and m.group(1) == m.group(2)
    return (0 if ok else 1), (m.group(0) if m else out[-400:])

def main():
    argv, only = sys.argv[1:], None
    if "--only" in argv:
        i = argv.index("--only"); only = set(argv[i + 1].split(",")); del argv[i:i + 2]
    args = argv
    up = os.path.abspath(args[0] if len(args) > 0 else "/home/user/nvim-upstream")
    fx = os.path.abspath(args[1] if len(args) > 1 else "/home/user/verified_neovim")
    muts = tomllib.load(open(os.path.join(HERE, "mutants.toml"), "rb"))["mutant"]
    w = tempfile.mkdtemp()
    base = {"upstream": (up, build(up, os.path.join(w, "up.c"))),
            "fixed": (fx, build(fx, os.path.join(w, "fx.c")))}
    rows, bad = [], 0
    for m in muts:
        if only and m["id"] not in only: continue
        tree, text = base[m.get("base", "upstream")]
        src = open(os.path.join(tree, m["file"])).read()
        if src.count(m["find"]) != 1 or text.count(m["find"]) != 1:
            print(f"{m['id']}: find matches {src.count(m['find'])}x in source, "
                  f"{text.count(m['find'])}x in build"); sys.exit(1)
        mc = os.path.join(w, f"{m['id']}.c")
        open(mc, "w").write(text.replace(m["find"], m["replace"]))
        if m["harness"] == "wp":
            rc, note = wp(mc, w)
        else:
            r = run(["bash", os.path.join(HERE, "cbmc/run_cbmc.sh"), tree, mc],
                    env=dict(os.environ, ONLY=f"^{m['harness']}$"), timeout=1800)
            rc, note = r.returncode, " ".join(l for l in r.stdout.splitlines() if "FAILED" in l)
        caught = rc != 0
        exp = not m.get("expect_uncaught", False)
        if caught != exp and not m.get("equivalent", False): bad += 1
        print(f"{m['id']} {m['function']} {m['harness']}: {'caught' if caught else 'NOT caught'}"
              f"{'' if caught == exp else '  (UNEXPECTED)'}  {note[:120]}", flush=True)
        rows.append((m["id"], m["function"], m["harness"], "yes" if caught else "no",
                     "yes" if m.get("equivalent") else "no",
                     "yes" if m.get("expect_uncaught") else "no"))
    if not only:
        with open(os.path.join(HERE, "mutants_result.tsv"), "w") as f:
            f.write("id\tfunction\tharness\tcaught\tequivalent\texpect_uncaught\n")
            for r in rows: f.write("\t".join(r) + "\n")
    n = sum(1 for r in rows if r[4] == "no")
    c = sum(1 for r in rows if r[4] == "no" and r[3] == "yes")
    print(f"caught {c}/{n} non-equivalent mutants; {bad} unexpected")
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
