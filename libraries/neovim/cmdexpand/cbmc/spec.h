// Independent reference for find_cmd_after_global_cmd, written from the documented meaning of
// ":g/pat/cmd": the first character is the delimiter; the pattern runs to the next delimiter that
// is not escaped by a backslash; the command starts right after it. No closing delimiter -> NULL.
// A delimiter at index j (j >= 1) is escaped when an odd number of backslashes, all at indices
// >= 1, immediately precede it. When the delimiter is itself a backslash it cannot be escaped.
static long ref_global(const char *s, long len)
{
  if (len == 0) return -1;
  char d = s[0];
  for (long j = 1; j < len; j++) {
    if (s[j] != d) continue;
    if (d == '\\') return j + 1;
    long run = 0;
    for (long k = j - 1; k >= 1 && s[k] == '\\'; k--) run++;
    if (run % 2 == 0) return j + 1;
  }
  return -1;
}
