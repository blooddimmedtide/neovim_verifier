static int bytes2offset(char **pp)
{
  uint8_t *p = (uint8_t *)(*pp);
  int nr;

  int c = *p++;
  if ((c & 0x80) == 0x00) {             // 1 byte
    nr = c - 1;
  } else if ((c & 0xc0) == 0x80) {      // 2 bytes
    nr = (c & 0x3f) - 1;
    nr = nr * 255 + (*p++ - 1);
  } else if ((c & 0xe0) == 0xc0) {      // 3 bytes
    nr = (c & 0x1f) - 1;
    nr = nr * 255 + (*p++ - 1);
    nr = nr * 255 + (*p++ - 1);
  } else {                              // 4 bytes
    nr = (c & 0x0f) - 1;
    nr = nr * 255 + (*p++ - 1);
    nr = nr * 255 + (*p++ - 1);
    nr = nr * 255 + (*p++ - 1);
  }

  *pp = (char *)p;
  return nr;
}
