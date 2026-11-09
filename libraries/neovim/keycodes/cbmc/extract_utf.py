"""Write the verbatim utf_char2bytes (sha256 pinned, same pin as ../../mbyte/cbmc) to utf.c."""
import hashlib, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "tools"))
from extract_c import find
lines = open(f"{sys.argv[1]}/src/nvim/mbyte.c").read().split("\n")
s, e = find(lines, "utf_char2bytes")
piece = "\n".join(lines[s:e + 1])
if hashlib.sha256(piece.encode()).hexdigest() != "912fa872a6f92cf89173e88127394ac878b206ae12ef9d599b1134aeb1513617":
    sys.exit("utf_char2bytes changed upstream")
open(sys.argv[2], "w").write(piece + "\n")
