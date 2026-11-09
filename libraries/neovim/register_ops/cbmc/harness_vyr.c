// CBMC harness for valid_yank_reg (register.c), with vim_strchr (strings.c) and
// utf_char2bytes (mbyte.c) verbatim. Reference from :help registers: writable registers are
// 0-9, a-z, A-Z, '"', '-', '_', '*', '+'; read-only ones (only when !writing) are / # . % : =.
#include "ro.c"
// libc model: CBMC 6.4 has no strstr body. Plain C standard semantics (first occurrence).
char *strstr(const char *h, const char *n)
{
  for (;; h++) {
    size_t i = 0;
    while (n[i] != 0 && h[i] == n[i]) i++;
    if (n[i] == 0) return (char *)h;
    if (*h == 0) return NULL;
  }
}
int nondet_int(void);
bool nondet_bool(void);
void harness_valid_yank_reg(void)
{
  int c = nondet_int();
  bool writing = nondet_bool();
  bool alnum = ('0' <= c && c <= '9') || ('a' <= c && c <= 'z') || ('A' <= c && c <= 'Z');
  bool ro = c == '/' || c == '#' || c == '.' || c == '%' || c == ':' || c == '=';
  bool rw = c == '"' || c == '-' || c == '_' || c == '*' || c == '+';
  bool want = alnum || rw || (!writing && ro);
  assert(valid_yank_reg(c, writing) == want);
}
