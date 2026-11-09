# Claim: src/nvim/fileio.c encoding helpers (partial)

Pinned source: blooddimmedtide/verified_neovim `7b87ce822e6fd45a4d9993599c2854afdb0dc4dd`, `src/nvim/fileio.c`.

## Proved (status `candidate`)

| Function | Tool | Property | Evidence |
|---|---|---|---|
| `check_for_bom` | CBMC 6.4.1, x86_64, signed and unsigned char | For every buffer of exactly `size` bytes (any `2 <= size <= INT_MAX`, every byte value) and every `flags` int: return value and `*lenp` equal the reference in `cbmc/spec.h`; no out-of-bounds read, no UB; the reported BOM length never exceeds `size`. | `cbmc/run_cbmc.sh`, `cbmc/difftest.c` (86,436 cases, gcc -O2 -fsigned-char, ASan+UBSan, 0 mismatches), 11/11 planted mutants caught (`cbmc/mutants.txt`) |

Body extracted verbatim by `cbmc/build.py`, sha256 pinned (`7f858059...64b7`).

### Reference (`cbmc/spec.h`)
Written from the Unicode BOM byte sequences (UTF-8 `EF BB BF`, UTF-16/UCS-2 BE `FE FF`, LE `FF FE`,
UCS-4 BE `00 00 FE FF`, LE `FF FE 00 00`) and the function's contract: return the encoding name the
BOM names, restricted by `flags` (`FIO_ALL` accepts all; otherwise only the named form). The reference
decides itself: no match gives NULL with `*lenp = 2`; `FF FE` with `FIO_UCS2|FIO_ENDIAN_L` is
"ucs-2le", otherwise "utf-16le"; `FE FF` with `FIO_UCS2` is "ucs-2", otherwise "utf-16".

### Precondition
`size >= 2`. Documented and enforced at the only caller (`readfile`: "no BOM detection in a short
file", `if (size < 2 ...) ccname = NULL`). The function always reads `p[0]` and `p[1]`, so a call
with `size < 2` would read out of bounds; no such call exists.

## Not yet verified (fileio.c encoding/byte helpers)
`get_fio_flags`, `need_conversion` (depend on `enc_canon_props` / `p_enc`), `next_fenc`,
`set_forced_fenc`, `readfile_charconvert`, `vim_fgets`, `read_string`, `put_bytes`,
`readfile_linenr`, and the conversion loops inside `readfile`. `get8ctime` was handled by the undo
thread. The rest of fileio.c (66 functions in inventory.tsv) is also open.

## Review
No independent adversarial review yet (stopped at the 2026-11-09 09:00 UTC deadline).

## Added: put_bytes, put_time (CBMC, `cbmc_put/`)
Models: `putc` and `fwrite` can each fail, and fwrite can write short, nondeterministically;
`time_to_bytes` is modelled from its memory.c contract (big-endian 8 bytes). That model has not
itself been proved against memory.c.
- `put_bytes` (`candidate`): for every `number` and `1 <= len <= 8`, it writes exactly the low
  `len` bytes, most significant first, and returns false exactly when a putc fails. Precondition
  `len <= 8` is not asserted by the function; every caller (spellfile.c) passes 1 to 4. Larger
  `len` would shift by 64 or more bits (UB).
- `put_time` (`fixed-candidate`): upstream FAILS its documented contract (FAIL on success, see
  findings/put-time-return.md). The fix on verified_neovim `fix-put-time-return` is proved.
No mutants or difftest for these two yet.
