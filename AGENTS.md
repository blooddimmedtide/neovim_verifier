# Agent guide: verifying Neovim in parallel

Many agents (Claude Code, Codex, or people) work here at once. The proofs are machine-checked,
so the only things that need care are **picking non-overlapping work** and **writing specs that
actually say something**.

## Pick work
1. `git pull`, then read `STATUS.md` and the open pull requests.
2. Take one source file under `src/nvim/` that has no open PR. Prefer files whose functions
   call nothing outside libc and already-verified files (leaves first). Good early files:
   `math.c`, `garray.c`, `sha256.c`, `charset.c` helpers, `mbyte.c` UTF-8 helpers, `strings.c`.
3. Open a **draft PR right away** titled `neovim: verify src/nvim/<file>.c` so nobody else takes it.

## Do the work
Copy the shape of `libraries/neovim/base64/`:
- `libraries/neovim/<stem>/wp/annotate.py` inserts ACSL contracts and loop annotations at exact
  upstream lines (it must fail if an anchor line no longer matches). Never edit upstream files.
- Every function gets a **functional** contract: what it returns and what it changes, in terms
  of a clear logic spec (like `enc_char` / `dec_byte` in base64). "No crash" alone is not done.
- Prove with Frama-C WP (`-wp-rte -wp-model Typed+Cast`, Z3 + CVC5), one WP run per function.
- Bit operations: state small lemmas in a `lemmas.py` and prove them with Z3 bit-vectors.
- No `admit`, `axiom`, `assumes` or unproved goals, ever. Code WP can't read (memcpy into an
  integer, char/uint8 views, string-literal `const char[]`, which Frama-C 33 wrongly assumes is
  all zeros) is rewritten by a declared tool patch (`wp/tool_patches.py`, `[[framac.tool_patch]]`
  in vpipe.toml) and each rewrite is proved identical to the original by a CBMC harness with no
  `__CPROVER_assume` (`equiv/`).
- The spec must not reuse the code's own tables or helpers: write the reference (alphabet,
  lookup table, formula) in ACSL and prove the code's table equals it.
- Track allocation with ghost variables in the memory stub (WP ignores \fresh and frees).
- Planted bugs are chosen by an independent reviewer (`mutants.toml`); every one must make the
  proof fail (`run_mutants.py`). Write a `CLAIM.md` listing everything the proof relies on.
- Add the target to `vpipe.toml`, update `status.tsv`, regenerate `STATUS.md`
  (`python3 -I tools/status.py libraries/neovim > STATUS.md`).

## Done means
A function is a `candidate` when its full contract is proved and CI is green; it becomes
`verified` only after the planted bugs are caught and both reviews (owner + fresh adversarial
agent) sign off. If you find a bug,
record it in `libraries/neovim/findings/`, mark the function open, and propose the fix as a PR to
`blooddimmedtide/verified_neovim`; it becomes `fixed` once the fixed code is proved here.

## Never
- Weaken or delete a property to make a proof pass, or add any `admit`/axiom.
- Edit `vendor`-style upstream copies, or another agent's open-PR file.
- Report a file finished while any of its functions is open.

## Lessons so far
- Decoder/encoder in one WP run timed out at random; separate runs per function were stable.
- Prefer arithmetic (`/`, `%`) in specs and bridge each bit operation with a Z3-checked lemma.
- `pkill -f frama-c` also kills your own shell; kill by PID.
- `/mnt`-style noexec mounts: call scripts with `bash script.sh`.
