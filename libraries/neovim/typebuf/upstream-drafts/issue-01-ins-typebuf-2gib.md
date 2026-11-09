DRAFT, not filed. For Yerin to file at neovim/neovim.

Title: feedkeys() with a string of 2 GiB or more crashes (int truncation in ins_typebuf)

### Problem
`ins_typebuf()` (src/nvim/input.c, was getchar.c) stores `(int)strlen(str)`. For 2^31 bytes or
more the length is negative and the following `memmove()` gets a size near 2^64, so Nvim
segfaults. Slightly shorter strings overflow `int extra = addlen + newoff + 4 * (MAXMAPLEN + 4)`.

### Steps to reproduce
```
nvim --clean --headless -u NONE \
  -c "let s = repeat(repeat('a', 65536), 32768)" \
  -c "call feedkeys(s, 'n')" -c 'qa!'
```
(needs about 5 GB of memory). Observed in 0.9.5: exit status 139 (SIGSEGV). Same code on master.

### Expected behavior
E74 "Command too complex", as `ins_typebuf()` already gives when the buffer would grow past INT_MAX.

### Suggested fix
```c
  const size_t slen = strlen(str);
  if (slen > (size_t)(INT_MAX - 5 * (MAXMAPLEN + 4))) {
    emsg(_(e_command_too_complex));
    setcursor();
    return FAIL;
  }
  int addlen = (int)slen;
```
Found with Frama-C WP; the fixed function is machine-checked (no admits).
