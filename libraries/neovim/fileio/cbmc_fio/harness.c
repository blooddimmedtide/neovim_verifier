// get_fio_flags doc: "Return the FIO_ flags needed for the internal conversion if 'name' was
// unicode or latin1, otherwise 0. If "name" is an empty string, use 'encoding'."
// need_conversion doc: "Check if conversion from fenc to 'encoding' is needed. Conversion is
// not needed when fenc is empty, equal to 'encoding', both have the same nonzero FIO flags
// (e.g. "ansi"/"latin1", "ucs-4"/"ucs-4be"), or fenc is UTF-8 (Neovim's 'encoding' is always
// Unicode)."
// enc_canon_props (mbyte.c) is modelled as an arbitrary deterministic function of the string,
// restricted to the property shapes its table can produce (at most one Unicode width bit).
// Two strings get independent properties unless they are equal (then they must match).
#include <stdbool.h>
#include <string.h>
#include <assert.h>
#define NUL '\0'
enum { ENC_8BIT=0x01, ENC_DBCS=0x02, ENC_UNICODE=0x04, ENC_ENDIAN_B=0x10, ENC_ENDIAN_L=0x20,
       ENC_2BYTE=0x40, ENC_4BYTE=0x80, ENC_2WORD=0x100, ENC_LATIN1=0x200, ENC_LATIN9=0x400, ENC_MACROMAN=0x800 };
enum { FIO_LATIN1=0x01, FIO_UTF8=0x02, FIO_UCS2=0x04, FIO_UCS4=0x08, FIO_UTF16=0x10, FIO_ENDIAN_L=0x80 };
#define N 4
char *p_enc;
int pa, pb;
static int width_ok(int p){ int w=!!(p&ENC_2BYTE)+!!(p&ENC_4BYTE)+!!(p&ENC_2WORD); return w<=1; }
const char *last_name;
static char a[N], b[N];
int enc_canon_props(const char *name){ last_name=name; if (strcmp(name,a)==0) return pa; assert(strcmp(name,b)==0); return pb; }
#include FIO_C
static int ref_flags(int p){       // from the doc: unicode form + endianness, latin1, else 0
  if (p & ENC_UNICODE) {
    int L = (p & ENC_ENDIAN_L) ? FIO_ENDIAN_L : 0;
    if (p & ENC_2BYTE) return FIO_UCS2|L;
    if (p & ENC_4BYTE) return FIO_UCS4|L;
    if (p & ENC_2WORD) return FIO_UTF16|L;
    return FIO_UTF8;
  }
  return (p & ENC_LATIN1) ? FIO_LATIN1 : 0;
}
int nondet_int(void); char nondet_char(void);
static void mk(char *s){ for(int i=0;i<N-1;i++) s[i]=nondet_char(); s[N-1]=0; }
static void setup(void){ pa=nondet_int(); pb=nondet_int(); __CPROVER_assume(width_ok(pa)&&width_ok(pb)); if (strcmp(a,b)==0) __CPROVER_assume(pa==pb); }
void h_get_fio_flags(void){
  mk(a); mk(b); setup(); p_enc=b;   // 'encoding' is never empty (option invariant)
  __CPROVER_assume(b[0]!=0);
  int r=get_fio_flags(a);
  const char *eff = a[0] ? a : b;
  assert(last_name==eff);
  assert(r==ref_flags(eff==a?pa:pb));
}
void h_need_conversion(void){
  mk(a); mk(b); setup(); p_enc=b; __CPROVER_assume(b[0]!=0);
  int fe = ref_flags(pa), ee = ref_flags(pb);
  bool want = !(a[0]==0 || strcmp(a,b)==0 || (ee!=0 && fe==ee) || fe==FIO_UTF8);
  assert(need_conversion(a)==want);
}
