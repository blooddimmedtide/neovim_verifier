# mbyte.c UTF-8 helpers, round 2 (CBMC 6.4.1)

Proved for every input, x86_64, signed and unsigned char, `--bounds-check --pointer-check
--signed-overflow-check --undefined-shift-check --unwinding-assertions`, exact-size objects.
References: `../cbmc/spec.h` (RFC 2279 1-6 byte form / RFC 3629), not Neovim's tables.
Code: verbatim upstream text, sha256-pinned in `pins.txt` (shared pieces match round 1 pins).
Run: `bash run_cbmc.sh <neovim checkout>`.

| Function | Result | Property |
|---|---|---|
| utf_ptr2CharInfo_impl | proved (candidate) | with its caller's preconditions (NUL-terminated p, p[0] >= 0x80, len = utf8len_tab[p[0]]): value of a complete sequence, negative otherwise; never reads past NUL |
| mb_cptr2char_adv | proved (candidate) | returns utf_ptr2char meaning, advances by the sequence length (0 for "") |
| utf_safe_read_char_adv | upstream: memory safe, fails the spec on overlong forms; fixed: proved (fixed-candidate) | upstream returns -1 for an overlong sequence whose value equals its first byte, e.g. FC 80 80 80 83 BC or E0 83 A0; see ../../findings/safe-read-overlong.md. Fix: verified_neovim branch claude/project-thread-s2rcie (13c7bc1), full spec proved (build.py accepts the fixed piece by sha256) |

Preconditions used: the ones above for utf_ptr2CharInfo_impl (its NUL-terminated caller in mbyte.h
establishes them).

Upstream run: 8/10 harness runs proved (h_safe_read fails, both signednesses). Fixed fork: 10/10.

Not done (deadline 2026-11-09 09:00 UTC): differential test, adversarial review + mutants, CI.
