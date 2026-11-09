// get_undolevel: the buffer's 'undolevels' unless it is the "no local value" marker, then the
// global one. zero_fmark_additional_data: frees the additional data of all 26 marks and sets
// each pointer to NULL; nothing leaks (--memory-leak-check), nothing else in the array changes.
#include SMALL_C
int nondet_int(void); int64_t nondet_i64(void); _Bool nondet_bool(void);

void h_get_undolevel(void) {
  buf_T b; b.b_p_ul = nondet_bool() ? NO_LOCAL_UNDOLEVEL : nondet_i64(); p_ul = nondet_i64();
  OptInt r = get_undolevel(&b);
  assert(r == (b.b_p_ul == -123456 ? p_ul : b.b_p_ul));
}

void h_zero_fmark(void) {
  fmark_T m[NMARKS + 1];   // one extra entry to check nothing past NMARKS is touched
  AdditionalData *sentinel = (AdditionalData *)malloc(1);
  for (int i = 0; i < NMARKS; i++) m[i].additional_data = nondet_bool() ? (AdditionalData *)malloc(1) : NULL;
  m[NMARKS].additional_data = sentinel;
  zero_fmark_additional_data(m);
  for (int i = 0; i < 26; i++) assert(m[i].additional_data == NULL);
  assert(m[NMARKS].additional_data == sentinel);
  free(sentinel);
}
