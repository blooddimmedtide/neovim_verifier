// Reproducer: invocation_path_tail reads past the terminating NUL when the
// invocation ends in a backslash inside an open double quote, e.g. "\"sh\\".
// The function text below is pasted verbatim from src/nvim/path.c (pinned commit);
// helpers are the UNIX definitions from path.c, utfc_ptr2len is 1 for ASCII (as in mbyte.c).
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define NUL '\000'
#define FUNC_ATTR_NONNULL_RET
#define FUNC_ATTR_NONNULL_ARG(x)
static int utfc_ptr2len(const char *p) { return *p == NUL ? 0 : 1; }
static bool vim_ispathsep(int c) { return c == '/'; }
static bool vim_ispathsep_nocolon(int c) { return vim_ispathsep(c); }
static char *path_skip_sep(const char *path, bool colon) { while (vim_ispathsep(*path)) path++; return (char *)path; }
static char *get_past_head(const char *path) { return path_skip_sep(path, true); }
const char *invocation_path_tail(const char *invocation, size_t *len)
  FUNC_ATTR_NONNULL_RET FUNC_ATTR_NONNULL_ARG(1)
{
  const char *tail = get_past_head(invocation);
  const char *tail_end = tail;
  const char *p = tail;
  bool inquote = false;
  while (*p != NUL && (inquote || *p != ' ')) {
    int l = utfc_ptr2len(p);
    if (vim_ispathsep_nocolon(*p)) {
      tail = p + 1;  // Now tail points one past the separator.
      tail_end = tail;
    } else if (*p == '\\' && inquote) {
      p++;
    } else if (*p == '"') {
      inquote ^= 1;
    } else {
      tail_end = p + l;
    }
    p += l;
  }

  if (len != NULL) {
    *len = (size_t)(tail_end - tail);
  }

  return tail;
}
int main(void) {
  // exact-size heap copy of the 'shell' value  "sh\   (open quote, trailing backslash)
  const char *s = "\"sh\\";
  char *buf = malloc(strlen(s) + 1);
  memcpy(buf, s, strlen(s) + 1);
  size_t len;
  const char *t = invocation_path_tail(buf, &len);
  printf("tail offset %td len %zu\n", t - buf, len);
  free(buf);
  return 0;
}
