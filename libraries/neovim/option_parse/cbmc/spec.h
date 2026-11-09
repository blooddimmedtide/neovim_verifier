// Independent reference, written from :help set-args / :help t_xx and the doc comments,
// using index arithmetic on the length-n buffer (s[n-1] == NUL, earlier NULs allowed).
static size_t ref_len(const char *s, size_t n) { size_t i = 0; while (i < n && s[i]) i++; return i; }

// ":set opt+=v" / "^=" / "-=": operator is the two characters at arg, else none.
static set_op_T ref_get_op(const char *s, size_t n)
{
  size_t L = ref_len(s, n);
  if (L < 2 || s[1] != '=') return OP_NONE;
  return s[0] == '+' ? OP_ADDING : s[0] == '^' ? OP_PREPENDING : s[0] == '-' ? OP_REMOVING : OP_NONE;
}

// ":set noopt" / ":set invopt": a leading "no" wins over "inv"; else no prefix, nothing skipped.
static set_prefix_T ref_prefix(const char *s, size_t n, size_t *adv)
{
  size_t L = ref_len(s, n);
  if (L >= 2 && s[0] == 'n' && s[1] == 'o') { *adv = 2; return PREFIX_NO; }
  if (L >= 3 && s[0] == 'i' && s[1] == 'n' && s[2] == 'v') { *adv = 3; return PREFIX_INV; }
  *adv = 0; return PREFIX_NONE;
}

// End offset of a terminal option name at s, or -1 if none:
//  whole string "term" / "ttytype"           -> its length
//  "t_" + two non-NUL chars                  -> 4
//  "<t_" + two non-NUL chars + ">"           -> 6   (no '>' there -> -1)
//  "<" ... first ">" (not a t_xx form)       -> one past that '>'  (no '>' -> -1)
//  anything else                             -> -1
static long ref_tty_end(const char *s, size_t n)
{
  size_t L = ref_len(s, n);
  if ((L == 4 && !memcmp(s, "term", 4)) || (L == 7 && !memcmp(s, "ttytype", 7))) return (long)L;
  if (L >= 1 && s[0] == '<') {
    if (L >= 5 && s[1] == 't' && s[2] == '_') return (L >= 6 && s[5] == '>') ? 6 : -1;
    for (size_t i = 1; i < L; i++) if (s[i] == '>') return (long)i + 1;
    return -1;
  }
  if (L >= 4 && s[0] == 't' && s[1] == '_') return 4;
  return -1;
}

// Length of the leading run of ASCII letters A-Z / a-z (option names).
static size_t ref_alpha_run(const char *s, size_t n)
{
  size_t i = 0;
  while (i < n && ((s[i] >= 'a' && s[i] <= 'z') || (s[i] >= 'A' && s[i] <= 'Z'))) i++;
  return i;
}
