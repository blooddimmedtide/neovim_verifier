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
| utf_safe_read_char_adv | FAILS the spec on overlong forms only | memory safe (never reads past n). Returns -1 for an overlong sequence whose value equals its first byte, e.g. FC 80 80 80 83 BC (value 0xFC) or E0 83 A0 (0xE0); see ../../findings/safe-read-overlong.md. No fix proved yet |

Preconditions used: the ones above for utf_ptr2CharInfo_impl (both callers in mbyte.h establish
them for the NUL-terminated case). Not yet checked: the `utf_ptr2CharInfo_len` caller with
size == 1 and a lone continuation byte (len 1 <= size, impl reads p[1] past size). Open question.

Not done (deadline 2026-11-09 09:00 UTC): differential test, adversarial review + mutants, CI.
