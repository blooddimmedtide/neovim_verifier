static char *get_retab_arg(expand_T *xp FUNC_ATTR_UNUSED, int idx)
{
  if (idx == 0) {
    return "-indentonly";
  }
  return NULL;
}
static char *get_messages_arg(expand_T *xp FUNC_ATTR_UNUSED, int idx)
{
  if (idx == 0) {
    return "clear";
  }
  return NULL;
}
static char *get_mapclear_arg(expand_T *xp FUNC_ATTR_UNUSED, int idx)
{
  if (idx == 0) {
    return "<buffer>";
  }
  return NULL;
}
