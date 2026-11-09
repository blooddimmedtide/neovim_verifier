"""Copy inmacro() verbatim from src/nvim/textobject.c and check its sha256 pin."""
import hashlib, re, sys
PINS = {"cea4385fc28b0f8d40dc4b9379c13492e714fca81210b31f6dc00247ca90e8d3": "upstream 7b87ce8",
        "d3f8ba6def03640862ead61049f75f7dc43028610fefbd979f1ec8b4b44d515f": "fixed f563ea4"}
src = open(sys.argv[1] + "/src/nvim/textobject.c").read()
m = re.search(r"^static bool inmacro\(char \*opt, const char \*s\)\n\{.*?^\}\n", src, re.S | re.M)
if not m:
    sys.exit("inmacro not found")
body = m.group(0)
h = hashlib.sha256(body.encode()).hexdigest()
if h not in PINS:
    sys.exit(f"inmacro sha256 {h} is not a reviewed version")
open(sys.argv[2], "w").write("#include <stdbool.h>\n#define NUL '\\000'\n" + body)
print(h)
