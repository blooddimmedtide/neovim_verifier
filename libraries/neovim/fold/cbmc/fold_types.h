// Minimal copies of the types foldFind uses (pinned commit: pos_defs.h, garray_defs.h, fold.c:67-76).
#pragma once
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
typedef int32_t linenr_T;
typedef struct { int ga_len; int ga_maxlen; int ga_itemsize; int ga_growsize; void *ga_data; } garray_T;
typedef enum { kNone = -1, kFalse = 0, kTrue = 1 } TriState;
typedef struct {
  linenr_T fd_top;
  linenr_T fd_len;
  garray_T fd_nested;
  char fd_flags;
  TriState fd_small;
} fold_T;
