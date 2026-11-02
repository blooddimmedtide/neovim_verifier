# Independent review: utf_cp_bounds_len / utf_cp_bounds (CBMC), finding cp-bounds-over-2gib, fix aec5ed2

Reviewer: fresh adversarial reviewer (did not write the proof). Date: 2026-11-02.
Inputs: `harness_bounds.c`, `spec.h`, `build.py`, `extract.py`, `run_cbmc.sh` (this directory),
`../CLAIM.md`, `../../findings/cp-bounds-over-2gib.md` + reproducer, upstream 7b87ce8,
`verified_neovim` commit aec5ed2. Scratch work (probe harnesses, logs, mutated files):
`/tmp/claude-0/-home-claude/6d24df0b-9d65-5d89-84cb-9e71c7c76de6/scratchpad/rev-bounds/`.
CBMC 6.4.1, x86_64, same flags as `run_cbmc.sh`.

## Verdict: accept with changes

The upstream result (p - base <= INT_MAX) and the finding stand. The fix is correct and
minimal. But two stated properties are not what CBMC checked, and the card is stale. All three
are wording or small harness changes; none needs new proof engineering.

## Blocking findings (must change before admission)

**B1. "Any distance" / "every distance up to PTRDIFF_MAX" is not machine-proved; CBMC only models
`p - base` + 6 < 2^56.** With the default `--object-bits 8`, CBMC pointers have 56 offset bits.
`malloc(d + 6)` with a bigger `d` is accepted (no failure, since `--no-malloc-may-fail`) and the
offset wraps. Probe (`probe.c`): `assume(d <= PTRDIFF_MAX - 6); p = obj + d; assert((size_t)(p - obj) == d)`
FAILS with d = 0x017FFFFFFFFFFFFC. The same check with `d <= 2^56 - 7` is proved. So for
d >= 2^56 the fixed-fork harness compares the code and `ref_bounds` on a wrapped distance, and both
are wrong in the same way.
Shown by mutant `fix-wrong-past-2pow56`: a "fix" that keeps only 56 bits of the distance
(`MIN((p - b) & 0xFFFFFFFFFFFFFF, 5)`, wrong at d = 2^56 + 2) is **proved** by both harnesses at the
default settings. With `--object-bits 3` (61 offset bits) both harnesses catch it, and the real fix
is still proved (h_cp_bounds_len 156 s, h_cp_bounds 212 s).
Practical impact is nil: no x86_64 object reaches 2^56 bytes (user space is 2^47, or 2^56 with
5-level paging). The problem is the evidence claim. Required:
- either run the fixed-fork harnesses with `--object-bits 3`, assume `d <= 2^60 - 8`, add
  `__CPROVER_assert((size_t)(p - base) == d, "model keeps the distance")` to each harness so a
  too-large bound fails loudly, and state "p - base < 2^60 (machine-proved); larger distances do not
  exist on x86_64";
- or keep the flags and state "p - base < 2^56 - 6".
Fix the wording in `CLAIM.md` ("Any distance `p - base`"), `findings/cp-bounds-over-2gib.md`
("proved correct for every distance up to `PTRDIFF_MAX`"), the harness comment ("any distance a C
object allows") and, if it is re-pushed, the aec5ed2 commit message ("Proved for every distance").

**B2. "Reads nothing ... more than 5 bytes back" is not proved.** The object runs from `base`, so
the pointer check only catches reads before `base`. A read at `p[-6]` with `p - base >= 6` is in
bounds and invisible. Mutant `back-six` (scan limit 6 instead of 5) gives the same results, reads
`p[-6]`, and is proved by both harnesses (signed and unsigned char). Required: drop that clause
from the card, or say "reads nothing before `base` or at/past `p + min(p_len, 6)`; the result depends
only on `p[-5..5]`". Proving the stronger clause would need a two-object or two-run harness, and
reading in-bounds bytes is harmless anyway.

**B3. CLAIM.md is stale for utf_cp_bounds.** "Not covered" still lists `utf_cp_bounds`, the table has
no row for it, and the evidence says "9 / 9 harnesses". `run_cbmc.sh` runs 10, including
`h_cp_bounds`, which this review confirms is proved and non-vacuous. Required: add a
`utf_cp_bounds(base, p)` row (equal to `utf_cp_bounds_len(base, p, INT_MAX)` on a NUL-terminated
stream; reads nothing past the NUL or past `p[5]`; same distance limit as B1), remove it from
"Not covered", and update the counts.

## Checks done

### 1. Is ref_bounds right for callers?
- I checked `ref_bounds` against a declarative statement: the result is (k, L - k) iff some
  k <= min(p - base, 5) has a lead `p[-k]` announcing L > k, continuation bytes at
  `p[-k+1 .. -k+L-1]`, and L - k <= p_len; otherwise (0, 1). This k is unique, because the lead
  must be the nearest non-continuation byte at or before p. That is exactly what the walk-back in
  `ref_bounds` finds. The reference is written in spec terms (`spec_is_cont`, `spec_lead_len`), not
  Neovim's table. It has the same overall shape as the code (scan back, then check forward), which is
  the main remaining risk, but I found no input on which the two would agree and both be wrong.
- The fast path `p[0] < 0x80` agrees with the reference (`!cont && < 0x80` is the same as `< 0x80`).
  Mutant `no-ascii-fast-path` confirms that the general path also gives (0,1) for ASCII.
- Callers:
  - `nlua_str_utf_start` / `_end` use `-begin_off` and `end_off - 1`. A stray or cut-off byte counts
    as its own character, giving 0, which is the documented behavior. `p_len = s1_len - off >= 1`,
    so `assert(p_len > 0)` holds.
  - `grid.c:297` passes `base = scbuf + off`, so the scan cannot reach the bytes of c0/c1 that are
    being replaced. That is right, and `rest >= 1` there.
  - `buffer.c:3510`: `namelen += end_off` always advances at least 1 byte. When `name + namelen` is
    at the start of a character, it skips that whole character, so the icon keeps fewer than 100
    bytes. This is a caller quirk; the function does what its doc says. Out of scope, not a defect
    in the claim.
- Overlong forms, 0xC0/0xC1, and 5- and 6-byte forms are accepted, as in `utf_ptr2len`. This is
  consistent with the rest of the card.

### 2. Harness soundness
- Object sizes are as described: `base..p` then `min(p_len, 6)` bytes. For `h_cp_bounds`, either
  n <= 5 nonzero bytes and a NUL, or 6 nonzero bytes. The `back-check-lt`, `no-base-clamp`,
  `end-loop-le` and `plen-ignored` mutants show that reads before base, past `p_len` and past
  `p[5]` are caught as pointer-check failures.
- Vacuity (`probe_bounds.c`, fixed fork): `assert(0)` after the main assertion fails in both
  harnesses. These cases are all reachable:
  - begin 5;
  - end 6;
  - lead at base (d = 3, b = 3);
  - p_len > 6 with e = 6;
  - a valid character at d > 2^31 and begin 5 at d > 2^40 (h_cp_bounds_len);
  - a 6-byte sequence at p, n = 2 with b = 3 before the NUL, and b = 4 at d > 2^31 (h_cp_bounds).
- The upstream-only assumption `d <= INT_MAX` is needed. Mutant `finding-no-precondition` (upstream
  code with the precondition removed) fails both harnesses with the `-INT_MIN` overflow, an
  unwinding failure (the scan does not stop) and a wrong result. This independently reproduces the
  finding.
- The `NVIM_FIXED_CP_BOUNDS` mechanism: the define is emitted only when the sha256 of the fixed
  piece matches, and it comes before the harness bodies. This is fine.
- `h_cp_bounds` is stricter than its contract: it forbids reads past `p[5]` even when the string
  continues. That is a stronger proved property, not a weakness.
- Baselines, signed char: h_cp_bounds_len proved for upstream (47 s) and the fixed fork (108 s);
  h_cp_bounds proved for the fixed fork (89 s).

### 3. Fix and reachability
- `-(int)MIN(p - b, MB_MAXCHAR - 1)`: the comparison is done in `ptrdiff_t` and the result is in
  0..5 before the cast. The fix is correct, and minimal (one line). The rest of mbyte.c is
  byte-identical between 7b87ce8 and aec5ed2.
- stdlib.c clamp: `(int)MIN(s1_len - off, (size_t)INT_MAX)`. When `s1_len - off <= INT_MAX`, which
  is true for every string under 2^31 bytes, the value equals the old `(int)(s1_len - off)`, so
  there is no behavior change. Both added includes exist and are sorted. This was checked by hand
  and is not machine-proved, as the finding says.
- Reachability: PUC Lua 5.1 is linked into nvim when `PREFER_LUA=ON`
  (`src/nvim/CMakeLists.txt:59-64`, lua-5.1.5 in `cmake.deps/deps.txt`). In 5.1, `lua_Integer` is
  `ptrdiff_t` and string lengths are `size_t`, so an index past 2^31 is reachable with about 2 GiB
  of memory. LuaJIT caps strings at `LJ_MAX_STR` = 0x7fffff00 (< 2^31). I quoted that from memory of
  `lj_def.h` and did not re-check it here. With that cap, `off` and `s1_len - off` stay
  <= INT_MAX. The finding's analysis is right. The PUC-Lua reach also turns the `p_len` truncation
  into an `assert(p_len > 0)` failure or a negative `p_len`, which the stdlib.c clamp removes.

### 4. Other
- Machine contention (another mutant run shared the 4 cores): `trail-ge` on h_cp_bounds_len hit my
  900 s timeout with no verdict. It is counted as caught because h_cp_bounds gives a real
  counterexample.

## Planted bugs (`mutants_bounds.toml`, 21 mutants)

All runs use signed char. The equivalent mutants were also run with `--unsigned-char`, and every
one was proved again. "fail" = counterexample. "n/a" = the harness does not exercise the changed
code.

| id | function | h_cp_bounds_len | h_cp_bounds | result | expected |
|---|---|---|---|---|---|
| ascii-le-80 | utf_cp_bounds_len | fail | fail | caught | caught |
| ascii-lt-c0 | utf_cp_bounds_len | fail | fail | caught | caught |
| no-ascii-fast-path | utf_cp_bounds_len | proved | proved | survived | equivalent |
| back-six | utf_cp_bounds_len | proved | proved | survived | equivalent (see B2) |
| back-four | utf_cp_bounds_len | fail | fail | caught | caught |
| no-base-clamp | utf_cp_bounds_len | fail (OOB before base) | fail | caught | caught |
| back-check-lt | utf_cp_bounds_len | fail (OOB before base) | fail | caught | caught |
| end-minus-first | utf_cp_bounds_len | fail | fail | caught | caught |
| illegal-lt0 | utf_cp_bounds_len | fail | fail | caught | caught |
| plen-ge | utf_cp_bounds_len | fail | proved (n/a: p_len = INT_MAX) | caught | caught |
| plen-ignored | utf_cp_bounds_len | fail (OOB past p_len) | proved (n/a) | caught | caught |
| end-loop-from-0 | utf_cp_bounds_len | fail | fail | caught | caught |
| end-loop-le | utf_cp_bounds_len | fail (OOB) | fail (OOB) | caught | caught |
| begin-sign | utf_cp_bounds_len | fail | fail | caught | caught |
| trail-top-bit | utf_is_trail_byte | fail | fail | caught | caught |
| trail-ge | utf_is_trail_byte | timeout (900 s) | fail | caught | caught |
| trail-no-cast | utf_is_trail_byte | proved | proved | survived | equivalent |
| wrapper-plen-6 | utf_cp_bounds | proved (n/a) | proved | survived | equivalent |
| wrapper-plen-5 | utf_cp_bounds | proved (n/a) | fail | caught | caught |
| finding-no-precondition | utf_cp_bounds_len | fail (overflow, unwind, result) | fail | caught | caught |
| fix-wrong-past-2pow56 | utf_cp_bounds_len | **proved** | **proved** | **survived** | caught → harness gap B1 |

Score: 16 of the 17 non-equivalent mutants caught. The 4 predicted-equivalent mutants all survived,
and each is justified in the toml. The one escape is B1. With `--object-bits 3` it is caught by
both harnesses.

The equivalent mutants are equivalent for these reasons:
- `no-ascii-fast-path`: an ASCII byte is not a trail byte and announces length 1, so the general
  path gives (0,1).
- `back-six`: a lead 6 back announces at most 6 bytes, which is not more than 6, so the result is
  (0,1) either way. It still violates the card's read claim (B2).
- `trail-no-cast`: the value is already in 0..0xC0.
- `wrapper-plen-6`: `L - k <= 6`, so `p_len = 6` never bites.

Note for `run_mutants.py`: it reads only `mutants.toml` and runs all 10 harnesses in both
signednesses. Pointing it at this file works, because the format is the same, but each mutant then
costs about 20 CBMC runs. Running only the two bounds harnesses, as done here, is enough.
