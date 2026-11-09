// CBMC harness: sub_set_replacement / sub_get_replacement (src/nvim/ex_cmds.c).
// Spec (doc comments): set stores `sub` without copying it and releases the previous string;
// the previous ShaDa additional data is released unless the new value keeps the same pointer;
// get returns exactly what was last set. Checked over two consecutive sets from the initial
// state { NULL, 0, NULL }, so double frees, frees of live data and leaks all fail.
// Precondition (from "@warning sub must be in allocated memory. It is not copied."): each
// `sub.sub` is a fresh allocation (or NULL); `additional_data` is fresh, NULL or the stored one.
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
typedef uint64_t Timestamp;
typedef struct { uint32_t nitems; uint32_t nbytes; char data[]; } AdditionalData;
typedef struct { char *sub; Timestamp timestamp; AdditionalData *additional_data; } SubReplacementString;
static SubReplacementString old_sub = { NULL, 0, NULL };
static void xfree(void *p) { free(p); }
#include REPL_C
bool nondet_bool(void); uint64_t nondet_u64(void);
static SubReplacementString fresh(bool keep_ad)
{
  SubReplacementString s;
  s.sub = nondet_bool() ? NULL : malloc(4);
  s.timestamp = nondet_u64();
  s.additional_data = keep_ad ? old_sub.additional_data
                    : nondet_bool() ? NULL : malloc(sizeof(AdditionalData) + 2);
  return s;
}
void h_set_get(void)
{
  for (int round = 0; round < 2; round++) {
    SubReplacementString s = fresh(nondet_bool()), g;
    sub_set_replacement(s);
    sub_get_replacement(&g);
    __CPROVER_assert(g.sub == s.sub && g.timestamp == s.timestamp
                     && g.additional_data == s.additional_data, "get returns what was set");
    if (g.sub) g.sub[0] = 'x';                       // stored string still live
    if (g.additional_data) g.additional_data->nitems = 1;   // stored data still live
  }
  // Release the stored value: with --memory-leak-check, anything the setter forgot is a leak.
  sub_set_replacement((SubReplacementString){ NULL, 0, NULL });
}
