// repeat_list (src/nvim/eval/funcs.c @ 7b87ce8) computes (n > 0) * n * slen before check_repeat_count.
// gcc -O0 -fsanitize=undefined -fno-sanitize-recover repeat-list-overflow-repro.c -o r && ./r 9223372036854775807 2
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
typedef int64_t varnumber_T;
int main(int argc, char **argv) {
  varnumber_T n = strtoll(argv[1], 0, 10); const int slen = atoi(argv[2]);
  long long arg = (n > 0) * n * slen;   // repeat_list in src/nvim/eval/funcs.c, verbatim expression
  printf("%lld\n", arg); return 0; }
