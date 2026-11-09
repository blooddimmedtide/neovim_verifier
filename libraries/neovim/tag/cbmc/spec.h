// Independent references, written from the documented meaning of each helper
// (tags file format: "<tagname>TAB<filename>TAB<command>", see :help tags-file-format),
// using indices only, not the upstream pointer code.
static size_t spec_index_of(const char *s, size_t from, size_t n, char c)
{ // first i >= from, i < n, with s[i] == c; n if none (s has n bytes, s[n-1] == 0)
  for (size_t i = from; i < n; i++) if (s[i] == c) return i;
  return n;
}
static int spec_upper(unsigned char c) { return (c >= 'a' && c <= 'z') ? c - 32 : c; }
