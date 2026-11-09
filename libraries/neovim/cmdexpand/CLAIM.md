---
entry: neovim/src/nvim/cmdexpand.c (string helpers, partial)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
toolchain: CBMC 6.4.1 (.deb, see tools/install.sh)
strength: candidate (3 functions, all inputs) + bounded (2 functions, inputs up to a length)
platform: x86_64, char signed and unsigned (both proved)
---

# Claim card: Neovim cmdexpand.c string helpers (partial, 5 of 89 functions)

Function bodies are extracted verbatim (sha256 below) and checked against independent
references in `cbmc/spec*.h`, written from the commands' documented meaning. Every loop is
fully unwound (`--unwinding-assertions`); strings are exact-size heap objects, so any read
past the terminating NUL fails the pointer check. Re-run with `bash cbmc/run.sh`.

| Function | sha256 of body | Strength | Property |
|---|---|---|---|
| `find_cmd_after_global_cmd(arg)` | 4fa62a5a87d34ae0bbd0e7445372df7435ce78c20947ff1b9212e49d8146398b | bounded: strlen(arg) <= 10 | First char is the delimiter; returns the char after the first later delimiter not escaped by an odd run of backslashes (a backslash delimiter is never escaped), else NULL. Reads nothing past the NUL |
| `sort_func_compare(s1, s2)` | 4e7303c672508f775c1d40b4500a6c3e86633c3cc88341d40258937897c75e29 | bounded: each string <= 6 bytes | Sign equals the reference: names starting with `<` sort after all others, otherwise unsigned byte order (strcmp). No out-of-bounds read |
| `get_retab_arg(xp, idx)` | 74756d5fbc64095c57c845d3760fdead41e28cc48fa9e466fa6b9215ed90fba6 | candidate, every int idx | idx 0 -> "-indentonly", else NULL |
| `get_messages_arg(xp, idx)` | 20086df4585d39c4966d5ffebd9a559da9e858bd5b975e0630670ec251c5144d | candidate, every int idx | idx 0 -> "clear", else NULL |
| `get_mapclear_arg(xp, idx)` | e280dea90683e0c7cd7d2ccd14ae96b0d19c99f3ba3f858d95b635f518153619 | candidate, every int idx | idx 0 -> "<buffer>", else NULL |

Harness assumptions (each listed): `arg`/`*s1`/`*s2` are live NUL-terminated strings (callers
pass the command line or completion matches; xmalloc never returns NULL). `xp` is unused.

The two string-scanning functions have unbounded loops, so the bounded result is not a
full-correctness claim; a Frama-C WP proof with loop invariants is the next step.

Planted bugs (7, `cbmc/run.sh`): all caught. No independent review yet; no differential test yet.

## Finding

None so far.
