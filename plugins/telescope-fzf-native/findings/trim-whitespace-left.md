# telescope-fzf-native: `trim_whitespace_left` skips at most half the leading spaces

Upstream b25b749, src/fzf.c:113 (same in the fixed copy).

```c
static char *trim_whitespace_left(char *str, size_t *len) {
  for (size_t i = 0; i < *len; i++) {   // i counts up while *len counts down
    if (str[0] == ' ') { (*len)--; str++; } else break;
```

With k leading spaces in a string of length L it removes min(k, ceil(L/2)) of them,
not k ("    a": L = 5, removes 3, leaves " a").

Severity: none observable. Its only caller, `fzf_parse_pattern`, then splits the pattern
with `strtok(..., " ")`, which skips leading delimiters, so the parsed pattern is the
same (proved for every pattern up to the bound in `cbmc/harness_api.c`, h_parse, which
compares the parse with a reference that trims fully). Reported because the helper does
not do what its name says, so a future caller could rely on it.

Fix: `while (*len > 0 && str[0] == ' ') { (*len)--; str++; }`

CBMC: `cbmc/harness_helpers.c` h_trim_left states the actual behaviour (proved); with
`-DINTENDED` the full-trim assertion fails with the counterexample above.
