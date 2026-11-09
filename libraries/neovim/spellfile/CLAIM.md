---
entry: neovim/src/nvim/spellfile.c (.spl reader helpers, untrusted spell-file input)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
fixed_fork: none (no bug found)
toolchain: CBMC 6.11.0 (nixpkgs), python3 for the verbatim extraction
strength: candidate (2 functions), bounded (2 functions; see below)
platform: x86_64, char signed and unsigned (both proved)
---

# Claim card: Neovim spellfile.c reader helpers

Run: `bash spellfile/cbmc/run_cbmc.sh <neovim checkout>`; planted bugs: `bash spellfile/cbmc/run_mutants.sh <neovim checkout>`.

Code under test is copied verbatim (sha256-pinned in `cbmc/reviewed.sha256`, `cbmc/build.py`),
including the `SPELL_READ_BYTES` / `SPELL_READ_NONNUL_BYTES` macros. The spec in
`cbmc/harness.c` is written from the .spl format (`runtime/doc/spell.txt`: counts are MSB-first
unsigned bytes) and the functions' comments. Checks on: bounds, pointer, signed and unsigned
overflow, undefined shift, memory leak, unwinding assertions. Every byte is nondeterministic.

| Function | Property | Strength |
|---|---|---|
| `spell_check_magic_string(fd)` | 0 iff the file starts with "VIMspell"; SP_TRUNCERROR when it holds fewer than 8 bytes; else SP_FORMERROR; consumes exactly min(len, 8) bytes | candidate: reads at most 8 bytes, so files up to 20 bytes cover every behaviour |
| `read_region_section(fd, lp, len)`, len >= 0 | len > 16: SP_FORMERROR, nothing read; fewer than len bytes: SP_TRUNCERROR; a NUL among them: SP_FORMERROR; else `sl_regions` = the bytes + NUL, returns 0. No write outside `sl_regions[17]` | candidate: reads at most 16 bytes |
| `read_cnt_string(fd, k, &cnt)`, k in {1, 2} | short count: NULL, SP_TRUNCERROR; count 0: NULL, 0; short body: NULL, SP_OTHERERROR, no leak; else a fresh NUL-terminated copy of the n bytes, cnt = n | **bounded**: file length <= 20 bytes, so bodies up to 18 bytes. Bodies up to 65535 bytes not covered: needs a WP loop invariant for `read_string` |
| `read_string(fd, cnt)` (fileio.c, callee) | as used by read_cnt_string | **bounded**, same reason |

## Assumptions (each documented)

- FILE model (`cbmc/model.h`): a regular file with no I/O error. `getc`/`fread`/`feof` follow
  C11 7.21. The SP_OTHERERROR path for a failing `fread` is therefore not exercised.
- `xmallocz` never returns NULL (Neovim exits on out-of-memory); `memchr` modelled from C11 7.24.5.1.
- `read_region_section` callers pass len >= 0 (spell_load_file rejects a negative `get4c` length).
- `(char)c` for c in 128..255 is implementation-defined; gcc wraps, which is what Neovim relies on.

## Spec notes

- `read_cnt_string` reports a body cut short by end of file as SP_OTHERERROR, not
  SP_TRUNCERROR (read_string does not say why it failed). The spell loader then gives a
  generic error instead of "E758: Truncated spell file". Not a memory-safety issue; recorded, not fixed.
- k = 4 is never used in spellfile.c; with k = 4 a count >= 2^31 would turn negative. Not reachable.

## Evidence

| Gate | Result |
|---|---|
| CBMC, 3 harnesses x 2 signednesses | 6/6 proved |
| Planted bugs (`cbmc/mutants.txt`) | 8/9 caught. `cnt_shift7` (count built with `<< 7`) survives: with a 20-byte file every 2-byte count >= 256 is a short body either way, so the bound hides it. This is why read_cnt_string stays **bounded**, not candidate |
| k = 1 run with 257-byte file (would cover every 1-byte count) | ran out of memory in this container; not done |
| Differential test, independent review | not done (deadline 2026-11-09 09:00 UTC) |

## Still unverified in spellfile.c

Everything else: spell_load_file, tree_count_words, suggest_load_files, read_charflags_section,
read_prefcond_section, read_rep_section, read_sal_section, read_words_section, read_sofo_section,
read_compound, set_sofo, set_sal_first, mb_str2wide, spell_read_tree, read_tree_node, and all
writer / .aff / .dic functions (77 of 81 inventory functions open).
