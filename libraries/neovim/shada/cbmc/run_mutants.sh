#!/bin/bash
# Confirm the proofs catch each planted bug in mutants.toml. Exit 0 iff all caught.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd)
python3 -I "$HERE/build.py" "$NV" /tmp/base_shada.c || exit 1
python3 -I - "$HERE/mutants.toml" <<'PY'
import sys, tomllib, subprocess, tempfile, os, re
here=os.path.dirname(os.path.abspath(sys.argv[1]))
base=open('/tmp/base_shada.c').read()
muts=tomllib.load(open(sys.argv[1],'rb'))['mutant']
ok=True
for m in muts:
    if m['find'] not in base:
        print(f"{m['name']}: FIND NOT PRESENT"); ok=False; continue
    mut=base.replace(m['find'], m['repl'])
    f=tempfile.NamedTemporaryFile('w',suffix='.c',delete=False); f.write(mut); f.close()
    r=subprocess.run(['bash',os.path.join(here,'run_cbmc.sh'),os.environ.get('NV','/tmp/claude-0/nv'),f.name],
                     capture_output=True,text=True)
    caught = 'FAILED' in r.stdout
    print(f"{m['name']}: {'caught' if caught else 'MISSED (proof vacuous!)'}")
    ok = ok and caught
    os.unlink(f.name)
sys.exit(0 if ok else 1)
PY
