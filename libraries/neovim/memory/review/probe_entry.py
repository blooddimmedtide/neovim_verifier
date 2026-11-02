import re,sys
src=open(sys.argv[1] if len(sys.argv)>1 else 'mem.c').read()
P='/*@ assert probe: \\false; */ '
pts=[ # (anchor occurring once, insert before it)
 ("  memcpy(dst, src, len);\n  ((char *)dst)[len] = NUL;", "xmemcpyz-entry"),
 ("  return dst;\n}", "xmemcpyz-ret"),
 ("  const char *end = memchr(s, NUL, n);", "xstrnlen-entry"),
 ("    return n;\n  }\n  return (size_t)(end - s);", "xstrnlen-notfound"),
 ("  return (size_t)(end - s);", "xstrnlen-found"),
 ("  return p ? (char *)p : (char *)(str + strlen(str));", "xstrchrnul-ret"),
 ("  return p ? (char *)p : (char *)addr + size;", "xmemscan-ret"),
 ("  assert(c != NUL);", "strchrsub-entry"),
 ("    *str++ = x;", "strchrsub-body"),
 ("  char *p = data;\n  char *end", "memchrsub-entry"),
 ("    *p++ = x;", "memchrsub-body"),
 ("  assert(c != 0);", "strcnt-entry"),
 ("  const char *ptr = data;", "memcnt-entry"),
 ("  const size_t len = strlen(src);", "xstpcpy-entry"),
 ("  return (char *)memcpy(dst, src, len + 1) + len;", "xstpcpy-ret"),
 ("    return dst + srclen;", "xstpncpy-nul"),
 ("    return dst + maxlen;", "xstpncpy-full"),
 ("    dst[len] = NUL;", "xstrlcpy-copy"),
 ("  return slen;  // Does not include NUL.", "xstrlcpy-ret"),
 ("    dst[dsize - 1] = NUL;", "xstrlcat-trunc"),
 ("    memmove(dst + dlen, src, slen + 1);", "xstrlcat-fits-pre"),
 ("  return slen + dlen;  // Does not include NUL.", "xstrlcat-ret"),
 ("      return (uint8_t *)src + len;", "xmemrchr-found"),
 ("  return NULL;\n}", "xmemrchr-null"),
 ("  return (a == NULL && b == NULL) || (a && b && strcmp(a, b) == 0);", "strequal-entry"),
 ("  return (a == NULL && b == NULL) || (a && b && strncmp(a, b, n) == 0);", "strnequal-entry"),
]
for a,name in pts:
    assert src.count(a)==1,(name,src.count(a))
    ind=re.match(r'\s*',a).group(0)
    src=src.replace(a, ind+P.replace('probe','p_'+name.replace('-','_'))+'\n'+a)
# loop body counters in strcnt/memcnt: before "    str++;  // Skip" and "    ptr++;  // Skip"
for a,name in [("    str++;  // Skip the instance of c.","strcnt-body"),("    ptr++;  // Skip the instance of c.","memcnt-body"),
               ("  return cnt;\n}\n\n// src/nvim/memory.c:354","strcnt-ret"),("  return cnt;\n}\n\n// src/nvim/memory.c:381","memcnt-ret")]:
    assert src.count(a)==1,name
    src=src.replace(a, ('  ' if 'ret' in name else '    ')+P.replace('probe','p_'+name.replace('-','_'))+'\n'+a)
# stub consistency harnesses
src+=r'''
void h_strlen(void){ char b[4]="ab"; size_t r=strlen(b); /*@ assert ok_strlen: r == 2; */ /*@ assert p_h_strlen: \false; */ }
void h_memchr_f(void){ char b[4]="abc"; char *r=memchr(b,'b',3); /*@ assert ok_memchr: r == b+1; */ /*@ assert p_h_memchr_f: \false; */ }
void h_memchr_n(void){ char b[4]="abc"; char *r=memchr(b,'z',3); /*@ assert p_h_memchr_n: \false; */ }
void h_memchr_hi(void){ unsigned char b[2]={200,0}; char *r=memchr(b,200,2); /*@ assert ok_memchr_hi: r == (char*)b; */ /*@ assert p_h_memchr_hi: \false; */ }
void h_strchr_f(void){ char b[4]="abc"; char *r=strchr(b,'c'); /*@ assert ok_strchr: r == b+2; */ /*@ assert p_h_strchr_f: \false; */ }
void h_strchr_nul(void){ char b[4]="abc"; char *r=strchr(b,0); /*@ assert ok_strchr0: r == b+3; */ /*@ assert p_h_strchr_nul: \false; */ }
void h_strchr_n(void){ char b[4]="abc"; char *r=strchr(b,'z'); /*@ assert p_h_strchr_n: \false; */ }
void h_memcpy(void){ char a[3]="ab"; char d[3]; memcpy(d,a,3); /*@ assert p_h_memcpy: \false; */ }
void h_memmove(void){ char a[5]="abcd"; memmove(a+1,a,3); /*@ assert ok_memmove: a[3] == 'c'; */ /*@ assert p_h_memmove: \false; */ }
void h_memset(void){ char d[3]; memset(d,0,3); /*@ assert ok_memset: d[2] == 0; */ /*@ assert p_h_memset: \false; */ }
void h_strcmp_eq(void){ char a[3]="ab", b[3]="ab"; int r=strcmp(a,b); /*@ assert ok_strcmp: r == 0; */ /*@ assert p_h_strcmp_eq: \false; */ }
void h_strcmp_ne(void){ char a[3]="ab", b[3]="ac"; int r=strcmp(a,b); /*@ assert ok_strcmp_ne: r != 0; */ /*@ assert p_h_strcmp_ne: \false; */ }
void h_strncmp(void){ char a[3]="ab", b[3]="ac"; int r=strncmp(a,b,1); /*@ assert ok_strncmp: r == 0; */ int s=strncmp(a,b,2); /*@ assert ok_strncmp2: s != 0; */ /*@ assert p_h_strncmp: \false; */ }
'''
open(sys.argv[2] if len(sys.argv)>2 else 'probe.c','w').write(src)
