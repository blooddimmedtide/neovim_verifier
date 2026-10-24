"""Differential test: pristine base64.c vs the tool-patched, annotated file WP proves,
and both vs RFC 4648 (Python's base64 module, with canonical-form checking).

  python3 -I difftest.py <neovim checkout> [random cases]

Builds two native binaries with gcc, feeds both the RFC 4648 test vectors, edge
cases and random inputs (valid, corrupted and random strings for the decoder),
and fails on any disagreement. This checks that what WP reads is what the
compiler builds, and that the proved spec matches the standard on real runs.
"""
import base64, binascii, os, random, struct, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
NV = os.path.abspath(sys.argv[1])
N = int(sys.argv[2]) if len(sys.argv) > 2 else 20000
SRC = os.path.join(NV, "src/nvim/base64.c")
tmp = tempfile.mkdtemp()


def build(src, name, extra=()):
    exe = os.path.join(tmp, name)
    subprocess.run(["gcc", "-O2", "-std=gnu99", "-w", "-I", os.path.join(HERE, "stubs"),
                    "-I", os.path.join(NV, "src"), f'-DNVIM_BASE64_C="{src}"', *extra,
                    os.path.join(HERE, "driver.c"), "-o", exe], check=True)
    return exe


ann = os.path.join(tmp, "b64_annotated.c")
subprocess.run([sys.executable, "-I", os.path.join(HERE, "../wp/annotate.py"), SRC, ann, "all"], check=True)
exes = {"pristine": build(SRC, "pristine"), "annotated": build(ann, "annotated"),
        "pristine-glibc-be64": build(SRC, "pristine_glibc",
                                     ["-DHAVE_BE64TOH", "-DENDIAN_INCLUDE_FILE=<endian.h>"])}


def expect(op, data):
    if op == "e":
        return base64.b64encode(data)
    try:
        out = base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError):
        return None
    return out if base64.b64encode(out) == data else None   # canonical only


cases = []
for v in [b"", b"f", b"fo", b"foo", b"foob", b"fooba", b"foobar"]:      # RFC 4648 section 10
    cases += [("e", v), ("d", base64.b64encode(v))]
cases += [("d", s) for s in [b"=", b"==", b"===", b"====", b"A===", b"AA=A", b"QR==", b"QUJ=",
                             b"Zm9v\n", b"Zm 9v", b"Zm9v====", b"Zg==Zg==", b"\x00\x00\x00\x00", b"\xff\xff\xff\xff"]]
rng = random.Random(1)
alpha = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
for _ in range(N):
    n = rng.choice([rng.randrange(0, 20), rng.randrange(0, 300)])
    data = bytes(rng.randrange(256) for _ in range(n))
    enc = base64.b64encode(data)
    cases.append(("e", data))
    cases.append(("d", enc))
    if enc:   # one corrupted character
        i = rng.randrange(len(enc)); b = bytearray(enc); b[i] = rng.choice(alpha + b"\x00-_.\x80\xff"); cases.append(("d", bytes(b)))
    cases.append(("d", bytes(rng.choice(alpha) for _ in range(rng.randrange(0, 13)))))

stream = b"".join(op.encode() + struct.pack("<I", len(d)) + d for op, d in cases)
outs = {k: subprocess.run([e], input=stream, capture_output=True, check=True).stdout for k, e in exes.items()}


def parse(buf):
    i, res = 0, []
    while i < len(buf):
        if buf[i:i + 1] == b"N": res.append(None); i += 1
        else:
            (L,) = struct.unpack("<Q", buf[i + 1:i + 9]); res.append(buf[i + 9:i + 9 + L]); i += 9 + L
    return res


res = {k: parse(v) for k, v in outs.items()}
bad = 0
for j, (op, d) in enumerate(cases):
    want = expect(op, d)
    got = {k: r[j] for k, r in res.items()}
    if any(g != want for g in got.values()):
        bad += 1
        if bad <= 10: print("MISMATCH", op, d[:40], "want", want and want[:40], {k: g and g[:40] for k, g in got.items()})
print(f"{len(cases)} cases x {len(exes)} builds: {bad} mismatches")
sys.exit(1 if bad else 0)
