"""Copy read_string verbatim from fileio.c (sha256 pinned) and insert its ACSL contract and
loop invariant. Usage: python3 -I annotate.py <neovim checkout> <out.c>"""
import hashlib, re, sys
WANT = "63b60365efd3d2ba41c5c8e564a8ffa0ac6ac8d870a704f7e2cb056749cc6a9a"
CONTRACT = """/*@ requires \\valid_read(fdata + (0 .. flen - 1)) && fpos <= flen && cnt < SIZE_MAX;
    behavior ok: assumes flen - fpos >= cnt;
      ensures \\valid(\\result + (0 .. cnt));
      ensures \\forall integer i; 0 <= i < cnt ==> \\result[i] == (char)fdata[\\old(fpos) + i];
      ensures \\result[cnt] == 0 && fpos == \\old(fpos) + cnt;
    behavior short: assumes flen - fpos < cnt;
      ensures \\result == \\null && fpos == flen;
    // no function-level assigns: WP cannot name the block allocated inside; the loop assigns
    // clause bounds writes to fpos and str[0 .. cnt - 1]
    complete behaviors; disjoint behaviors; */"""
LOOP = """  /*@ loop invariant 0 <= i <= cnt && fpos == \\at(fpos, Pre) + i && fpos <= flen;
      loop invariant \\valid(str + (0 .. cnt)) && str[cnt] == 0;
      loop invariant \\forall integer j; 0 <= j < i ==> str[j] == (char)fdata[\\at(fpos, Pre) + j];
      loop assigns i, fpos, str[0 .. cnt - 1];
      loop variant cnt - i; */"""
def main(tree, out):
    lines = open(f"{tree}/src/nvim/fileio.c").read().split("\n")
    s = [i for i, l in enumerate(lines) if re.match(r"^char \*read_string\(", l)][0]
    e = s
    while not lines[e].startswith("}"): e += 1
    piece = "\n".join(lines[s:e + 1])
    h = hashlib.sha256(piece.encode()).hexdigest()
    if h != WANT: sys.exit(f"annotate: read_string changed upstream: {h}")
    body = piece.split("\n")
    k = [i for i, l in enumerate(body) if l.startswith("  for (size_t i = 0; i < cnt; i++)")]
    assert len(k) == 1
    body.insert(k[0], LOOP)
    open(out, "w").write('#include <stdint.h>\n#include "model.h"\n' + CONTRACT + "\n" + "\n".join(body) + "\n")
if __name__ == "__main__": main(sys.argv[1], sys.argv[2])
