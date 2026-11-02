# telescope-fzf-native: two out-of-bounds reads in src/fzf.c

Upstream: nvim-telescope/telescope-fzf-native.nvim at b25b749b9db64d375d782094e2b9dce53ad53a40.

## 1. `trailing_whitespaces` reads before the text

```c
for (size_t i = str->size - 1; i >= 0; i--) {   // i >= 0 is always true for size_t
  if (!isspace((uint8_t)str->data[i])) break;
```

- Empty text: `i` starts at `SIZE_MAX`, so the first read is `data[SIZE_MAX]`, which is `data[-1]` in practice.
- Text that is all whitespace: after `data[0]`, `i` wraps to `SIZE_MAX` and the loop reads `data[-1]`, `data[-2]`, ... until it meets a non-space byte in whatever memory comes before.
- The count it returns is then larger than the text, and callers subtract it from `text->size` (`fzf_suffix_match`, `fzf_equal_match`), which wraps too.

Called from `fzf_suffix_match` (pattern `foo$`) and `fzf_equal_match` (pattern `^foo$`).

## 2. `fzf_suffix_match` reads before the text when the pattern is longer

```c
size_t diff = trimmed_len - M;
if (diff < 0) { ... }               // never true for size_t
for (size_t idx = 0; idx < M; idx++) {
  char c = text->data[idx + diff];  // idx + diff wraps below 0 when M > trimmed_len
```

A suffix pattern longer than the (trimmed) text reads `M - trimmed_len` bytes before the text.

## Reachability

Any Telescope picker that uses the fzf sorter (the plugin's whole purpose) passes every typed prompt token to `fzf_parse_pattern` and every candidate line to `fzf_get_score`. A user who types a token ending in `$` (for example `abc$`) while any candidate is shorter than the token, empty, or all spaces triggers it. Empty and whitespace-only candidates are common (blank buffer lines in `current_buffer_fuzzy_find`, for example). The reads are of heap bytes just before the candidate string; they change the score and, if they run off a mapped page, can crash Neovim.

## Reproduce (ASan)

```
gcc -g -fsanitize=address -I src src/fzf.c repro.c -o r1
./r1 'abc$' x      # heap-buffer-overflow READ in fzf_suffix_match (fzf.c:887)
./r1 'a$' ''       # heap-buffer-overflow READ in trailing_whitespaces (fzf.c:88)
./r1 'b$' '   '    # heap-buffer-overflow READ in trailing_whitespaces (fzf.c:88)
```

## Fix

`fix.diff`: count down with `i > 0` and read `data[i - 1]`; return no match when `trimmed_len < M` before subtracting.
With the fix, the random ASan/UBSan driver in `../fuzz/` ran about 2,000,000 inputs (4 seeds × 150 s) with no report. Fuzzing is evidence, not proof; the proof of the fixed file is in progress.
