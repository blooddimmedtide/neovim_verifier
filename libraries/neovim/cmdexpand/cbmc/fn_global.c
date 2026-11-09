static const char *find_cmd_after_global_cmd(const char *arg)
{
  const int delim = (uint8_t)(*arg);  // Get the delimiter.
  if (delim) {
    arg++;  // Skip delimiter if there is one.
  }

  while (arg[0] != NUL && (uint8_t)arg[0] != delim) {
    if (arg[0] == '\\' && arg[1] != NUL) {
      arg++;
    }
    arg++;
  }
  if (arg[0] != NUL) {
    return arg + 1;
  }

  return NULL;
}
