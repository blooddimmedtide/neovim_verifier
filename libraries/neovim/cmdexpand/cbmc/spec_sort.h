// Reference for sort_func_compare (qsort comparator for function-name completion): names that
// start with '<' (script-local "<SNR>..."/"<SID>") sort after all others; otherwise byte order,
// comparing bytes as unsigned char like C strcmp. Only the sign of the result is specified.
static int ref_sort(const char *a, const char *b)
{
  int ka = a[0] == '<', kb = b[0] == '<';
  if (ka != kb) return ka ? 1 : -1;
  for (long i = 0;; i++) {
    unsigned char x = (unsigned char)a[i], y = (unsigned char)b[i];
    if (x != y) return x < y ? -1 : 1;
    if (x == 0) return 0;
  }
}
