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

Differential test (`run_difftest.sh`, gcc -O2, signed and unsigned char; exhaustive over all
1-3 byte inputs, 20M random 4-6 byte inputs): fixed fork 0 mismatches; upstream 95 mismatches,
all overlong forms in utf_safe_read_char_adv (the finding).
Planted bugs (`mutants.py`, self-written, NOT the independent review): 8/8 caught.

Not done (deadline 2026-11-09 09:00 UTC): independent adversarial review + its mutants, CI,
vpipe.toml target entry.

## mbyte.c functions still unverified (79 of 90, after rounds 1 and 2)

enc_canon_search enc_canon_props bomb_size remove_bom mb_get_class mb_get_class_tab prop_is_emojilike utf_char2cells ptr2cells utf_ptr2cells mb_string2cells mb_string2cells_len mb_ptr2char_adv utf_iscomposing_first utf_composinglike utf_iscomposing utfc_ptr2schar utfc_ptrlen2schar schar_from_buf_first utfc_ptr2len utfc_ptr2len_len utf_iscomposing_legacy utf_isalnum utf_printable intable utf_printable utf_class utf_class_tab utf_ambiguous_width utf_fold mb_toupper mb_islower mb_tolower mb_isupper mb_isalpha utf_strnicmp utf8_to_utf16 utf16_to_utf8 mb_utflen mb_utf_index_to_bytes mb_strnicmp mb_stricmp show_utf8 always_break always_break_two utf_head_off utf_ClusterInfo_impl utf_eat_space utf_allow_break_before utf_allow_break_after utf_allow_break mb_copy_char mb_off_next utf_find_illegal utf_valid_string mb_adjust_cursor mb_check_adjust_col mb_prevptr mb_charlen mb_charlen_len mb_unescape enc_skip enc_canonize enc_alias_search enc_locale my_iconv_open iconv_string f_iconv convert_setup convert_setup_ext string_convert string_convert_ext cw_value tv_nr_compare f_setcellwidths f_getcellwidths f_charclass get_encoding_name mb_strcmp_ic 
