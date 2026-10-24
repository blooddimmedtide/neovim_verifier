"""Build STATUS.md: per-file progress over every function in the inventory.

Usage: python3 -I tools/status.py libraries/neovim > STATUS.md
A function counts as done only when its status is "verified" or "fixed"
(a verified fix). Anything else, including partial results, is open.
"""
import collections, csv, sys, os

DONE = {"verified", "fixed"}   # admitted only; candidate and fixed-candidate stay open until both reviews pass


def read(path):
    with open(path) as f:
        return list(csv.DictReader(f, delimiter="\t"))


def main(lib):
    inv = read(os.path.join(lib, "inventory.tsv"))
    st = {(r["file"], r["function"]): r for r in read(os.path.join(lib, "status.tsv"))}
    per = collections.OrderedDict()
    for r in inv:
        s = st.get((r["file"], r["function"]), {}).get("status", "open")
        per.setdefault(r["file"], collections.Counter())[s] += 1
    total = sum(sum(c.values()) for c in per.values())
    done = sum(c[s] for c in per.values() for s in DONE)
    started = [f for f, c in per.items() if sum(c.values()) != c["open"]]
    print(f"# Neovim verification status\n")
    print(f"**{done} / {total} functions done** (verified, or a verified fix) across {len(per)} files.")
    print("A function is done only when every property in its contract is proved; partial results stay open.\n")
    print("## Files with work in progress or done\n")
    print("| File | Done | Partial | Open | Total |\n|---|---|---|---|---|")
    for f in started:
        c = per[f]; n = sum(c.values()); d = sum(c[s] for s in DONE)
        print(f"| {f} | {d} | {n - d - c['open']} | {c['open']} | {n} |")
    print("\n## Function details\n")
    print("| File | Function | Status | Evidence | Notes |\n|---|---|---|---|---|")
    for (f, fn), r in st.items():
        print(f"| {f} | `{fn}` | {r['status']} | {r['evidence']} | {r['notes']} |")
    print("\n## All files\n")
    print("| File | Done / Total |\n|---|---|")
    for f, c in per.items():
        print(f"| {f} | {sum(c[s] for s in DONE)} / {sum(c.values())} |")


if __name__ == "__main__":
    main(sys.argv[1])
