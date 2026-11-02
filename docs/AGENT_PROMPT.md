# Prompt for a parallel verification agent

Paste everything below the line into a new Claude Code or Codex session that has push access
to `blooddimmedtide/neovim_verifier` (and, for fixes, `blooddimmedtide/verified_neovim`).
Change nothing else; the agent picks its own file.

---

You are one of several agents formally verifying Neovim, function by function, in
https://github.com/blooddimmedtide/neovim_verifier. Read `AGENTS.md` and `STATUS.md` first,
then follow them exactly. In short:

1. **Claim a file.** Run `gh pr list --repo blooddimmedtide/neovim_verifier --state open`.
   Choose a file under `src/nvim/` in STATUS.md that no open PR names, preferring files whose
   functions call only libc or already-proved functions. Open a draft PR titled
   `neovim: verify src/nvim/<file>` right away, before any proof work, so nobody else takes it.
2. **Pick the tool per function.**
   - Bounded loops or none, byte-level code: CBMC, like `libraries/neovim/mbyte/cbmc/`
     (verbatim extraction with sha256 pins, an independent reference in `spec.h`, nondeterministic
     inputs, exact-size objects so out-of-bounds reads fail, `--unwinding-assertions`).
   - Loops over unbounded data: Frama-C WP with loop invariants, like `libraries/neovim/base64/`.
   - Never `admit`, axioms, unchecked assumes or unproved goals. Input preconditions in a harness
     are allowed only when they are documented or asserted by the function; list each in CLAIM.md.
3. **Write the spec before the proof**, from the function's documented meaning and the standard
   it implements, not from its code or tables. State in CLAIM.md what the reference decides
   itself (for example, what to return on bad input).
4. **Prove both C char signednesses** (`--unsigned-char` run) and x86_64. Add a differential test:
   compiled code (`gcc -O2 -fsigned-char`) against your reference, exhaustive where it fits.
5. **If the proof fails, look for a real bug before weakening anything.** Reproduce it with
   ASan/UBSan, write `libraries/neovim/findings/<name>.md` and a reproducer, push a fix branch to
   `blooddimmedtide/verified_neovim` (based on the pinned upstream commit, one fix per branch),
   prove the fixed code, and say so in the PR. Do not file upstream issues yourself; the owner does.
6. **Review.** When everything passes, start a fresh agent with no context of yours as an
   adversarial reviewer: it writes `REVIEW.md` and at least 10 planted bugs (`mutants.toml`),
   and every non-equivalent one must be caught. Address what it finds.
7. **Record.** CLAIM.md (copy the shape of `libraries/neovim/mbyte/CLAIM.md`), a `[targets.*]`
   entry in `libraries/neovim/vpipe.toml`, rows in `status.tsv` (status `candidate` or
   `fixed-candidate`; only the owner's sign-off makes it `verified` / `fixed`), regenerate
   `STATUS.md` with `python3 -I tools/status.py libraries/neovim > STATUS.md`.
8. **Finish.** Mark the PR ready. CI must pass in the pinned container. Never call a file done
   while any of its functions is open, and never weaken a property to get a pass.

PR body: what is proved, what it relies on, any finding, and the evidence table. Commit as
yourself; no model names in commits or PRs.
