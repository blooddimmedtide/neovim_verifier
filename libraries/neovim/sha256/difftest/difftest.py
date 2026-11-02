"""Usage: python3 -I difftest.py <neovim checkout> [iterations]
Compiles src/nvim/sha256.c with gcc -O2 under ASan/UBSan, runs dt.c, checks every digest
against hashlib (random lengths 0..1199, random update splits incl. empty updates, and
sha256_bytes with and without salt), and runs sha256_self_test."""
import hashlib, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); NV = sys.argv[1]; N = sys.argv[2] if len(sys.argv) > 2 else "20000"
W = tempfile.mkdtemp(); stubs = os.path.join(HERE, "..", "cbmc", "stubs")
subprocess.run(["gcc", "-O2", "-fsanitize=address,undefined", "-fno-sanitize-recover=all", "-I", stubs, "-I", f"{NV}/src",
                f"{NV}/src/nvim/sha256.c", os.path.join(HERE, "dt.c"), "-o", f"{W}/dt"], check=True)
out = subprocess.run([f"{W}/dt", N, "12345"], capture_output=True, text=True, check=True).stdout.split("\n")
bad = checks = 0; last = None
for line in out:
    if not line: continue
    if line.startswith("B "):
        _, cut, salted, h = line.split(); cut = int(cut)
        want = hashlib.sha256(last if salted == "1" else last[:cut]).hexdigest()   # buf, then salt if given
        checks += 1; bad += h != want
    else:
        mhex, d = line.split(" "); last = bytes.fromhex(mhex)
        checks += 1; bad += hashlib.sha256(last).hexdigest() != d
print(f"self-test passed; {checks} digests, {bad} mismatches"); sys.exit(1 if bad else 0)
