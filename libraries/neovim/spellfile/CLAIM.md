---
entry: neovim/src/nvim/spellfile.c (.spl reader helpers, untrusted spell-file input)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
fixed_fork: none (no bug found)
toolchain: CBMC 6.11.0 (nixpkgs); Frama-C 33.0 WP + Why3 1.8.2 + Z3 5.1.0 + CVC5 1.4.0 (pinned nixpkgs of tools/install.sh); python3
strength: candidate (all 4 functions)
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
| `read_cnt_string(fd, k, &cnt)`, k in {1, 2} | short count: NULL, SP_TRUNCERROR; count 0: NULL, 0; short body: NULL, SP_OTHERERROR, no leak; else a fresh NUL-terminated copy of the n bytes, cnt = n | candidate: every file length and count. `cbmc/harness_composed.c` runs the upstream count loop on read_string's WP-proved contract (`cbmc/read_string_contract.h`); files up to 70000 bytes > 2 + 65535 cover every count. Also proved directly, without the contract, for files up to 20 bytes |
| `read_string(fd, cnt)` (fileio.c, callee) | enough bytes left: a valid (cnt+1)-byte block holding the next cnt bytes and a NUL, position +cnt; else NULL, position at end | candidate: Frama-C WP for every cnt (`wp/run_wp.sh`, 33/33 goals, 11/11 smoke tests, no admits). WP has no \fresh/\freeable, so freshness, the free on the error path and leaks are covered only by the CBMC runs (files <= 20 bytes) |

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
| Planted bugs (`cbmc/mutants.txt`) | 9/9: 8 by the 20-byte runs, `cnt_shift7` only by the composed every-length run |
| WP read_string (`wp/run_wp.sh`) | 33/33 goals, smoke tests 11/11 |
| WP planted bugs (`wp/mutants.txt`) | 4/4 caught |
| Differential test, independent review | not done (deadline 2026-11-09 09:00 UTC) |

## Still unverified in spellfile.c

Everything else: spell_load_file, tree_count_words, suggest_load_files, read_charflags_section,
read_prefcond_section, read_rep_section, read_sal_section, read_words_section, read_sofo_section,
read_compound, set_sofo, set_sal_first, mb_str2wide, spell_read_tree, read_tree_node, and all
writer / .aff / .dic functions (77 of 81 inventory functions open; read_string is in fileio.c).
