"""Run the reviewer's planted bugs (mutants.toml) against the garray.c proof.

  python3 -I run_mutants.py <upstream checkout> <fixed checkout> [id ...] [--timeout S]

Each mutant names the function it changes, the tree (upstream or fixed), and an exact
substring `original` of that function's code. The runner builds the proof file for that
tree (wp/build.py), replaces `original` by `mutated` in the built file (so the ACSL stays
in place and a mutant on an annotation anchor is judged by WP, not by an anchor mismatch),
and runs Frama-C WP on that function with the same options as wp/run_wp.sh. A mutant is
caught when at least one goal is not proved (every goal is proved on the unmutated code).
`original` must occur exactly once inside the function, else the mutant is an error.
Results go to mutants_result.tsv (id, tree, function, verdict, failed goals).
"""
import os, re, shutil, subprocess, sys, tempfile, tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]
T = "60"
if "--timeout" in args:
    i = args.index("--timeout"); T = args[i + 1]; del args[i:i + 2]
TREES = {"upstream": os.path.abspath(args[0]), "fixed": os.path.abspath(args[1])}
only = set(args[2:])
FRAMA = ["frama-c", "-machdep", "x86_64", "-cpp-extra-args=-I stubs"]
WP = ["-wp", "-wp-rte", "-wp-model", "Typed+Cast", "-wp-prover", "z3,cvc5",
      "-wp-timeout", T, "-wp-par", str(os.cpu_count()), "-wp-cache", "none"]


def built(tree):
    w = tempfile.mkdtemp()
    os.mkdir(os.path.join(w, "stubs"))
    for d in (os.path.join(HERE, "wp/stubs"), os.path.join(HERE, "../memory/wp/stubs")):
        for f in os.listdir(d):
            if f.endswith(".h"):
                shutil.copy(os.path.join(d, f), os.path.join(w, "stubs"))
    subprocess.run([sys.executable, "-I", os.path.join(HERE, "wp/build.py"), TREES[tree],
                    os.path.join(w, "ga.c"), tree], check=True)
    return w


def function_span(text, fn):
    m = re.search(r"^[A-Za-z_][\w \*]*\b" + re.escape(fn) + r"\(", text, re.M)
    if not m:
        sys.exit(f"function {fn} not found in the built file")
    end = text.index("\n}\n", m.start())
    return m.start(), end


muts = tomllib.load(open(os.path.join(HERE, "mutants.toml"), "rb"))["mutant"]
res_path = os.path.join(HERE, "mutants_result.tsv")
done = set()
if os.path.exists(res_path):
    done = {l.split("\t")[0] for l in open(res_path).read().splitlines()[1:]}
else:
    open(res_path, "w").write("id\ttree\tfunction\tverdict\tfailed goals\n")
cache, failures = {}, 0
for m in muts:
    if (only and m["id"] not in only) or m["id"] in done:
        continue
    tree = m.get("tree", "upstream")
    if tree not in cache:
        cache[tree] = built(tree)
    w = cache[tree]
    src = open(os.path.join(w, "ga.c")).read()
    s, e = function_span(src, m["function"])
    body = src[s:e]
    if body.count(m["original"]) != 1:
        print(f"{m['id']}: ERROR original occurs {body.count(m['original'])} times in {m['function']}")
        failures += 1
        continue
    mutated = src[:s] + body.replace(m["original"], m["mutated"]) + src[e:]
    open(os.path.join(w, "mut.c"), "w").write(mutated)
    r = subprocess.run(FRAMA + ["mut.c"] + WP + ["-wp-fct", m["function"]], cwd=w,
                       capture_output=True, text=True)
    out = r.stdout + r.stderr
    g = re.search(r"Proved goals: +(\d+) / (\d+)", out)
    bad = [l.split("] ", 2)[-1].split(" (")[0] for l in out.splitlines()
           if re.search(r"\[(Timeout|Unknown|Failed)\]", l)]
    if g and g.group(1) == g.group(2):
        verdict = "SURVIVED"
        failures += m.get("expect", "caught") == "caught"
    elif g:
        verdict = "caught"
    else:  # the mutant does not even parse or type-check: caught by the kernel
        verdict = "caught (frama-c rejects the file)"
        bad = [l for l in out.splitlines() if "rror" in l][:2]
    print(f"{m['id']} ({tree} {m['function']}): {verdict} {', '.join(bad[:4])}", flush=True)
    with open(res_path, "a") as f:
        f.write(f"{m['id']}\t{tree}\t{m['function']}\t{verdict}\t{','.join(bad)}\n")
sys.exit(1 if failures else 0)
