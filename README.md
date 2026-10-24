# neovim_verifier

Machine-checked proofs about [Neovim](https://github.com/neovim/neovim)'s C code, built
function by function, plus the tooling for many agents to work on it in parallel.

**Status: 0 of 8,107 functions admitted; 4 are proved and waiting for review.** Live table: [STATUS.md](STATUS.md).
Neovim is finished here only when every function is verified or has a verified fix.
A result counts only under the verified-libs admission standard: full functional
correctness on the real code, for every input, no `admit`s, planted bugs caught, and two
reviews. Anything short of that is listed as a candidate.

Pinned upstream: `neovim/neovim@7b87ce822e6f` (master, 2026-10-23). Upstream code is never
edited for a proof; annotations go into a pristine copy at proof time.

## Proved, pending review: `src/nvim/base64.c`

| Function | Result | How |
|---|---|---|
| `base64_encode` | Output is exactly the RFC 4648 Base64 of the input, NUL-terminated, for every input (up to 4 EiB). No runtime errors; one allocation, returned. | Frama-C WP, 260/260 goals |
| `base64_decode` | Returns a buffer **exactly when** the input is canonical padded Base64, and then the length and every byte match RFC 4648. No runtime errors, no leak, no double free. Upstream: inputs under 2 GiB (120/120 goals). Fixed version: every input (118/118 goals). | Frama-C WP |
| `vim_htobe64`, `vim_htobe32` | Equal to the big-endian reading of the bytes, for every input. | CBMC, no loops |

No `admit`s or axioms. The few statements Frama-C can't read are rewritten for the proof,
and each rewrite is proved identical to the original by CBMC for every input. Bit-level
lemmas are proved separately with Z3. Everything assumed is in
[CLAIM.md](libraries/neovim/base64/CLAIM.md).

**Bug found:** from 2 GiB on, upstream `base64_decode` skips its padding check, accepts
invalid input and returns bytes it never wrote
([details and repro](libraries/neovim/findings/base64-decode-over-2gib.md)). The fix is in
[verified_neovim](https://github.com/blooddimmedtide/verified_neovim) and is proved with no size limit.

**Tool bug found:** Frama-C 33 WP assumes a `const char` array initialized from a string
literal is all zeros, so it can prove false things about it. The proof here avoids it with
a CBMC-proved rewrite.

Extra checks: a differential test of the pristine code, the proved code and Python's
RFC 4648 implementation on ~100k inputs (0 mismatches), and 35 planted bugs chosen by an
independent reviewer ([REVIEW.md](libraries/neovim/base64/REVIEW.md), results in
`mutants_result.tsv`).

## Run it

```bash
bash tools/install.sh                       # CBMC 6.4.1, Frama-C 33, Why3, Z3, CVC5 (Ubuntu 24.04)
export PATH="$HOME/.nix-profile/bin:$PATH"
git clone https://github.com/neovim/neovim nvim-src && git -C nvim-src checkout 7b87ce822e6f
python3 -I tools/run_target.py libraries/neovim nvim-src     # every target: proofs + checks
```

CI runs the same on every pull request (`.github/workflows/verify.yml`).

## Layout

```
libraries/neovim/
  vpipe.toml          pinned commit, targets, proved properties, assumptions
  inventory.tsv       every C function in src/nvim (tools/inventory.py)
  status.tsv          per-function status and evidence -> STATUS.md (tools/status.py)
  base64/             CLAIM.md, REVIEW.md, mutants.toml; wp/ (annotate.py, lemmas.py,
                      tool_patches.py, stubs), equiv/, bridge/, difftest/, cbmc/ (bounded, older)
  findings/           bugs found, with repros
tools/                install, inventory, status, target runner
AGENTS.md             how agents pick up and finish work in parallel
```

## Helping (people or agents)

Read [AGENTS.md](AGENTS.md). One pull request per source file; CI decides what counts as verified.
