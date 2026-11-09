"""Quick planted bugs for round 2 (self-written, not the independent review). Each must FAIL."""
import subprocess, sys
M = [
 ("h_charinfo_impl", "if ((uint32_t)len == 3) {", "if ((uint32_t)len == 4) {"),
 ("h_charinfo_impl", "if (EXPECT((uint8_t)(cur & 0xC0U) != 0x80U, false)) {", "if (EXPECT((uint8_t)(cur & 0x80U) != 0x80U, false)) {"),
 ("h_charinfo_impl", "-(0x80U + (0xC0U << 6)),", "-(0x80U + (0xC0U << 5)),"),
 ("h_cptr2char_adv", "  *pp += utf_ptr2len(*pp);\n  return c;\n}", "  *pp += utf_ptr2len(*pp) + 1;\n  return c;\n}"),
 ("h_safe_read", "  if (*n == 0) {  // end of buffer\n    return 0;", "  if (*n == 0) {  // end of buffer\n    return -1;"),
 ("h_safe_read", "    (*n)--;\n    return (uint8_t)(*(*s)++);", "    return (uint8_t)(*(*s)++);"),
 ("h_safe_read", "  if (k <= *n) {", "  if (k <= *n + 1) {"),
 ("h_safe_read", "      *n -= k;\n      return c;", "      *n -= 1;\n      return c;"),
]
base = open(sys.argv[1]).read(); bad = 0
for i, (h, a, b) in enumerate(M):
    assert base.count(a) == 1, a
    open("/tmp/mut.c", "w").write(base.replace(a, b))
    r = subprocess.run(["cbmc", "harness.c", "-I", ".", "--function", h, '-DMBYTE_UTF8_C="/tmp/mut.c"', "--arch", "x86_64",
        "--no-malloc-may-fail", "--bounds-check", "--pointer-check", "--signed-overflow-check", "--undefined-shift-check",
        "--unwind", "10", "--unwinding-assertions"], capture_output=True, text=True)
    caught = "VERIFICATION FAILED" in r.stdout
    bad += not caught; print(i, h, "caught" if caught else "MISSED")
sys.exit(bad)
