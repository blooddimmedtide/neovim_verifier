"""Check that map_int.c's C text is the exact upstream text.
Usage: python3 -I check_strip.py <neovim checkout at 7b87ce8> [fixed]
With "fixed": checks map_realloc_fixed.c against the fork (verified_neovim branch
claude/project-thread-ik9odv, commit 9821c98).
Removes every /*@ ... */ from map_int.c and checks that each upstream function
below appears verbatim, and that its text has the pinned sha256."""
import hashlib, re, sys
HERE = __file__.rsplit("/", 1)[0]
SHA = {  # upstream 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
    "mh_realloc": "de94387ec2d481d9375fac53d9287405ca88adcd6780f0f3b87a6182895de816",
    "mh_clear": "a6a47a00281c9d83972aa6dff91e394a063833a57be010bf5dd405dfbb73c749",
    "KEY_NAME(mh_find_bucket_)": "f413064338422ea667e0219c5c090ba4cf051e5f40396c13feb875758c4473b7",
    "KEY_NAME(mh_get_)": "04ecba273bae24acc16201dbf71b0d8368ca29d4e29caa66311481734e3d8509",
    "KEY_NAME(mh_rehash_)": "d0d9bf460e1740849ababa51256aa5ed37fd8c22f51442f04c97b82a623e5600",
    "MAP_NAME(map_ref_)": "1ff27a97c1866480ac523aca26804860a941011fa19e039c7db0b54087a60ef3",
}
PIECES = [("src/nvim/map.c", "mh_realloc"), ("src/nvim/map.c", "mh_clear"),
          ("src/nvim/map_key_impl.c.h", "KEY_NAME(mh_find_bucket_)"),
          ("src/nvim/map_key_impl.c.h", "KEY_NAME(mh_get_)"),
          ("src/nvim/map_key_impl.c.h", "KEY_NAME(mh_rehash_)"),
          ("src/nvim/map_value_impl.c.h", "MAP_NAME(map_ref_)")]
tree = sys.argv[1]
src_file = "map_int.c"
if len(sys.argv) > 2 and sys.argv[2] == "fixed":
    SHA = {"mh_realloc": "93c1b14d251e4465d35851578fe5850677972712f6596202081dd1a4ade4c6e3"}
    PIECES = [("src/nvim/map.c", "mh_realloc")]
    src_file = "map_realloc_fixed.c"
ann = open(f"{HERE}/{src_file}").read()
stripped = re.sub(r"[ \t]*/\*@.*?\*/[ \t]*\n?", "", ann, flags=re.S)
stripped = re.sub(r"/\*@.*?\*/", "", stripped, flags=re.S)
ok = True
for path, name in PIECES:
    lines = open(f"{tree}/{path}").read().split("\n")
    s = [i for i, l in enumerate(lines) if not l.startswith((" ", "/", "#")) and (name + "(") in l]
    if len(s) != 1:
        sys.exit(f"{name}: expected one definition, found {len(s)}")
    e = s[0]
    while lines[e] != "}":
        e += 1
    text = "\n".join(lines[s[0]:e + 1])
    h = hashlib.sha256(text.encode()).hexdigest()
    found = text in stripped and SHA.get(name) == h
    ok &= found
    print(f"{name}: {'verbatim' if found else 'MISMATCH'} sha256 {h}")
sys.exit(0 if ok else 1)
