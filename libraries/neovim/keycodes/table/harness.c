// CBMC: find_special_key_in_table and get_special_key_code (verbatim, kt.c) against
// references written from their doc comments, over the generated key_names_table.
#include "kt.c"
int nondet_int(void);
char nondet_char(void);
#ifndef NAMELEN
#define NAMELEN 20
#endif
#define N ((int)(sizeof(key_names_table) / sizeof(key_names_table[0])))

static int lower(int c) { return ('A' <= c && c <= 'Z') ? c + 32 : c; }

int main(void) {
#ifdef IN_TABLE
  // "the index when found, -1 when not found" (preferred names only: is_alt false)
  int c = nondet_int();
  int want = -1;
  for (int i = 0; i < N; i++) if (key_names_table[i].key == c && !key_names_table[i].is_alt) { want = i; break; }
  __CPROVER_assert(find_special_key_in_table(c) == want, "first preferred entry");
#else
  // "Name ... assumed to end before the first non-idchar. If name starts with t_ the
  // next two characters are a termcap name. Return key code or 0 if not found."
  char name[NAMELEN + 1];
  for (int i = 0; i < NAMELEN; i++) name[i] = nondet_char();
  name[NAMELEN] = 0;
  int want;
  if (name[0] == 't' && name[1] == '_' && name[2] != 0 && name[3] != 0) {
    want = -((uint8_t)name[2] + ((int)(uint8_t)name[3] << 8));
  } else {
    int L = 0;
    while (L < NAMELEN && (('a' <= lower(name[L]) && lower(name[L]) <= 'z')
                           || ('0' <= name[L] && name[L] <= '9') || name[L] == '_')) L++;
    want = 0;
    for (int i = 0; i < N; i++) {
      const String *s = &key_names_table[i].name;
      if ((int)s->size != L) continue;
      int eq = 1;
      for (int k = 0; k < L; k++) if (lower((uint8_t)name[k]) != lower((uint8_t)s->data[k])) eq = 0;
      if (eq) { want = key_names_table[i].key; break; }
    }
  }
  __CPROVER_assert(get_special_key_code(name) == want, "key of the first entry with that name");
#endif
  return 0;
}
