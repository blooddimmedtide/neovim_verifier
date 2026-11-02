import re,sys
src=open('mem.c').read()
A={
 'ret':[("  return dst;\n}","xmemcpyz_ret"),("    return n;\n  }\n  return (size_t)(end - s);","xstrnlen_notfound"),
        ("  return (size_t)(end - s);","xstrnlen_found"),("}\n\n// src/nvim/memory.c:319","strchrsub_end"),
        ("}\n\n// src/nvim/memory.c:336","memchrsub_end"),
        ("  return cnt;\n}\n\n// src/nvim/memory.c:354","strcnt_ret"),("  return cnt;\n}\n\n// src/nvim/memory.c:381","memcnt_ret"),
        ("  return (char *)memcpy(dst, src, len + 1) + len;","xstpcpy_ret"),("  return slen + dlen;  // Does not include NUL.","xstrlcat_ret")],
 'body':[("    *str++ = x;","strchrsub_body"),("    *p++ = x;","memchrsub_body"),("    str++;  // Skip the instance of c.","strcnt_body"),
         ("    ptr++;  // Skip the instance of c.","memcnt_body")]}
for a,name in A[sys.argv[1]]:
    assert src.count(a)==1,name
    if name.endswith('_end') or name in('strcnt_ret','memcnt_ret'):
        # put before the <END> / return annotations block start: find the line index and insert there
        pass
    ind=re.match(r'\s*',a).group(0) or '  '
    src=src.replace(a, ind+'/*@ assert p_%s: \\false; */\n'%name+a)
open('probe_%s.c'%sys.argv[1],'w').write(src)
