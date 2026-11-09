---
entry: neovim/src/nvim/path.c (string and path helpers, first 19 of 67 functions)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
fixed_fork: https://github.com/blooddimmedtide/verified_neovim (branch claude/project-thread-t2grsh, commit ae63bc4)
toolchain: Frama-C 33.0 WP with Why3 1.8.2, Z3, CVC5 (Nix, pipeline toolchain/versions.toml); gcc for the differential test
strength: candidate   # full functional correctness for the 16 functions below, once the owner signs off the spec
platform: x86_64 Linux (UNIX defined, no MSWIN, no BACKSLASH_IN_FILENAME), char signed and unsigned (both proved)
---

# Claim card: Neovim path.c string and path helpers

Not finished: 19 of 67 path.c functions are proved, 1 more (`invocation_path_tail`) has a
fix proved memory-safe but not yet against its quoting rules, and 47 are open. The list is in
`PLAN.md`.

## What is proved, for every input

Every function: no undefined behavior (`-wp-rte`, signed overflow and downcasts included),
terminates (loop variants), reads nothing outside its documented input (for strings: nothing
past the NUL), writes nothing (`assigns \nothing`), and returns:

| Function | Property |
|---|---|
| `vim_ispathsep(c)`, `vim_ispathsep_nocolon(c)` | true exactly when `c == '/'` |
| `vim_ispathlistsep(c)` | true exactly when `c == ':'` |
| `path_head_length()` | 1 |
| `is_path_head(p)` | true exactly when `p[0] == '/'` |
| `path_skip_sep(p, colon)` | pointer to the first byte that is not '/', every byte before it '/' |
| `get_past_head(p)` | the same (the UNIX head is the leading '/' run) |
| `path_tail(f)` | `""` for NULL; else the pointer just past the last '/' (f when there is none): no '/' at or after it |
| `path_next_component(f)` | pointer just past the first '/', or to the NUL when there is no '/' |
| `path_tail_with_sep(f)` | `path_tail(f)` moved back over the '/' run in front of it, but not into the leading '/' head (`"dir///file.txt"` gives `"///file.txt"`, `"/file"` gives `"file"`) |
| `after_pathsep(b, p)` | true exactly when `p > b` and `p[-1] == '/'` |
| `path_is_absolute(f)` | true exactly when `f[0]` is '/' or '~' |
| `path_has_drive_letter(p, len)` | WHATWG URL "starts with a Windows drive letter" on the first `len` bytes: ASCII letter, ':' or '\|', then end or one of `/ \ ? #`. Reads only bytes below `len` |
| `path_is_url(p)` | 1 (URL_SLASH) for `":/"`, 2 (URL_BACKSLASH) for `":\\"`, else 0 |
| `path_with_url(f)` | when f starts with an RFC 3986 scheme (ASCII letter, then letters, digits, `+ - .`), the scheme does not end in `+ - .`, f is not a drive letter, and `":/"` or `":\\"` follows: that kind (1 or 2); else 0 |
| `vim_isAbsName(n)` | true exactly when n is a URL as above or starts with '/' or '~' |
| `add_pathsep(p)` | "" or a name ending in '/': true, unchanged; else if the name plus "/" fits in MAXPATHL (4096) bytes with its NUL: appends "/", true; else false, unchanged. Writes only `p[len]`, `p[len+1]` |
| `path_to_backslash(p)` | returns p; every '/' becomes '\', nothing else changes (NULL: nothing) |
| `path_to_slash(p)` | returns p; when p is not a URL (as `path_with_url`), every '\' becomes '/'; a URL is unchanged (NULL: nothing) |

The specs are written from each doc comment (and the WHATWG / RFC 3986 rules the comments
cite), not from the code. Where the doc is silent the reference follows the UNIX build's
code and says so: the head is the run of leading '/', and `path_tail(NULL)` is `""`.

## Finding

`invocation_path_tail()` reads past the end of its string when a double-quoted part ends in a
backslash (`'shell'` set to `"sh\`), or a quoted backslash is followed by a composing
character. WP fails on it (loop invariant "p stays in the string": 34/35 goals); ASan confirms
a heap-buffer-overflow read. All callers pass `'shell'`. Details and reproducer:
`../findings/path-invocation-tail.md`; draft upstream issue (not filed):
`/mnt/project-files/neovim-verify/upstream/path/`. The fix (verified_neovim ae63bc4) is proved
memory-safe and terminating, with the result and `*len` inside the string (40/40 goals).
Its quoting/escaping behavior is not specified or proved yet, so it is not counted as done.

## What the proof relies on

1. **Frama-C WP, Why3, Z3 and CVC5 are sound** for this code (Typed+Cast memory model, x86_64).
2. **Extraction** (`wp/build.py`): the proved file is the exact upstream (or fixed) text of each
   function, sha256 pinned, with ACSL only in comments; the build checks that removing the
   comments gives the text back. The prelude defines `UNIX`, `NUL`, `ASCII_IS*`, `ascii_isdigit`
   and the URL enum as Neovim's headers do (each checked against the header text), and the
   `FUNC_ATTR_*` macros as nothing (attributes only).
3. **One tool patch** (`wp/tool_patches.py`): Frama-C 33 WP assumes string literals are all
   zero bytes (verification-notes/toolchain-bugs/framac33-wp-string-init.md; it showed up here
   as an unprovable goal in `path_is_url`). The two literals in `path_is_url`, and `PATHSEPSTR` (`"/"`) in the prelude, become
   compound literals with the same bytes; `equiv/literals.c` checks the bytes match (run by run_wp.sh).
   The only other literal is `path_tail`'s `""`, which really is all zeros.
4. **C library**: `strlen` and `strncmp` meet the C11 contracts in `memory/wp/stubs/vp_string.h`.
5. **Unproved mbyte.c callees**, by contract from their doc comments (`wp/stubs/vp_path.h`):
   `utfc_ptr2len(p)` returns 0 at the NUL and 1 .. strlen(p) otherwise; `utf_head_off(b, p)` is
   0 at an ASCII byte (an ASCII byte always starts a UTF-8 character).
6. **memory.c `strchrsub`** meets the contract proved for it in `memory/wp` (candidate there).
7. **Preconditions**: strings are NUL-terminated; each string function gets its length as a
   ghost parameter (it adds no runtime behavior). `path_has_drive_letter` needs
   `min(len, 3)` readable bytes; `after_pathsep` needs `b .. p` readable. `add_pathsep` needs `p[len]`, `p[len+1]` writable when they fit in MAXPATHL (its callers pass MAXPATHL buffers). The prelude defines MAXPATHL as 4096 (os_defs.h's DEFAULT_MAXPATHL; Linux PATH_MAX is 4096, so the header picks 4096).
8. **Smoke tests** (`-wp-smoke-tests`, all functions): no contract or stub is contradictory. The one doomed smoke test is the `utf_head_off(...) != 0` outcome in `after_pathsep`, which is dead code: `p[-1]` is '/' there, an ASCII byte.

## Not covered

- The other 47 path.c functions (file system, globbing, expansion, `path_cmp`, ...), and the
  quoting rules of `invocation_path_tail`.
- The MSWIN build (drive letters, backslashes as separators).
- Independent review by a fresh agent, CI in the pinned container, owner sign-off.

## Evidence

| Check | Command | Result |
|---|---|---|
| WP, upstream | `bash wp/run_wp.sh <nvim> upstream` | 20 functions (19 + ascii_isdigit) all goals, signed and unsigned char; `invocation_path_tail` 34/35 (the finding) |
| WP, fixed fork | `bash wp/run_wp.sh <verified_neovim> fixed` | 21 / 21 functions all goals, signed and unsigned char |
| Differential test (gcc -O2, ASan+UBSan) | `bash difftest/run_difftest.sh <nvim> upstream` (and `fixed`) | 5,229,043 strings (all of length 0..6 over 13 bytes), 0 failures, both signednesses |
| Planted bugs | `python3 -I run_mutants.py <nvim> <verified_neovim>` | see `mutants_result.tsv` |
| Independent review | — | pending |
| CI, pinned container | — | pending |
| Owner review | Yerin | pending |
