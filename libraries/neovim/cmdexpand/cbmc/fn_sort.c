static int sort_func_compare(const void *s1, const void *s2)
{
  char *p1 = *(char **)s1;
  char *p2 = *(char **)s2;

  if (*p1 != '<' && *p2 == '<') {
    return -1;
  }
  if (*p1 == '<' && *p2 != '<') {
    return 1;
  }
  return strcmp(p1, p2);
}
