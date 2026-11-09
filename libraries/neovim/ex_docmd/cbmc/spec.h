// Independent references, written from the documentation comments in ex_docmd.c /
// charset.c and Vim's :help cmdline-lines, not from the function bodies.
// Each returns an index (or -1 for "no result") into a NUL-terminated string s.

static bool sp_blank(char c) { return c == ' ' || c == '\t'; }  // :help white-space

// skipwhite: index of the first character that is not a space or tab.
static int ref_skipwhite(const char *s) {
  int i = 0;
  for (; sp_blank(s[i]); i++) {}
  return i;
}

// ends_excmd: a character ends an Ex command iff it is NUL, '|', '"' (comment) or '\n'.
static bool ref_ends_excmd(int c) { return c == 0 || c == '|' || c == '"' || c == '\n'; }

// find_nextcmd: the next command starts right after the first '|' or '\n';
// -1 (NULL) when the string has neither.
static int ref_find_nextcmd(const char *s) {
  for (int i = 0; s[i] != 0; i++) {
    if (s[i] == '|' || s[i] == '\n') return i + 1;
  }
  return -1;
}

// check_nextcmd: after optional blanks, a '|' or '\n' separator gives the index
// just past it; anything else gives -1 (NULL).
static int ref_check_nextcmd(const char *s) {
  int i = ref_skipwhite(s);
  return (s[i] == '|' || s[i] == '\n') ? i + 1 : -1;
}

// skip_colon_white: skip the colons that may precede a command and the blanks after
// each one ("::  :cmd"); with lead, blanks before the first colon too. The skipped
// prefix is the longest one made of ':' and blanks that (without lead) is empty or
// starts with ':'.
static int ref_skip_colon_white(const char *s, bool lead) {
  if (!lead && s[0] != ':') return 0;
  int i = 0;
  for (; s[i] == ':' || sp_blank(s[i]); i++) {}
  return i;
}

// checkforcmd: "pp" names command "cmd" when it starts with a prefix of "cmd" at least
// "len" characters long, taken as long as it matches, and the next character is not a
// letter (an abbreviation followed by its argument). On a match the result is the
// index of the argument after blanks; otherwise -1 and "pp" is unchanged.
static int ref_checkforcmd(const char *p, const char *cmd, int len) {
  int k = 0;
  while (cmd[k] != 0 && p[k] == cmd[k]) k++;
  char next = p[k];
  bool letter = (next >= 'A' && next <= 'Z') || (next >= 'a' && next <= 'z');
  if (k >= len && !letter) return k + ref_skipwhite(p + k);
  return -1;
}
