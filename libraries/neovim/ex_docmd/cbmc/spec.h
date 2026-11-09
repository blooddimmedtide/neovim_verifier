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

// skipdigits: index of the first character that is not '0'..'9'.
static int ref_skipdigits(const char *s) {
  int i = 0;
  for (; s[i] >= '0' && s[i] <= '9'; i++) {}
  return i;
}

// modifier_len: the command modifiers of Vim's ":help :command-modifiers" (written out
// here from the help text, not copied from cmdmods[]): full name, shortest abbreviation
// from the "[...]" brackets, and whether a count may come first (":[N]tab", ":[N]verbose").
static const struct { const char *name; int min; bool count; } ref_mods[] = {
  {"aboveleft", 3, 0}, {"belowright", 3, 0}, {"botright", 2, 0}, {"browse", 3, 0},
  {"confirm", 4, 0}, {"filter", 4, 0}, {"hide", 3, 0}, {"horizontal", 3, 0},
  {"keepalt", 5, 0}, {"keepjumps", 5, 0}, {"keepmarks", 3, 0}, {"keeppatterns", 5, 0},
  {"leftabove", 5, 0}, {"lockmarks", 3, 0}, {"noautocmd", 3, 0}, {"noswapfile", 3, 0},
  {"rightbelow", 6, 0}, {"sandbox", 3, 0}, {"silent", 3, 0}, {"tab", 3, 1},
  {"topleft", 2, 0}, {"unsilent", 3, 0}, {"verbose", 4, 1}, {"vertical", 4, 0},
};
// A modifier word is the run of letters at the start (after "N" and blanks for a count).
// It names modifier m when it is an abbreviation of m's name at least m.min long.
// Result: length of count + blanks + word, or 0 when no modifier is named.
static int ref_modifier_len(const char *s) {
  int off = 0;
  bool counted = false;
  if (s[0] >= '0' && s[0] <= '9') {
    off = ref_skipdigits(s);
    off += ref_skipwhite(s + off);
    counted = true;
  }
  const char *w = s + off;
  int L = 0;
  while ((w[L] >= 'a' && w[L] <= 'z') || (w[L] >= 'A' && w[L] <= 'Z')) L++;
  for (int m = 0; m < (int)(sizeof ref_mods / sizeof ref_mods[0]); m++) {
    if (counted && !ref_mods[m].count) continue;
    if (L < ref_mods[m].min) continue;
    int k = 0;
    while (k < L && ref_mods[m].name[k] == w[k]) k++;
    if (k == L) return off + L;  // w[0..L) is a prefix of the name (name has no NUL before L)
  }
  return 0;
}
