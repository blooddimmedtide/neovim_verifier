"""Run the reviewer's planted bugs (mutants.toml) against the full base64.c proof.

  python3 -I run_mutants.py <upstream checkout> <fixed checkout> [id ...] [--timeout S]

For each mutant the mutated base64.c goes through every check the proof uses,
stopping at the first one that rejects it:
  1. tool-patch equivalence harnesses (equiv/, CBMC, all inputs)
  2. htobe bridge (bridge/, CBMC)
  3. Frama-C WP on the function the mutant is in. The mutation is applied to the
     annotated file (after annotate.py), so mutants on annotation anchor lines
     are judged by WP, not by an anchor mismatch. If the original text is gone
     from the annotated file (a tool patch rewrote it), the mutant is applied to
     the source first and annotate.py's refusal is the (documented) catch.
A mutant is caught when a step fails. For WP, only goals that are proved on the
unmutated code under the same settings count: the baseline run's slow goals
(timeouts at this --timeout) are recorded in mutants_baseline.tsv and ignored.
Results go to mutants_result.tsv; finished ids are skipped on a rerun.
"""
import os, re, shutil, subprocess, sys, tempfile, tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
args = [a for a in sys.argv[1:]]
T = "60"
if "--timeout" in args:
    i = args.index("--timeout"); T = args[i + 1]; del args[i:i + 2]
UP, FIX = os.path.abspath(args[0]), os.path.abspath(args[1])
only = set(args[2:])
FRAMA = ["frama-c", "-cpp-extra-args=-I stubs -DNDEBUG", "-machdep", "x86_64"]
WP = ["-wp", "-wp-rte", "-wp-model", "Typed+Cast", "-wp-prover", "z3,cvc5",
      "-wp-timeout", T, "-wp-par", str(os.cpu_count()), "-wp-cache", "none"]


def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def wp_failures(path, part, cwd):
    fn = "base64_decode" if part == "dec" else "base64_encode"
    rc, out = run(FRAMA + [os.path.basename(path)] + WP + ["-wp-fct", fn], cwd=cwd)
    g = re.search(r"Proved goals: +(\d+) / (\d+)", out)
    bad = [l.split("] ", 2)[-1].split(" (")[0] for l in out.splitlines()
           if re.search(r"\[(Timeout|Unknown|Failed)\]", l)]
    return g, bad, out


BASE = {}
def baseline(tree_name, tree, part):
    key = f"{tree_name}:{part}"
    path = os.path.join(HERE, "mutants_baseline.tsv")
    if not BASE and os.path.exists(path):
        for l in open(path).read().splitlines():
            k, t_, goals = (l.split("\t") + [""])[:3]
            if t_ == T: BASE[k] = set(filter(None, goals.split(",")))
    if key not in BASE:
        w = tempfile.mkdtemp()
        shutil.copytree(os.path.join(HERE, "wp/stubs"), os.path.join(w, "stubs"))
        out_c = os.path.join(w, f"b64_{part}.c")
        subprocess.run([sys.executable, "-I", os.path.join(HERE, "wp/annotate.py"),
                        os.path.join(tree, "src/nvim/base64.c"), out_c, part], check=True, capture_output=True)
        g, bad, out = wp_failures(out_c, part, w)
        BASE[key] = set(bad)
        with open(path, "a") as f:
            f.write(f"{key}\t{T}\t{','.join(sorted(bad))}\n")
    return BASE[key]


def check(m):
    tree = FIX if m.get("tree") == "fixed" else UP
    w = tempfile.mkdtemp()
    nv = os.path.join(w, "nv"); os.makedirs(os.path.join(nv, "src/nvim"))
    src = open(os.path.join(tree, "src/nvim/base64.c")).read()
    if src.count(m["original"]) != 1:
        return "error", f"original found {src.count(m['original'])} times in source"
    msrc = src.replace(m["original"], m["mutated"])
    open(os.path.join(nv, "src/nvim/base64.c"), "w").write(msrc)
    # 1. equivalence harnesses (regenerated harnesses must match; then CBMC)
    rc, out = run(["bash", os.path.join(HERE, "equiv/run_equiv.sh"), nv])
    if rc:
        return "caught", "equiv: " + "; ".join(l for l in out.splitlines() if l.startswith(("FAILED", "stale")))[:200]
    # 2. bridge
    rc, out = run(["bash", os.path.join(HERE, "bridge/run_bridge.sh"), nv])
    if rc:
        return "caught", "bridge: CBMC " + ("failed" if "VERIFICATION FAILED" in out else "error")
    # 3. WP on the function containing the mutation
    part = "dec" if src.index(m["original"]) > src.index("char *base64_decode(") else "enc"
    if src.index(m["original"]) < src.index("char *base64_encode("):
        part = "enc"   # tables and htobe helpers sit above the encoder
    shutil.copytree(os.path.join(HERE, "wp/stubs"), os.path.join(w, "stubs"))
    out_c = os.path.join(w, f"b64_{part}.c")
    rc, out = run([sys.executable, "-I", os.path.join(HERE, "wp/annotate.py"),
                   os.path.join(tree, "src/nvim/base64.c"), out_c, part])
    ann = open(out_c).read()
    if ann.count(m["original"]) == 1:
        open(out_c, "w").write(ann.replace(m["original"], m["mutated"]))
        how = "post-annotate"
    else:   # the text was rewritten by a tool patch: mutate the source instead
        rc, out = run([sys.executable, "-I", os.path.join(HERE, "wp/annotate.py"),
                       os.path.join(nv, "src/nvim/base64.c"), out_c, part])
        if rc:
            return "caught", "annotate.py refused (tool-patch text changed): " + out.strip().splitlines()[-1][:150]
        how = "pre-annotate"
    base = baseline(m.get("tree", "upstream"), tree, part)
    g, bad, out = wp_failures(out_c, part, w)
    if not g:
        return "caught", f"WP error ({how}): " + out.strip().splitlines()[-1][:150]
    new = [b for b in bad if b not in base]
    if new:
        return "caught", f"WP {g.group(1)}/{g.group(2)} ({how}), newly failing: " + ", ".join(new[:4])
    return "SURVIVED", f"WP {g.group(1)}/{g.group(2)} ({how}); only baseline-slow goals failed" if bad else f"WP {g.group(1)}/{g.group(2)} ({how})"


ms = tomllib.load(open(os.path.join(HERE, "mutants.toml"), "rb"))["mutant"]
res_path = os.path.join(HERE, "mutants_result.tsv")
done = {}
if os.path.exists(res_path):
    for l in open(res_path).read().splitlines()[1:]:
        done[l.split("\t")[0]] = l
for m in ms:
    if (only and m["id"] not in only) or (not only and m["id"] in done):
        continue
    status, detail = check(m)
    done[m["id"]] = f"{m['id']}\t{status}\t{detail}"
    print(done[m["id"]], flush=True)
    with open(res_path, "w") as f:
        f.write("id\tstatus\tdetail\n" + "\n".join(done[x["id"]] for x in ms if x["id"] in done) + "\n")
