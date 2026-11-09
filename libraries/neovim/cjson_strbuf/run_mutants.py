"""Run the reviewer's planted bugs (mutants.toml) against the strbuf CBMC proof.

  python3 -I run_mutants.py [--src DIR] [--jobs N] [id ...]

DIR holds the FIXED strbuf.c and strbuf.h (default: extracted with `git show` from
/home/user/verified_neovim at claude/project-thread-gritim; nothing is checked out).
Their sha256 must equal the pins in cbmc/run_cbmc.sh (FIX_C and H).

For each mutant the mutated sources go to a temp dir and the harnesses of
cbmc/run_cbmc.sh are run with exactly its CBMC flags (the harness list and flags
are read from run_cbmc.sh and the flags are checked to be the ones it uses), both
char signednesses, the harnesses of the mutated function first. A mutant is
caught when any run fails verification (a parse/type error is an "error", not a
catch). A survivor has passed all 20 runs.
For survivors the reviewer's strengthened harness (review/harness_review.c, the
suggested fix) is run too, recorded in the review_caught_by column.

Results: mutants_result.tsv (id, function, result, caught_by, expected,
review_caught_by). Exit 1 if a mutant with expect = "caught" survives the
original harnesses, or if an "equivalent" one is caught (the reason is wrong).
"""
import concurrent.futures, hashlib, os, re, shutil, subprocess, sys, tempfile, tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
CB = os.path.join(HERE, "cbmc")
RV = os.path.join(HERE, "review")
CBMC = "cbmc"
args = sys.argv[1:]
src = None; jobs = 4
if "--src" in args:
    i = args.index("--src"); src = args[i + 1]; del args[i:i + 2]
if "--jobs" in args:
    i = args.index("--jobs"); jobs = int(args[i + 1]); del args[i:i + 2]
only = set(args)

# ---- harness list and flags, from run_cbmc.sh ----
sh = open(os.path.join(CB, "run_cbmc.sh")).read()
FLAGS = ["--arch", "x86_64", "--bounds-check", "--pointer-check", "--signed-overflow-check",
         "--conversion-check"]
need = "--arch x86_64 ${sign#signed} --bounds-check --pointer-check --signed-overflow-check --conversion-check"
assert need in sh and "--unwinding-assertions --sat-solver cadical" in sh, "run_cbmc.sh flags changed"
m = re.search(r"for hu in (.*?); do", sh, re.S)
HARN = [tuple(x.split(":")) for x in m.group(1).replace("\\\n", " ").split()]
assert len(HARN) == 10, HARN
SIGNS = [[], ["--unsigned-char"]]
pin = dict(re.findall(r"^(FIX_C|H)=([0-9a-f]{64})", sh, re.M))

# ---- which harnesses check which function (run first) ----
REL = {
    "die": ["h_die"], "strbuf_init": ["h_init", "h_new"], "strbuf_new": ["h_new"],
    "debug_stats": ["h_debug_stats", "h_free", "h_free_to_string"], "strbuf_free": ["h_free"],
    "strbuf_free_to_string": ["h_free_to_string"],
    "calculate_new_size": ["h_calculate_new_size", "h_resize"], "strbuf_resize": ["h_resize"],
    "strbuf_append_string": ["h_append_string"],
}
WHICH = {"strbuf_reset": 0, "strbuf_allocated": 1, "strbuf_empty_length": 2, "strbuf_empty_ptr": 3,
         "strbuf_length": 4, "strbuf_string": 5, "strbuf_ensure_null": 6,
         "strbuf_ensure_empty_length": 7, "strbuf_append_char": 8, "strbuf_append_char_unsafe": 9,
         "strbuf_append_mem": 10, "strbuf_append_mem_unsafe": 11, "strbuf_extend_length": 12,
         "strbuf_set_length": 13}
UNW = {"r_" + h[2:]: u for h, u in HARN}


def run_cbmc(harness_file, h, u, sign, d, extra=()):
    cmd = [CBMC, harness_file, "--function", h, "-I", os.path.dirname(harness_file), "-I", d,
           f'-DSTRBUF_C="{d}/strbuf.c"'] + FLAGS + sign + ["--unwind", u] + list(extra) + \
          ["--unwindset", "calculate_new_size.0:66", "--unwinding-assertions", "--sat-solver", "cadical"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    except subprocess.TimeoutExpired:
        return "timeout", ""
    out = r.stdout + r.stderr
    if "VERIFICATION SUCCESSFUL" in out:
        return "proved", ""
    if "VERIFICATION FAILED" in out:
        f = [l for l in out.splitlines() if l.endswith("FAILURE")]
        why = f[0].split("] ", 1)[-1].replace(": FAILURE", "") if f else "?"
        return "failed", why[:120]
    return "error", " ".join(l for l in out.splitlines() if "rror" in l)[:160]


def original_runs(fn):
    first = REL.get(fn, ["h_helpers", "h_append_string"] if fn in WHICH else [])
    order = first + [h for h, _ in HARN if h not in first]
    unw = dict(HARN)
    return [(h, unw[h], s) for h in order for s in SIGNS]


def review_runs(fn):
    if fn in WHICH:
        hs = [("r_helpers", ["-DWHICH=%d" % WHICH[fn]])]
        if fn in ("strbuf_empty_length", "strbuf_ensure_null"):
            hs += [("r_append_string", []) if fn == "strbuf_empty_length" else ("r_init", [])]
    else:
        hs = [("r_" + h[2:], []) for h in REL[fn]]
    return [(h, UNW[h], s, ex + ["--unwindset", "calculate_new_size.0:66"]) for h, ex in hs for s in SIGNS]


def sname(s): return "unsigned" if s else "signed"


def check(m, base):
    w = tempfile.mkdtemp(prefix="strbuf_mut_")
    try:
        for f in ("strbuf.c", "strbuf.h"):
            shutil.copy(os.path.join(base, f), w)
        p = os.path.join(w, m["file"]); text = open(p).read()
        n = text.count(m["original"])
        if n != 1:
            return "error", f"original occurs {n} times", ""
        open(p, "w").write(text.replace(m["original"], m["mutated"]))
        res, by = "survived", ""
        for h, u, s in original_runs(m["function"]):
            v, why = run_cbmc(os.path.join(CB, "harness.c"), h, u, s, w)
            if v == "failed":
                res, by = "caught", f"{h} ({sname(s)}): {why}"; break
            if v != "proved":
                return "error", f"{h} ({sname(s)}): {v} {why}", ""
        rby = ""
        if res == "survived":
            rby = "not caught"
            for h, u, s, ex in review_runs(m["function"]):
                v, why = run_cbmc(os.path.join(RV, "harness_review.c"), h, u, s, w, ex)
                if v == "failed":
                    rby = f"{h}{' ' + ex[0] if ex[0].startswith('-DWHICH') else ''} ({sname(s)}): {why}"; break
                if v != "proved":
                    rby = f"{h}: {v} {why}"; break
        return res, by, rby
    finally:
        shutil.rmtree(w, ignore_errors=True)


def main():
    tmp = tempfile.mkdtemp(prefix="strbuf_src_")
    if src is None:
        for f in ("strbuf.c", "strbuf.h"):
            data = subprocess.run(["git", "-C", "/home/user/verified_neovim", "show",
                                   f"claude/project-thread-gritim:src/cjson/{f}"],
                                  capture_output=True, check=True).stdout
            open(os.path.join(tmp, f), "wb").write(data)
        base = tmp
    else:
        base = os.path.abspath(src)
    for f, key in (("strbuf.c", "FIX_C"), ("strbuf.h", "H")):
        hsh = hashlib.sha256(open(os.path.join(base, f), "rb").read()).hexdigest()
        assert hsh == pin[key], f"{f}: {hsh} is not the pinned fixed source"
    # sanity: the unmutated sources prove (one cheap harness per signedness)
    for s in SIGNS:
        v, why = run_cbmc(os.path.join(CB, "harness.c"), "h_free_to_string", "4", s, base)
        assert v == "proved", (v, why)
    ms = tomllib.load(open(os.path.join(HERE, "mutants.toml"), "rb"))["mutant"]
    ms = [m for m in ms if not only or m["id"] in only]
    out = {}
    with concurrent.futures.ThreadPoolExecutor(jobs) as ex:
        futs = {ex.submit(check, m, base): m for m in ms}
        for f in concurrent.futures.as_completed(futs):
            m = futs[f]; out[m["id"]] = f.result()
            print(m["id"], *out[m["id"]], sep="\t", flush=True)
    bad = []
    path = os.path.join(HERE, "mutants_result.tsv")
    with open(path, "w") as f:
        f.write("id\tfunction\tresult\tcaught_by\texpected\treview_caught_by\n")
        for m in ms:
            res, by, rby = out[m["id"]]
            exp = "caught" if m["expect"] == "caught" else "equivalent"
            f.write(f"{m['id']}\t{m['function']}\t{res}\t{by}\t{exp}\t{rby}\n")
            if res == "error" or (exp == "caught" and res != "caught") or (exp == "equivalent" and res == "caught"):
                bad.append((m["id"], exp, res))
    shutil.rmtree(tmp, ignore_errors=True)
    n_c = sum(1 for m in ms if out[m["id"]][0] == "caught")
    print(f"\n{n_c}/{len(ms)} caught; results in {path}")
    for b in bad:
        print("PROOF GAP / MISMATCH:", *b)
    sys.exit(1 if bad else 0)


main()
