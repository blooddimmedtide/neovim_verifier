static int buf_time_compare(const void *s1, const void *s2)
{
  buf_T *buf1 = *(buf_T **)s1;
  buf_T *buf2 = *(buf_T **)s2;

  if (buf1->b_last_used == buf2->b_last_used) {
    return 0;
  }
  return buf1->b_last_used > buf2->b_last_used ? -1 : 1;
}
