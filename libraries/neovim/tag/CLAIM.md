---
entry: neovim/src/nvim/tag.c (tags-file line parsing helpers)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
toolchain: CBMC 6.4.1 (.deb, see tools/install.sh)
strength: candidate (bounded)   # BOUNDED: strings up to N bytes; not yet a full proof
platform: x86_64, char signed and unsigned (both proved)
---

# Claim card: Neovim tag.c tag-line helpers (work in progress)

Run: `N=6 bash cbmc/run_cbmc.sh <neovim checkout at the pinned commit>`. All 8 runs
(4 harnesses x 2 char signednesses) report VERIFICATION SUCCESSFUL at N=6 (3.5 min).
Code is copied verbatim (`cbmc/build.py`, sha256 pinned per piece). Each string lives in an
object of exactly its size, so a read past it fails CBMC's pointer checks; all loops are fully
unwound (`--unwinding-assertions`).

## What is proved, for every NUL-terminated input of 1..N bytes (N = 6)

| Function | Property (reference in `cbmc/harness.c` / `spec.h`, index based) |
|---|---|
| `parse_tag_line(lbuf, tagp)` | OK iff the line has a TAB, a second TAB after it, and a byte other than NUL after the second TAB; tagname/tagname_end/fname/fname_end/command point exactly at those positions; no read past the NUL |
| `tag_strnicmp(s1, s2, len)` | returns the ASCII-uppercase-folded byte difference at the first differing position below len, 0 if none before a common NUL; any len up to N+1; no read past either NUL |
| `test_for_static(tagp)` | true iff some TAB at or after `tagp->command` is followed by `file:`; any command offset inside the string |
| `matching_line_len(lbuf)` | for the documented layout `<mtt><tag_fname>NUL<lbuf>NUL`, returns the offset of the final NUL (line length); no read past it |
| `vim_strchr` (strings.c, verbatim, dependency) | used only with ASCII c; its c >= 0x80 branch is proved unreachable (stub asserts false) |

## Update 08:55Z
- N=8 (unwind 11), both char types: parse_tag_line, tag_strnicmp, matching_line_len VERIFICATION SUCCESSFUL.
- test_for_static at N=8 failed because the harness let `command` point past an embedded NUL (outside the line). Harness fixed (`off <= strlen`); fixed harness re-run at N=7 (smallest size where "true" is reachable), signed char: VERIFICATION SUCCESSFUL (3.4 min). Unsigned char and N=8 not re-run yet. Note N=6 could not reach a true result (needs 7 bytes), so test_for_static's "true" case is covered only by the difftest so far.
- Differential test (`cbmc/difftest.c`, gcc -O2, real libc, signed and unsigned char): parse_tag_line and test_for_static exhaustive over an 8-symbol alphabet up to 7 bytes (2,396,745 lines) plus tag_strnicmp case pairs: 0 failures.

## Relies on
- libc `strlen`, `strchr`, `strncmp` written from C11 7.24 in `cbmc/libc.h` (CBMC's own models replaced so every byte read is checked). `strstr` is proved unreachable.
- `--conversion-check` is off: char -> uint8_t casts are defined C; same check set as mbyte plus unsigned/pointer overflow.
- Bounded: lengths above N are not covered. Next step: WP proofs for unbounded length (the functions are simple scans) or larger N in CI.

## Mutation check (quick, not the full review gate)
5/5 planted bugs caught: drop the empty-command FAIL, drop the NUL stop in tag_strnicmp,
`"file:"` length 5 -> 4, matching_line_len off by one, missing case fold on s2.

## Still unverified in tag.c
`parse_match`, `find_extra`, `findtags_parse_line`, `findtags_hdr_parse`, `findtags_match_tag`,
`findtags_get_next_line`, `prepare_pats`, `tagfunc_cmd_kind`, `tag_full_fname`, `expand_tag_fname`,
`test_for_current`, `add_tag_field`, `get_tags`, and all tag-stack / jump / UI functions
(`do_tag`, `jumpto_tag`, `find_tags`, `set_tagstack`, ...). No adversarial review yet; no
differential test yet. tag.c is not finished.
