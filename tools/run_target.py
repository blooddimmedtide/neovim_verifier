"""Run a target's proofs and checks as listed in libraries/<lib>/vpipe.toml.

Usage: python3 -I tools/run_target.py <lib dir> <neovim checkout> [--fixed <fixed checkout>] [target ...]
With no target names, runs every target. Exit 0 only if every command passes.
"""
import os, subprocess, sys, tomllib

args = sys.argv[1:]
fixed = ""
if "--fixed" in args:
    i = args.index("--fixed"); fixed = os.path.abspath(args[i + 1]); del args[i:i + 2]
lib, src = os.path.abspath(args[0]), os.path.abspath(args[1])
sys.argv = [sys.argv[0]] + args
cfg = tomllib.load(open(os.path.join(lib, "vpipe.toml"), "rb"))
names = sys.argv[3:] or list(cfg.get("targets", {}))
failed = []
for name in names:
    t = cfg["targets"][name]
    for kind in ("prove", "check"):
        for cmd in t.get(kind, []):
            if "{fixed}" in cmd and not fixed:
                print(f"SKIP  {name} {kind}: {cmd} (no --fixed checkout)"); continue
            cmd = cmd.format(src=src, fixed=fixed)
            print(f"::group::{name} {kind}: {cmd}", flush=True)
            r = subprocess.run(cmd, shell=True, cwd=lib, capture_output=True, text=True)
            print(r.stdout + r.stderr, flush=True)
            rc = r.returncode
            print("::endgroup::", flush=True)
            print(f"{'PASS' if rc == 0 else 'FAIL'}  {name} {kind}: {cmd}", flush=True)
            if rc:
                failed.append(f"{name}: {cmd}")
                # Annotations are readable through the API even when logs are not.
                tail = " | ".join(l.strip() for l in (r.stdout + r.stderr).strip().splitlines()[-12:])
                print(f"::error title={name} {kind} failed::{cmd}: {tail[:900]}", flush=True)
print("\nAll passed." if not failed else "\nFailed:\n  " + "\n  ".join(failed))
sys.exit(1 if failed else 0)
