"""Run a target's proofs and checks as listed in libraries/<lib>/vpipe.toml.

Usage: python3 -I tools/run_target.py <lib dir> <neovim checkout> [target ...]
With no target names, runs every target. Exit 0 only if every command passes.
"""
import os, subprocess, sys, tomllib

lib, src = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
cfg = tomllib.load(open(os.path.join(lib, "vpipe.toml"), "rb"))
names = sys.argv[3:] or list(cfg.get("targets", {}))
failed = []
for name in names:
    t = cfg["targets"][name]
    for kind in ("prove", "check"):
        for cmd in t.get(kind, []):
            cmd = cmd.format(src=src)
            print(f"::group::{name} {kind}: {cmd}", flush=True)
            rc = subprocess.run(cmd, shell=True, cwd=lib).returncode
            print("::endgroup::", flush=True)
            print(f"{'PASS' if rc == 0 else 'FAIL'}  {name} {kind}: {cmd}", flush=True)
            if rc:
                failed.append(f"{name}: {cmd}")
print("\nAll passed." if not failed else "\nFailed:\n  " + "\n  ".join(failed))
sys.exit(1 if failed else 0)
