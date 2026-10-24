### Problem

`base64_decode()` in `src/nvim/base64.c` stores the index of the first `=` in an `int`:

```c
int leftover_i = -1;
...
if (c == '=') {
  leftover_i = (int)src_i;
  break;
}
...
if (leftover_i > -1) {
  // validate padding
}
```

When `src_i >= 2^31` the cast wraps to a negative value, so `leftover_i > -1` is false and the padding check is skipped. The decoder then:

- accepts invalid input (anything after the first `=` is never looked at), and
- returns `out_len` computed from the last two characters, while the loop stopped early, so the tail of the returned buffer is uninitialized heap memory.

### Steps to reproduce

Calling `base64_decode` directly from C (built against master `7b87ce822e`):

```c
size_t n = (1ul << 31) + 4;
char *s = malloc(n);
memset(s, 'A', n);
s[1ul << 31] = '=';            // "AAAA...AAAA=AAA"
size_t out_len;
char *d = base64_decode(s, n, &out_len);
// d != NULL, out_len == 1610612739; the last 3 bytes of d were never written.
```

The same shape at 8 bytes (`"AAAA=AAA"`) is correctly rejected.

### Expected behavior

Inputs of any length with a non-trailing `=` are rejected, and no uninitialized bytes are returned.

### Impact

Low. LuaJIT strings are capped just under 2 GiB, so `vim.base64.decode()` probably can't reach this in LuaJIT builds. Builds using PUC Lua allow larger strings.

### Suggested fix

Track the padding position as `size_t` with a separate flag (or keep `src_i` after the `break`), e.g.:

```c
bool has_padding = false;
...
if (c == '=') { has_padding = true; break; }
...
if (has_padding) {
  for (size_t i = src_i; i < src_len; i++) { ... }
}
```

### How this was found

Formal verification of `base64.c` with CBMC and Frama-C WP. The WP memory-safety proof of `base64_decode` needs `src_len <= INT_MAX`; investigating why led to this case, which was then confirmed by running the code.

### Neovim version

master 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd (2026-10-23)

### Operating system/version

Ubuntu 24.04, x86_64, gcc
