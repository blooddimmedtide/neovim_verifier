static set_op_T get_op(const char *arg)
{
  set_op_T op = OP_NONE;
  if (*arg != NUL && *(arg + 1) == '=') {
    if (*arg == '+') {
      op = OP_ADDING;          // "+="
    } else if (*arg == '^') {
      op = OP_PREPENDING;      // "^="
    } else if (*arg == '-') {
      op = OP_REMOVING;        // "-="
    }
  }
  return op;
}
static set_prefix_T get_option_prefix(char **argp)
{
  if (strncmp(*argp, "no", 2) == 0) {
    *argp += 2;
    return PREFIX_NO;
  } else if (strncmp(*argp, "inv", 3) == 0) {
    *argp += 3;
    return PREFIX_INV;
  }

  return PREFIX_NONE;
}
static const char *find_tty_option_end(const char *arg)
{
  if (strequal(arg, "term")) {
    return arg + sizeof("term") - 1;
  } else if (strequal(arg, "ttytype")) {
    return arg + sizeof("ttytype") - 1;
  }

  const char *p = arg;
  bool delimit = false;  // whether to delimit <

  if (arg[0] == '<') {
    // look out for <t_>;>
    delimit = true;
    p++;
  }
  if (p[0] == 't' && p[1] == '_' && p[2] && p[3]) {
    // "t_xx" ("t_Co") option.
    p += 4;
  } else if (delimit) {
    // Search for delimiting >.
    while (*p != NUL && *p != '>') {
      p++;
    }
  }
  // Return NULL when delimiting > is not found.
  if (delimit) {
    if (*p != '>') {
      return NULL;
    }
    p++;
  }

  return arg == p ? NULL : p;
}
bool is_tty_option(const char *name)
  FUNC_ATTR_NONNULL_ALL FUNC_ATTR_PURE FUNC_ATTR_WARN_UNUSED_RESULT
{
  return find_tty_option_end(name) != NULL;
}
const char *find_option_end(const char *arg, OptIndex *opt_idxp)
{
  const char *p;

  // Handle TTY and keycode options separately.
  if ((p = find_tty_option_end(arg)) != NULL) {
    *opt_idxp = kOptInvalid;
    return p;
  } else {
    p = arg;
  }

  if (!ASCII_ISALPHA(*p)) {
    *opt_idxp = kOptInvalid;
    return NULL;
  }
  while (ASCII_ISALPHA(*p)) {
    p++;
  }

  *opt_idxp = find_option_len(arg, (size_t)(p - arg));
  return p;
}
