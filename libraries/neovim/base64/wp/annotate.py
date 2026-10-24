"""Insert the ACSL proof annotations into a pristine copy of base64.c.

Usage: python3 -I annotate.py <upstream base64.c> <output .c>
Each insertion is keyed on an exact line of upstream code. If upstream
changes so an anchor no longer matches exactly once, this stops with an
error, which is the signal that the proof needs a look.
"""
import subprocess, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
def lemmas(part):
    return subprocess.run([sys.executable, "-I", os.path.join(HERE, "lemmas.py"), "--acsl", part],
                          check=True, capture_output=True, text=True).stdout

ENC_LOGIC = r'''
/*@ // ---- RFC 4648 Base64, as a mathematical spec ----
    // Byte i of the input, with zero bytes past the end.
    logic integer byte_at(uint8_t *s, integer n, integer i) = (0 <= i < n) ? s[i] : 0;
    // 24-bit group g (input bytes 3g, 3g+1, 3g+2).
    logic integer grp(uint8_t *s, integer n, integer g) =
      byte_at(s, n, 3 * g) * 65536 + byte_at(s, n, 3 * g + 1) * 256 + byte_at(s, n, 3 * g + 2);
    // The i-th 6-bit value of the zero-padded input.
    logic integer sextet(uint8_t *s, integer n, integer i) =
      (i % 4 == 0) ? grp(s, n, i / 4) / 262144 :
      (i % 4 == 1) ? (grp(s, n, i / 4) / 4096) % 64 :
      (i % 4 == 2) ? (grp(s, n, i / 4) / 64) % 64 :
                     grp(s, n, i / 4) % 64;
    logic integer enc_len(integer n) = (n + 2) / 3 * 4;
    // Number of output characters that carry data; the rest are '='.
    logic integer data_len(integer n) = (8 * n + 5) / 6;
    // The RFC 4648 alphabet, written out here so the spec does not depend on
    // the code's own table: A-Z, a-z, 0-9, '+', '/'.
    logic integer rfc_char(integer k) =
      k < 26 ? 65 + k : k < 52 ? 71 + k : k < 62 ? k - 4 : k == 62 ? 43 : 47;
    logic integer enc_char(uint8_t *s, integer n, integer i) =
      i < data_len(n) ? rfc_char(sextet(s, n, i)) : '=';
    // Big-endian value of 8 (or 4) bytes starting at s.
    logic integer be64(uint8_t *s) =
      s[0] * 72057594037927936 + s[1] * 281474976710656 + s[2] * 1099511627776 +
      s[3] * 4294967296 + s[4] * 16777216 + s[5] * 65536 + s[6] * 256 + s[7];
    logic integer be32(uint8_t *s) = s[0] * 16777216 + s[1] * 65536 + s[2] * 256 + s[3];
*/
'''

# Each sextet is first derived from the logic value be64/be32 (small terms for
# the provers), then carried over to the C value bits_be by the load assert.
SEXT_C = ["({g} / 262144)", "(({g} / 4096) % 64)", "(({g} / 64) % 64)", "({g} % 64)"]
BYTES64 = "bytes_be64(" + ", ".join(f"s[src_i + {j}]" for j in range(8)) + ")"
BYTES32 = "bytes_be32(" + ", ".join(f"s[src_i + {j}]" for j in range(4)) + ")"
GRP = lambda o: f"s[src_i + {o}] * 65536 + s[src_i + {o + 1}] * 256 + s[src_i + {o + 2}]"
# Small steps the provers take one at a time: where the groups come from, the
# byte expansion of be64/be32, and each sextet in terms of its group.
FAST64_HELP = "\n".join([
    "    //@ assert src_i + 8 <= src_len && out_i % 8 == 0 && out_i / 4 * 3 == src_i;",
    "    //@ assert room: out_i + 8 <= out_len;",
    "    //@ assert (out_i + 4) % 4 == 0 && (out_i + 5) % 4 == 1 && (out_i + 6) % 4 == 2 && (out_i + 7) % 4 == 3;",
    "    //@ assert (out_i + 4) / 4 == out_i / 4 + 1 && (out_i + 5) / 4 == out_i / 4 + 1;",
    "    //@ assert (out_i + 6) / 4 == out_i / 4 + 1 && (out_i + 7) / 4 == out_i / 4 + 1;",
    f"    //@ assert g0: grp(s, src_len, out_i / 4) == {GRP(0)};",
    f"    //@ assert g1: grp(s, src_len, out_i / 4 + 1) == {GRP(3)};",
    f"    //@ assert be: be64(s + src_i) == {BYTES64};",
] + [f"    //@ assert sextet(s, src_len, out_i + {m}) == " + SEXT_C[m % 4].format(g=f"grp(s, src_len, out_i / 4 + {m // 4})") + ";"
     for m in range(8)])
FAST32_HELP = "\n".join([
    "    //@ assert src_i + 4 <= src_len && out_i % 4 == 0 && out_i / 4 * 3 == src_i;",
    "    //@ assert room: out_i + 4 <= out_len;",
    f"    //@ assert g0: grp(s, src_len, out_i / 4) == {GRP(0)};",
    f"    //@ assert be: be32(s + src_i) == {BYTES32};",
] + [f"    //@ assert sextet(s, src_len, out_i + {m}) == " + SEXT_C[m].format(g="grp(s, src_len, out_i / 4)") + ";"
     for m in range(4)])
FAST64_HELP += "\n" + "\n".join(
    f"    //@ assert ((({BYTES64}) >> {58 - 6 * m}) & 0x3F) == " + SEXT_C[m % 4].format(g=f"({GRP(3 * (m // 4))})") + ";"
    for m in range(8))
FAST32_HELP += "\n" + "\n".join(
    f"    //@ assert ((({BYTES32}) >> {26 - 6 * m}) & 0x3F) == " + SEXT_C[m].format(g=f"({GRP(0)})") + ";"
    for m in range(4))
FAST64_ASSERTS = FAST64_HELP + "\n" + "\n".join(
    f"    //@ assert ((be64(s + src_i) >> {58 - 6 * m}) & 0x3F) == sextet(s, src_len, out_i + {m});"
    for m in range(8)) + "\n" + "\n".join(
    f"    //@ assert ((bits_be >> {58 - 6 * m}) & 0x3F) == sextet(s, src_len, out_i + {m});"
    for m in range(8))
FAST32_ASSERTS = FAST32_HELP + "\n" + "\n".join(
    f"    //@ assert ((be32(s + src_i) >> {26 - 6 * m}) & 0x3F) == sextet(s, src_len, out_i + {m});"
    for m in range(4)) + "\n" + "\n".join(
    f"    //@ assert ((bits_be >> {26 - 6 * m}) & 0x3F) == sextet(s, src_len, out_i + {m});"
    for m in range(4))

INSERTS = [
    # (anchor line, 'before' | 'after', text)
    ("static inline uint64_t vim_htobe64(uint64_t host_64bits)", "before",
     "/*@ assigns \\nothing; */"),
    ("static inline uint32_t vim_htobe32(uint32_t host_32bits)", "before",
     "/*@ assigns \\nothing; */"),
    ("char *base64_encode(const char *src, size_t src_len)", "before", r'''/*@ requires src_len <= 0x3fffffffffffffff;  // 4 EiB; keeps out_len + 1 from overflowing
    requires \valid_read((uint8_t *)src + (0 .. src_len - 1));
    requires 0 <= vp_live < 2147483647;
    ensures allocation: vp_live == \old(vp_live) + 1 && (char *)vp_last == \result;
    ensures \valid(\result + (0 .. enc_len(src_len)));
    ensures encodes: \forall integer i; 0 <= i < enc_len(src_len) ==>
              \result[i] == enc_char((uint8_t *)src, src_len, i);
    ensures terminated: \result[enc_len(src_len)] == 0;
*/'''),
    ("  for (; src_i + 7 < src_len; src_i += 6) {", "before", r'''  /*@ loop invariant 0 <= src_i <= src_len && src_i % 6 == 0;
      loop invariant out_i == src_i / 3 * 4;
      loop invariant \forall integer k; 0 <= k < out_i ==>
                       dest[k] == alphabet[sextet(s, src_len, k)];
      loop assigns src_i, out_i, dest[0 .. out_len - 1];
      loop variant src_len - src_i;
  */'''),
    ("      | ((uint64_t)s[src_i + 6] << 8) | (uint64_t)s[src_i + 7];", "after",
     "    //@ assert load64: bits_be == be64(s + src_i);\n" + FAST64_ASSERTS),
    ("  for (; src_i + 3 < src_len; src_i += 3) {", "before", r'''  /*@ loop invariant 0 <= src_i <= src_len && src_i % 3 == 0;
      loop invariant out_i == src_i / 3 * 4;
      loop invariant \forall integer k; 0 <= k < out_i ==>
                       dest[k] == alphabet[sextet(s, src_len, k)];
      loop assigns src_i, out_i, dest[0 .. out_len - 1];
      loop variant src_len - src_i;
  */'''),
    ("      | ((uint32_t)s[src_i + 2] << 8) | (uint32_t)s[src_i + 3];", "after",
     "    //@ assert load32: bits_be == be32(s + src_i);\n" + FAST32_ASSERTS),
    (("  if (src_i + 2 < src_len) {", 0), "after", r'''    //@ assert out_i % 4 == 0 && out_i / 4 * 3 == src_i && src_i + 3 == src_len;
    //@ assert grp(s, src_len, out_i / 4) == s[src_i] * 65536 + s[src_i + 1] * 256 + s[src_i + 2];
    //@ assert (out_i + 1) % 4 == 1 && (out_i + 2) % 4 == 2 && (out_i + 3) % 4 == 3;
    //@ assert (out_i + 1) / 4 == out_i / 4 && (out_i + 2) / 4 == out_i / 4 && (out_i + 3) / 4 == out_i / 4;
    //@ assert sextet(s, src_len, out_i + 1) == (grp(s, src_len, out_i / 4) / 4096) % 64;
    //@ assert sextet(s, src_len, out_i + 2) == (grp(s, src_len, out_i / 4) / 64) % 64;
    //@ assert (s[src_i] >> 2) == s[src_i] / 4 && (s[src_i] & 0x3) == s[src_i] % 4;
    //@ assert (s[src_i + 1] >> 4) == s[src_i + 1] / 16 && (s[src_i + 1] & 0xF) == s[src_i + 1] % 16;
    //@ assert (s[src_i + 2] >> 6) == s[src_i + 2] / 64;
    //@ assert sextet(s, src_len, out_i) == s[src_i] / 4;
    //@ assert sextet(s, src_len, out_i + 1) == (s[src_i] % 4) * 16 + s[src_i + 1] / 16;
    //@ assert (s[src_i] >> 2) == sextet(s, src_len, out_i);
    //@ assert (((s[src_i] & 0x3) << 4) | (s[src_i + 1] >> 4)) == sextet(s, src_len, out_i + 1);
    //@ assert sextet(s, src_len, out_i + 2) == (s[src_i + 1] % 16) * 4 + s[src_i + 2] / 64;
    //@ assert (((s[src_i + 1] & 0xF) << 2) | (s[src_i + 2] >> 6)) == sextet(s, src_len, out_i + 2);
    //@ assert sextet(s, src_len, out_i + 3) == s[src_i + 2] % 64;
    //@ assert (s[src_i + 2] & 0x3F) == sextet(s, src_len, out_i + 3);'''),
    (("  } else if (src_i + 1 < src_len) {", 0), "after", r'''    //@ assert out_i % 4 == 0 && out_i / 4 * 3 == src_i && src_i + 2 == src_len;
    //@ assert grp(s, src_len, out_i / 4) == s[src_i] * 65536 + s[src_i + 1] * 256;
    //@ assert (out_i + 1) % 4 == 1 && (out_i + 2) % 4 == 2 && (out_i + 3) % 4 == 3;
    //@ assert (out_i + 1) / 4 == out_i / 4 && (out_i + 2) / 4 == out_i / 4 && (out_i + 3) / 4 == out_i / 4;
    //@ assert sextet(s, src_len, out_i + 1) == (grp(s, src_len, out_i / 4) / 4096) % 64;
    //@ assert sextet(s, src_len, out_i + 2) == (grp(s, src_len, out_i / 4) / 64) % 64;
    //@ assert (s[src_i] >> 2) == s[src_i] / 4 && (s[src_i] & 0x3) == s[src_i] % 4;
    //@ assert (s[src_i + 1] >> 4) == s[src_i + 1] / 16 && (s[src_i + 1] & 0xF) == s[src_i + 1] % 16;
    //@ assert sextet(s, src_len, out_i) == s[src_i] / 4;
    //@ assert sextet(s, src_len, out_i + 1) == (s[src_i] % 4) * 16 + s[src_i + 1] / 16;
    //@ assert (s[src_i] >> 2) == sextet(s, src_len, out_i);
    //@ assert (((s[src_i] & 0x3) << 4) | (s[src_i + 1] >> 4)) == sextet(s, src_len, out_i + 1);
    //@ assert sextet(s, src_len, out_i + 2) == (s[src_i + 1] % 16) * 4;
    //@ assert ((s[src_i + 1] & 0xF) << 2) == sextet(s, src_len, out_i + 2);'''),
    (("  } else if (src_i < src_len) {", 0), "after", r'''    //@ assert out_i % 4 == 0 && out_i / 4 * 3 == src_i && src_i + 1 == src_len;
    //@ assert grp(s, src_len, out_i / 4) == s[src_i] * 65536;
    //@ assert (s[src_i] >> 2) == s[src_i] / 4 && (s[src_i] & 0x3) == s[src_i] % 4;
    //@ assert sextet(s, src_len, out_i) == s[src_i] / 4;
    //@ assert sextet(s, src_len, out_i + 1) == (s[src_i] % 4) * 16;
    //@ assert (s[src_i] >> 2) == sextet(s, src_len, out_i);
    //@ assert ((s[src_i] & 0x3) << 4) == sextet(s, src_len, out_i + 1);'''),
    ("    out_i += 4;", "before",
     "    //@ assert dest[out_i + 0] == alphabet[sextet(s, src_len, out_i + 0)];\n    //@ assert dest[out_i + 1] == alphabet[sextet(s, src_len, out_i + 1)];\n    //@ assert dest[out_i + 2] == alphabet[sextet(s, src_len, out_i + 2)];\n    //@ assert dest[out_i + 3] == alphabet[sextet(s, src_len, out_i + 3)];\n    //@ assert \\forall integer k; 0 <= k < out_i + 4 ==> dest[k] == alphabet[sextet(s, src_len, k)];"),
    ("    out_i += 3;", "before",
     "    //@ assert dest[out_i + 0] == alphabet[sextet(s, src_len, out_i + 0)];\n    //@ assert dest[out_i + 1] == alphabet[sextet(s, src_len, out_i + 1)];\n    //@ assert dest[out_i + 2] == alphabet[sextet(s, src_len, out_i + 2)];\n    //@ assert \\forall integer k; 0 <= k < out_i + 3 ==> dest[k] == alphabet[sextet(s, src_len, k)];"),
    ("    out_i += 2;", "before",
     "    //@ assert dest[out_i + 0] == alphabet[sextet(s, src_len, out_i + 0)];\n    //@ assert dest[out_i + 1] == alphabet[sextet(s, src_len, out_i + 1)];\n    //@ assert \\forall integer k; 0 <= k < out_i + 2 ==> dest[k] == alphabet[sextet(s, src_len, k)];"),
    ("    out_i += 4;", "after",
     "    //@ assert \\forall integer k; 0 <= k < out_i ==> dest[k] == alphabet[sextet(s, src_len, k)];\n    //@ assert out_i == data_len(src_len);"),
    ("    out_i += 3;", "after",
     "    //@ assert \\forall integer k; 0 <= k < out_i ==> dest[k] == alphabet[sextet(s, src_len, k)];\n    //@ assert out_i == data_len(src_len);"),
    ("    out_i += 2;", "after",
     "    //@ assert \\forall integer k; 0 <= k < out_i ==> dest[k] == alphabet[sextet(s, src_len, k)];\n    //@ assert out_i == data_len(src_len);"),
    ("  for (; out_i < out_len; out_i++) {", "before", r'''  /*@ loop invariant data_len(src_len) <= out_i <= out_len;
      loop invariant \forall integer k; 0 <= k < data_len(src_len) ==>
                       dest[k] == alphabet[sextet(s, src_len, k)];
      loop invariant \forall integer k; data_len(src_len) <= k < out_i ==> dest[k] == '=';
      loop assigns out_i, dest[0 .. out_len - 1];
      loop variant out_len - out_i;
  */'''),
    ("  dest[out_len] = NUL;", "before",
     "  //@ assert enc_table: \\forall integer k; 0 <= k < 64 ==> alphabet[k] == rfc_char(k);\n"
     "  //@ assert \\forall integer k; 0 <= k < out_len ==> dest[k] == enc_char(s, src_len, k);"),
    (("  if (src_i + 2 < src_len) {", 0), "before",
     "  //@ assert src_len - src_i <= 3 && src_i % 3 == 0 && out_i == src_i / 3 * 4;\n"
     "  //@ assert src_i == src_len ==> out_i == data_len(src_len);"),
]


DEC_SPEC = r"""
/*@ // ---- Decoding spec ----
    // Position of character c in the RFC 4648 alphabet, or -1 if c is not in it.
    // Written out here so the spec does not depend on the code's own table.
    logic integer rfc_index(integer c) =
      65 <= c <= 90 ? c - 65 : 97 <= c <= 122 ? c - 71 : 48 <= c <= 57 ? c + 4 :
      c == 43 ? 62 : c == 47 ? 63 : -1;
    // 6-bit value of character i ('=' counts as 0; non-alphabet chars are never used).
    logic integer V(uint8_t *s, integer i) = s[i] == 61 ? 0 : rfc_index(s[i]);
    // Output byte j, from the 4 characters of its group (RFC 4648 section 4).
    logic integer dec_byte(uint8_t *s, integer j) =
      (j % 3 == 0) ? V(s, 4 * (j / 3)) * 4 + V(s, 4 * (j / 3) + 1) / 16 :
      (j % 3 == 1) ? (V(s, 4 * (j / 3) + 1) % 16) * 16 + V(s, 4 * (j / 3) + 2) / 4 :
                     (V(s, 4 * (j / 3) + 2) % 4) * 64 + V(s, 4 * (j / 3) + 3);
    // Number of trailing '=' (0, 1 or 2) as the decoder counts them.
    logic integer pad(uint8_t *s, integer n) =
      (n < 1 || s[n - 1] != 61) ? 0 : (n >= 2 && s[n - 2] == 61) ? 2 : 1;
    // How many of the last two characters are '=' (what the code subtracts).
    logic integer eqs(uint8_t *s, integer n) =
      (n >= 1 && s[n - 1] == 61 ? 1 : 0) + (n >= 2 && s[n - 2] == 61 ? 1 : 0);
    // Canonical padded Base64: length a multiple of 4, alphabet characters
    // followed by 0-2 '=', and unused low bits of the last character zero.
    predicate valid_b64(uint8_t *s, integer n) =
      n % 4 == 0 &&
      (\forall integer i; 0 <= i < n - pad(s, n) ==> rfc_index(s[i]) >= 0) &&
      (pad(s, n) == 1 ==> V(s, n - 2) % 4 == 0) &&
      (pad(s, n) == 2 ==> V(s, n - 3) % 16 == 0);
*/
"""


def dec_inserts(variant):
    up = variant == "upstream"
    notfound = "-1" if up else "SIZE_MAX"
    bound = "    requires src_len <= 0x7fffffff;  // see neovim issue: (int)src_i wraps past 2 GiB\n" if up else ""
    pad_loop = ("    for (; (size_t)leftover_i < src_len; leftover_i++) {" if up
                else "    for (; leftover_i < src_len; leftover_i++) {")
    pad_if = "  if (leftover_i > -1) {" if up else "  if (leftover_i != SIZE_MAX) {"
    return [
        ("/// Decode a Base64 encoded string.", "before", DEC_SPEC),
        ("char *base64_decode(const char *src, size_t src_len, size_t *out_lenp)", "before",
         "/*@\n" + bound + r"""    requires \valid_read((uint8_t *)src + (0 .. src_len - 1));
    requires \valid(out_lenp);
    requires \separated(out_lenp, (uint8_t *)src + (0 .. src_len - 1));
    requires 0 <= vp_live < 2147483647;
    ensures allocation: \result != \null ==> vp_live == \old(vp_live) + 1 && (char *)vp_last == \result;
    ensures no_leak: \result == \null ==> vp_live == \old(vp_live);
    ensures reject: \result == \null ==> *out_lenp == 0;
    ensures accepts_only_valid: \result != \null ==> valid_b64((uint8_t *)src, src_len);
    ensures accepts_all_valid: valid_b64((uint8_t *)src, src_len) ==> \result != \null;
    ensures length: \result != \null ==> *out_lenp == src_len / 4 * 3 - pad((uint8_t *)src, src_len);
    ensures valid_buffer: \result != \null ==> \valid(\result + (0 .. *out_lenp - 1));
    ensures bytes: \result != \null ==> \forall integer j; 0 <= j < *out_lenp ==>
              (uint8_t)\result[j] == dec_byte((uint8_t *)src, j);
*/"""),
        ("  for (; src_i < src_len; src_i++) {", "before", r"""  /*@ loop invariant 0 <= src_i <= src_len;
      loop invariant out_i * 8 + acc_len == 6 * src_i;
      loop invariant acc_len == (src_i % 4 == 0 ? 0 : src_i % 4 == 1 ? 6 : src_i % 4 == 2 ? 4 : 2);
      loop invariant 0 <= acc <= 4095;
      loop invariant src_i % 4 == 1 ==> acc % 64 == V(s, src_i - 1);
      loop invariant src_i % 4 == 2 ==> acc % 16 == V(s, src_i - 1) % 16;
      loop invariant src_i % 4 == 3 ==> acc % 4 == V(s, src_i - 1) % 4;
      loop invariant \forall integer k; 0 <= k < src_i ==> char_to_index[s[k]] != 0;
      loop invariant \forall integer j; 0 <= j < out_i ==> (uint8_t)dest[j] == dec_byte(s, j);
      loop invariant leftover_i == """ + notfound + r""";
      loop invariant alloc: vp_last == (void *)dest && vp_live == \at(vp_live, Pre) + 1;
      loop invariant src_len % 4 == 0;
      loop invariant out_len == src_len / 4 * 3 - eqs(s, src_len);
      loop invariant out_i <= out_len;
      loop assigns src_i, acc, acc_len, out_i, leftover_i, dest[0 .. out_len - 1];
      loop variant src_len - src_i;
  */"""),
        (("  const uint8_t *s = (const uint8_t *)src;", 1), "after",
         "  //@ assert out_len == src_len / 4 * 3 - eqs(s, src_len);"),
        ("    const uint8_t d = char_to_index[c];", "after",
         "    //@ assert d <= 64;\n    //@ assert d != 0 ==> c != 61;"),
        ("    acc = ((acc << 6) & 0xFFF) + (d - 1);", "before",
         "    //@ assert (acc << 6) == acc * 64;\n"
         "    //@ assert ((acc << 6) & 0xFFF) == (acc % 64) * 64;\n"
         "    //@ assert V(s, src_i) == d - 1;"),
        ("    acc_len += 6;", "before", r"""    //@ assert src_i % 4 == 0 ==> acc % 64 == V(s, src_i);
    //@ assert src_i % 4 == 1 ==> acc == V(s, src_i - 1) * 64 + V(s, src_i);
    //@ assert src_i % 4 == 2 ==> acc % 1024 == (V(s, src_i - 1) % 16) * 64 + V(s, src_i);
    //@ assert src_i % 4 == 3 ==> acc % 256 == (V(s, src_i - 1) % 4) * 64 + V(s, src_i);"""),
        ("      dest[out_i] = (char)(acc >> acc_len);", "before", r"""      //@ assert acc_len == 0 ==> (acc >> acc_len) == acc;
      //@ assert acc_len == 2 ==> (acc >> acc_len) == acc / 4;
      //@ assert acc_len == 4 ==> (acc >> acc_len) == acc / 16;
      //@ assert src_i % 4 == 1 ==> (acc >> acc_len) % 256 == V(s, src_i - 1) * 4 + V(s, src_i) / 16;
      //@ assert src_i % 4 == 2 ==> (acc >> acc_len) % 256 == (V(s, src_i - 1) % 16) * 16 + V(s, src_i) / 4;
      //@ assert src_i % 4 == 3 ==> (acc >> acc_len) % 256 == (V(s, src_i - 1) % 4) * 64 + V(s, src_i);      //@ assert src_len >= 1 && s[src_len - 1] == 61 ==> src_i + 1 <= src_len - 1;
      //@ assert src_len >= 2 && s[src_len - 2] == 61 ==> src_i + 1 <= src_len - 2;
      //@ assert out_i + 1 <= out_len;
      //@ assert out_i % 3 == (src_i % 4) - 1 && out_i / 3 == src_i / 4;
      //@ assert src_i % 4 == 1 ==> dec_byte(s, out_i) == V(s, src_i - 1) * 4 + V(s, src_i) / 16;
      //@ assert src_i % 4 == 2 ==> dec_byte(s, out_i) == (V(s, src_i - 1) % 16) * 16 + V(s, src_i) / 4;
      //@ assert src_i % 4 == 3 ==> dec_byte(s, out_i) == (V(s, src_i - 1) % 4) * 64 + V(s, src_i);
      //@ assert (acc >> acc_len) % 256 == dec_byte(s, out_i);
      //@ assert 0 <= (acc >> acc_len) <= 4095;"""),
        ("      out_i += 1;", "before",
         "      // int -> char is implementation-defined in C; WP models it as gcc and clang\n"
         "      // do (reduction modulo 2^8), which is listed in CLAIM.md.\n"
         "      //@ assert cast_mod256: (uint8_t)dest[out_i] == (acc >> acc_len) % 256;\n"
         "      //@ assert (uint8_t)dest[out_i] == dec_byte(s, out_i);"),
        ("  if (acc_len > 4 || ((acc & ((1 << acc_len) - 1)) != 0)) {", "before", r"""  //@ assert leftover_i == """ + notfound + r""" ==> src_i == src_len;
  //@ assert leftover_i != """ + notfound + r""" ==> leftover_i == src_i && src_i < src_len && s[src_i] == 61;
  //@ assert acc_len == 0 ==> (acc & ((1 << acc_len) - 1)) == 0;
  //@ assert acc_len == 2 ==> (acc & ((1 << acc_len) - 1)) == V(s, src_i - 1) % 4;
  //@ assert acc_len == 4 ==> (acc & ((1 << acc_len) - 1)) == V(s, src_i - 1) % 16;"""),
        (("    goto invalid;", 0), "before", "    //@ assert !valid_b64((uint8_t *)src, src_len);"),
        (("    goto invalid;", 1), "before", "    //@ assert !valid_b64(s, src_len);"),
        (("      goto invalid;", 0), "before", "      //@ assert !valid_b64(s, src_len);"),
        (("      goto invalid;", 1), "before", "      //@ assert !valid_b64(s, src_len);"),
        (("        goto invalid;", 0), "before", "        //@ assert !valid_b64(s, src_len);"),
        ("    xfree((void *)dest);", "before",
         "    //@ assert (void *)dest == vp_last && vp_live == \\at(vp_live, Pre) + 1;"),
        ("invalid:", "after", "  //@ assert not_valid: !valid_b64((uint8_t *)src, src_len);"),
        ("  *out_lenp = 0;", "after", "  //@ assert !valid_b64((uint8_t *)src, src_len);"),
        ("  *out_lenp = out_len;", "before", "  //@ assert valid_b64(s, src_len);\n  //@ assert out_len == src_len / 4 * 3 - pad(s, src_len);"),
        (pad_loop, "before", r"""    /*@ loop invariant src_i <= leftover_i <= src_len;
        loop invariant padding_chars == leftover_i - src_i;
        loop invariant alloc: vp_last == (void *)dest && vp_live == \at(vp_live, Pre) + 1;
        loop invariant \forall integer k; src_i <= k < leftover_i ==> s[k] == 61;
        loop assigns leftover_i, padding_chars;
        loop variant src_len - leftover_i;
    */"""),
    ]


def main(src, dst, part="all"):
    import importlib.util
    spec = importlib.util.spec_from_file_location("tool_patches", os.path.join(HERE, "tool_patches.py"))
    tp = importlib.util.module_from_spec(spec); spec.loader.exec_module(tp)
    text_in = tp.apply(open(src).read())
    if "  int leftover_i = -1;" in text_in:
        variant = "upstream"
    elif "  size_t leftover_i = SIZE_MAX;" in text_in:
        variant = "fixed"
    else:
        sys.exit("annotate.py: unknown base64_decode variant")
    print(f"annotate.py: {variant} decoder", file=sys.stderr)
    lines = text_in.split("\n")
    # 'enc' / 'dec' annotate one function only, so each WP run carries only the
    # logic and lemmas it needs (fewer axioms, faster and steadier proofs).
    inserts = [("/// Encode a string using Base64.", "before",
                lemmas(part) + (ENC_LOGIC if part != "dec" else ""))]
    if part != "dec":
        inserts += INSERTS
    if part != "enc":
        inserts += dec_inserts(variant)
    for anchor, where, text in inserts:
        # An anchor is a line, or (line, n) for the n-th of several equal lines.
        anchor, nth = (anchor, None) if isinstance(anchor, str) else anchor
        hits = [i for i, l in enumerate(lines) if l == anchor]
        if nth is not None:
            hits = hits[nth:nth + 1]
        if len(hits) != 1:
            sys.exit(f"annotate.py: anchor matched {len(hits)} times (want 1): {anchor!r}")
        i = hits[0] + (1 if where == "after" else 0)
        lines[i:i] = text.split("\n")
    open(dst, "w").write("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "all")
