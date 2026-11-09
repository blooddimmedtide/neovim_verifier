#include <stddef.h>
#include <string.h>
typedef struct expand_T expand_T;
#define FUNC_ATTR_UNUSED
#include "fn_args.c"
int nondet_int(void);
// Reference from the commands' documentation: ":retab -indentonly", ":messages clear",
// ":mapclear <buffer>" each have exactly one completion item, at index 0; other indices end the list.
int main(void) {
  int idx = nondet_int();
  char *a = get_retab_arg(NULL, idx), *b = get_messages_arg(NULL, idx), *c = get_mapclear_arg(NULL, idx);
  if (idx == 0) {
    __CPROVER_assert(a && strcmp(a, "-indentonly") == 0, "retab item 0");
    __CPROVER_assert(b && strcmp(b, "clear") == 0, "messages item 0");
    __CPROVER_assert(c && strcmp(c, "<buffer>") == 0, "mapclear item 0");
  } else {
    __CPROVER_assert(a == NULL && b == NULL && c == NULL, "list ends after one item");
  }
  return 0;
}
