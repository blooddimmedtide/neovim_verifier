// Stub: the one macro sha256.c uses, as in src/nvim/memory.h (run_cbmc.sh checks the text).
#pragma once
#include <string.h>
#define STRCPY(d, s)        strcpy((char *)(d), (char *)(s))  // NOLINT(runtime/printf)
