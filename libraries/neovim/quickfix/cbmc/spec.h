// Independent references, written from the 'errorformat' documentation (:help errorformat).
// A part of 'errorformat' ends at an unescaped ',' or at the end; "\x" escapes x (a trailing
// backslash escapes nothing).
static int ref_part_len(const char *s) {
  int i = 0;
  while (1) {
    if (s[i] == '\0' || s[i] == ',') return i;
    if (s[i] == '\\' && s[i + 1] != '\0') i += 2; else i += 1;
  }
}
// A prefix is an optional '+' or '-' flag followed by one of D X A E W I N C Z G O P Q.
static int ref_is_flag(char c) { return c == '+' || c == '-'; }
static int ref_is_prefix(char c) {
  const char *k = "DXAEWINCZGOPQ";
  for (int i = 0; i < 13; i++) if (k[i] == c) return 1;
  return 0;
}
