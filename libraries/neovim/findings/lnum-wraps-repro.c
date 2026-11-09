// tv_get_lnum / tv_get_lnum_buf (src/nvim/eval/typval.c @ 7b87ce8) convert the 64-bit Number
// with a plain cast: `(linenr_T)tv_get_number_chk(tv, NULL)`, linenr_T = int32_t.
// gcc -O2 lnum-wraps-repro.c -o r && ./r
#include <inttypes.h>
#include <stdio.h>
typedef int64_t varnumber_T;
typedef int32_t linenr_T;
int main(void) {
  varnumber_T inputs[] = {4294967297LL, 4294967296LL + 5, -4294967295LL, 2147483648LL};
  for (int i = 0; i < 4; i++) {
    linenr_T lnum = (linenr_T)inputs[i];   // the upstream expression
    printf("Number %" PRId64 " -> line %" PRId32 "\n", inputs[i], lnum);
  }
  return 0;
}
