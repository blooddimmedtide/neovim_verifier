// gcc -O2 -fsigned-char: compiled check_for_bom vs spec.h over every 4-byte
// combination of {00,BB,BF,EF,FE,FF,41}, sizes 2..4, and every flags value used.
#include <stdio.h>
#include <stdlib.h>
#include "spec.h"
#include FILEIO_BOM_C
int main(void) {
  const uint8_t v[] = {0x00, 0xBB, 0xBF, 0xEF, 0xFE, 0xFF, 0x41};
  const int fl[] = {FIO_ALL, 0, FIO_UTF8, FIO_UCS2, FIO_UCS4, FIO_UTF16, FIO_UCS2|FIO_ENDIAN_L,
                    FIO_UCS4|FIO_ENDIAN_L, FIO_UTF16|FIO_ENDIAN_L, 0x01, 0x2000, 0x4000};
  long n = 0, bad = 0;
  for (int a=0;a<7;a++) for (int b=0;b<7;b++) for (int c=0;c<7;c++) for (int d=0;d<7;d++)
  for (int s=2;s<=4;s++) for (unsigned f=0; f<sizeof fl/sizeof *fl; f++) {
    char *p = malloc(s); uint8_t q[4]={v[a],v[b],v[c],v[d]}; memcpy(p,q,s);
    int l1=-1,l2=-1; char *g=check_for_bom(p,s,&l1,fl[f]); const char *w=ref_bom((uint8_t*)p,s,fl[f],&l2);
    if (l1!=l2 || (!g)!=(!w) || (g && strcmp(g,w))) bad++;
    n++; free(p);
  }
  printf("%ld cases, %ld mismatches\n", n, bad); return bad != 0;
}
