"""Run the reviewer's planted bugs (mutants.toml) against the xutils.c proofs.

  python3 -I run_mutants.py [--src FILE] [--nv NEOVIM] [--no-wp] [id ...]

FILE is the FIXED xutils.c (default /tmp/claude-0/xd/xutils_fixed.c); NEOVIM is a checkout
with the xdiff headers (default /home/user/verified_neovim). Each mutant replaces `original`
(which must occur exactly once) by `mutated` in a temp copy and runs the proof CLAIM.md lists:
  cbmc = <harness>: cbmc/run_cbmc.sh with ONLY=^<harness>$ (both char signednesses, the
                    script's own flags and unwinding);
  wp = <function>:  wp/build_wp.py on the mutant, then frama-c -wp -wp-fct <function> with
                    the flags of CLAIM.md (Typed+Cast, -wp-rte, z3+cvc5, timeout 60, -wp-par 1).
One process at a time. caught = the proof fails; survived = it passes; error = the mutant did
not build (parse error, build_wp anchor missing).
Results: mutants_result.tsv (id, function, tool, result, detail, expected, verdict), where
verdict is ok / GAP (expected caught, survived) / WRONG-EQUIV (expected equivalent, caught).
"""
import os, re, subprocess, sys, tempfile, tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]
src = "/tmp/claude-0/xd/xutils_fixed.c"; nv = "/home/user/verified_neovim"; no_wp = False
if "--src" in args:
    i = args.index("--src"); src = args[i + 1]; del args[i:i + 2]
if "--nv" in args:
    i = args.index("--nv"); nv = args[i + 1]; del args[i:i + 2]
if "--no-wp" in args:
    args.remove("--no-wp"); no_wp = True
only = set(args)
env = dict(os.environ)
env["PATH"] = os.path.expanduser("~/.nix-profile/bin") + ":" + os.path.expanduser("~/.local/bin") + ":" + env["PATH"]
WPFLAGS = ["-machdep", "x86_64", "-wp", "-wp-rte", "-wp-model", "Typed+Cast", "-wp-prover", "z3,cvc5",
           "-wp-timeout", "60", "-wp-par", "1", "-wp-cache", "none"]

base = open(src).read()
muts = tomllib.load(open(os.path.join(HERE, "mutants.toml"), "rb"))["mutant"]


def run_cbmc(path, h):
    e = dict(env, ONLY=f"^{h}$")
    r = subprocess.run(["bash", os.path.join(HERE, "cbmc", "run_cbmc.sh"), nv, path],
                       capture_output=True, text=True, env=e, timeout=3600)
    out = r.stdout + r.stderr
    if "FAILED" in out:
        if re.search(r"PARSING ERROR|CONVERSION ERROR|syntax error|error:", out):
            return "error", " ".join(out.split())[:160]
        f = [l.strip() for l in out.splitlines() if "FAILURE" in l]
        return "caught", (f[0] if f else out.strip().splitlines()[0])[:160]
    if out.count(": proved") == 2:
        return "survived", ""
    return "error", " ".join(out.split())[:160]


def run_wp(path, fn, d):
    out_c = os.path.join(d, "wp.c")
    r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "wp", "build_wp.py"), path, out_c],
                       capture_output=True, text=True)
    if r.returncode:
        return "error", "build_wp: " + r.stderr.strip().splitlines()[-1][:140]
    r = subprocess.run(["frama-c", out_c] + WPFLAGS + ["-wp-fct", fn], capture_output=True, text=True,
                       env=env, timeout=3600, cwd=d)
    out = r.stdout + r.stderr
    m = re.search(r"Proved goals:\s+(\d+) / (\d+)", out)
    if not m:
        return "error", " ".join(l for l in out.splitlines() if "rror" in l)[:160]
    if m.group(1) != m.group(2):
        bad = [l.strip() for l in out.splitlines() if re.search(r"Goal .*(Timeout|Unknown|Failed)", l)]
        return "caught", f"{m.group(1)}/{m.group(2)} " + (bad[0] if bad else "")[:120]
    return "survived", f"{m.group(1)}/{m.group(2)}"


rows = []
res_path = os.path.join(HERE, "mutants_result.tsv")
for mu in muts:
    if only and mu["id"] not in only:
        continue
    tool = "cbmc:" + mu["cbmc"] if "cbmc" in mu else "wp:" + mu["wp"]
    if no_wp and "wp" in mu:
        continue
    n = base.count(mu["original"])
    if n != 1:
        res, det = "error", f"original occurs {n} times"
    else:
        with tempfile.TemporaryDirectory(dir="/tmp/claude-0/xd-review") as d:
            p = os.path.join(d, "xutils.c")
            open(p, "w").write(base.replace(mu["original"], mu["mutated"], 1))
            res, det = run_cbmc(p, mu["cbmc"]) if "cbmc" in mu else run_wp(p, mu["wp"], d)
    exp = mu["expect"]
    verdict = "ok"
    if exp == "caught" and res == "survived": verdict = "GAP"
    if exp.startswith("equivalent") and res == "caught": verdict = "WRONG-EQUIV"
    if res == "error": verdict = "error"
    row = [mu["id"], mu["function"], tool, res, det.replace("\t", " "), exp.split(":")[0], verdict]
    print("\t".join(row), flush=True)
    rows.append(row)
    with open(res_path, "w") as f:
        f.write("id\tfunction\ttool\tresult\tdetail\texpected\tverdict\n")
        for r_ in rows: f.write("\t".join(r_) + "\n")
sys.exit(1 if any(r[6] in ("GAP", "WRONG-EQUIV") for r in rows) else 0)
