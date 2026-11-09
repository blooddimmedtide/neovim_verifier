# Independent review: undo-file byte helpers (undo.c + get2c/get4c/get8ctime)

Reviewer: fresh adversarial agent, 2026-11-09. Scope: `CLAIM.md`, `cbmc/{build.py,hashes.txt,model.h,spec.h,harness.c,run_cbmc.sh}`,
`wp/{annotate.py,run_wp.sh}`, `../findings/get8ctime-shift-overflow.md`, against upstream 7b87ce8 and
the fixed fork. Planted bugs: `mutants.toml`, `run_mutants.py`, results in `mutants_result.tsv`.

## Verdict: accept with changes

The proof is real. The functions are copied word for word and pinned by sha256. The reference
(`spec.h`) is integer arithmetic on 128-bit values, so it shares no code with the shifts it checks.
Every loop is fully unwound and the UB checks are on. The WP contract of `uhp_table_find` is
functional (found / missing, `complete`/`disjoint`) and includes termination. The get8ctime finding
holds up: upstream fails `h_read_time` with a signed-shl overflow, and the fixed fork passes. Every
harness precondition (early `return`) is either a length bound for the stream or matches a caller
or an `assert` (details below). The changes asked for are about the stdio model and the wording,
not the proved results.

## Issues

1. **Medium: the `fread`/`fwrite` model is wrong for size 0.** C11 7.21.8.1/7.21.8.2 (and glibc,
   checked here: `fread(b, 0, 1, f)` and `fwrite(b, 0, 1, f)` both return 0) say a zero size
   returns 0. The model returns 1. `h_read` and `h_read_any` allow `size == 0` and assert
   `ok == (len >= size)`, i.e. `true`, but the real `undo_read(bi, buf, 0)` returns **false**.
   So the CLAIM row for `undo_read` is false at size 0 in real C. No current caller passes 0
   (`UNDO_HASH_SIZE`, `sizeof(ExtmarkSplice/Move)`; `undo_read_string` checks `len > 0`; the
   `undo_write` callers check `len > 0` or pass fixed sizes), so nothing in Neovim is affected. But
   the model hides a real behavior: planted bug **m13** (drop the `len > 0 &&` guard in
   `undo_read_string`) makes `:rundo` reject every empty line in real C, and the proof does not
   catch it.
   *Fix:* in `model.h`, `if (size == 0 || n == 0) return 0;` at the top of `fread` and `fwrite`.
   Change the `h_read`/`h_read_any` spec to `ok == (size > 0 && len >= size)`, or keep `size >= 1`
   as a documented precondition. m13 is then caught.

2. **Low: "writes nothing when the write fails" is a property of the model.** A real `fwrite` that
   fails can write part of the data (a short write on a full disk, or bytes already buffered). The
   model writes all or nothing, so the `h_write_bytes` failure branch `out_len == 0` only checks the
   model. *Fix:* reword the `undo_write_bytes` row to "returns false when the write fails". Or model
   a failing write as a nondeterministic prefix and assert only `!ok` on failure.

3. **Low: the corruption-message choice in `undo_read_len` is not checked.** The harness counts
   `corruption_error` calls but ignores the message ("truncated" vs `what`). Planted bug **m19**
   (the two branches swapped) is not caught. The claim does not promise the message, so this is a
   gap in coverage, not an overstatement. *Fix:* have the `corruption_error` stub record `mesg` and
   assert `mesg == (feof ? "truncated" : what)`, where feof means the 4-byte read hit the end of the
   file (`len < 4` in the model).

4. **Low: stdio read errors are not modeled.** `getc`/`fread` only return EOF at the end of the
   data. A real read error (EIO) also returns EOF with `feof` false. The results still hold (an error
   acts like EOF), but `undo_read_len` then reports `what` instead of "truncated". *Fix:* list it in
   "What the proof relies on": "no read errors (a read error acts like EOF except for the message)".

5. **Low: the unbounded harnesses exist but are not run.** `h_read_any` and `h_read_string_any`
   (any length below 2^40) are in `harness.c`, but `run_cbmc.sh` does not run them, and CLAIM.md
   says `undo_read`/`undo_read_string` are "bounded only". I ran both against the upstream build and
   both pass (`VERIFICATION SUCCESSFUL`, under a minute each). *Fix:* add them to `run_cbmc.sh` and
   change those two CLAIM rows to "any size < 2^40" (after fixing issue 1). Otherwise delete them so
   the file does not suggest more than the evidence shows.

6. **Low: small gaps in what the harnesses check.**
   - `h_read_byte` and `h_read_time` do not check how many bytes are consumed. The other readers
     do: `h_read_4c` and `h_read_2c` check `in_pos`, but CLAIM.md says this only for get4c.
     *Fix:* add `assert(f->in_pos == (len >= 1 ? 1 : 0))` and the matching 8-byte assert.
   - `h_put_header_ptr`, `h_serialize_pos` and `h_serialize_visualinfo` set `writes_may_fail = false`,
     so their failure paths are not checked. That is fine (the functions return void and ignore
     failures), but the CLAIM rows should say "when every write succeeds".
   - The `h_read_len` validity condition is close to a copy of the code's own expression. That is
     acceptable here because the documented meaning ("non-negative, fits in the rest of the file") is
     the same expression. A version phrased as "`v <= fsize - 4`" (the bytes left after the field)
     would be more independent.

7. **Info: the preconditions are justified.**
   - `undo_write_bytes` 1 <= len <= 8: `assert(len > 0)`, the `buf[8]` local, and callers pass 1, 2,
     4 or 8.
   - `put_header_ptr` uh_seq >= 0: asserted.
   - `uhp_table_find`: num_head >= 0 (`undo_read_len` returns -1 or >= 0, and -1 jumps to error);
     every entry non-NULL (`num_read_uhps == num_head` is checked before the qsort); sorted (qsort
     with `uhp_seq_cmp` just before). Duplicates are rejected after the qsort, but the contract does
     not need that.
   - The stream-length caps (6, 3, 2, 9, 13, 33) cover every EOF position of a fixed-width reader,
     so "a longer stream behaves like the longest one checked" is correct.
   - `bi_fsize` and the `ftell` outcome are fully nondeterministic.

8. **Info: the claim relies on `xmallocz` never returning NULL.** That matches Neovim
   (`xmalloc` → `preserve_exit` on OOM). The model's `assert(size < SIZE_MAX)` stands in for
   xmallocz's own overflow abort. Acceptable.

## Planted bugs

There are 22 mutants in `mutants.toml`, all non-equivalent: get4c ×2, get2c ×2, get8ctime ×2 (on
the fixed fork), undo_write_bytes ×2, undo_read_len ×3, undo_read, undo_read_string ×2,
unserialize_pos, serialize_pos, unserialize_visualinfo, uhp_seq_cmp, put_header_ptr, and
uhp_table_find ×3 (WP). Two are marked `expect_uncaught`. They show issues 1 and 3:

- **m13** `undo_read_string` without the `len > 0` guard is wrong in real C, but the model cannot
  see it.
- **m19** has the `undo_read_len` error messages swapped.

Score (`python3 -I run_mutants.py`, about 2 minutes): **20/22 caught**. All 20 expected catches were caught,
including all 3 WP mutants (31/32, 32/33 and 32/33 goals proved). The only misses are m13 and m19, the two marked `expect_uncaught`.
Once issues 1 and 3 are fixed, m13 and m19 should be caught; their `expect_uncaught` flags should
then be removed.
