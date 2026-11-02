#include "vp_string.h"
#define S3(b) char b[4]; b[0]='a'; b[1]='b'; b[2]='c'; b[3]=0;
void h_strlen_ok(void){ S3(b) size_t r=strlen(b); /*@ assert ok: r == 3; */ }
void h_strlen_f(void){ S3(b) size_t r=strlen(b); /*@ assert p: \false; */ }
void h_memchr_ok(void){ S3(b) char *r=memchr(b,'b',3); /*@ assert ok: r == &b[1]; */ }
void h_memchr_f(void){ S3(b) char *r=memchr(b,'b',3); /*@ assert p: \false; */ }
void h_memchr_hi_ok(void){ unsigned char b[2]; b[0]=200; b[1]=0; char *r=memchr(b,200,2); /*@ assert ok: r == (char*)&b[0]; */ }
void h_memchr_hi_f(void){ unsigned char b[2]; b[0]=200; b[1]=0; char *r=memchr(b,-56,2); /*@ assert p: \false; */ }
void h_memchr_n(void){ S3(b) char *r=memchr(b,'z',3); /*@ assert p: \false; */ }
void h_memchr_short(void){ char b[2]; b[0]='x'; b[1]='y'; char *r=memchr(b,'x',1000); /*@ assert p: \false; */ }
void h_strchr_ok(void){ S3(b) char *r=strchr(b,0); /*@ assert ok: r == &b[3]; */ }
void h_strchr_f(void){ S3(b) char *r=strchr(b,'c'); /*@ assert p: \false; */ }
void h_strchr_f0(void){ S3(b) char *r=strchr(b,0); /*@ assert p: \false; */ }
void h_strchr_n(void){ S3(b) char *r=strchr(b,'z'); /*@ assert p: \false; */ }
void h_memcpy_ok(void){ S3(a) char d[4]; memcpy(d,a,4); /*@ assert ok: d[1] == 'b'; */ }
void h_memcpy_f(void){ S3(a) char d[4]; memcpy(d,a,4); /*@ assert p: \false; */ }
void h_memmove_ok(void){ S3(a) memmove(a+1,a,2); /*@ assert ok: a[2] == 'b' && a[1] == 'a'; */ }
void h_memmove_f(void){ S3(a) memmove(a+1,a,2); /*@ assert p: \false; */ }
void h_memset_f(void){ char d[3]; memset(d,0,3); /*@ assert p: \false; */ }
void h_strcmp_eq_f(void){ S3(a) S3(b) int r=strcmp(a,b); /*@ assert p: \false; */ }
void h_strcmp_ne_ok(void){ S3(a) S3(b) b[1]='z'; int r=strcmp(a,b); /*@ assert ok: r != 0; */ }
void h_strcmp_ne_f(void){ S3(a) S3(b) b[1]='z'; int r=strcmp(a,b); /*@ assert p: \false; */ }
void h_strncmp_ok(void){ S3(a) S3(b) b[1]='z'; int r=strncmp(a,b,1); /*@ assert ok: r == 0; */ }
void h_strncmp_ok2(void){ S3(a) S3(b) b[1]='z'; int r=strncmp(a,b,2); /*@ assert ok: r != 0; */ }
void h_strncmp_f(void){ S3(a) S3(b) b[1]='z'; int s=strncmp(a,b,2); /*@ assert p: \false; */ }
void h_strncmp_f2(void){ S3(a) S3(b) int s=strncmp(a,b,100); /*@ assert p: \false; */ }
