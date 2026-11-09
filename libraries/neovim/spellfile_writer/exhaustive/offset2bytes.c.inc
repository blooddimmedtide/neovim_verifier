static int offset2bytes(int nr, char *buf_in)
{
  uint8_t *buf = (uint8_t *)buf_in;

  // Split the number in parts of base 255.  We need to avoid NUL bytes.
  int b1 = nr % 255 + 1;
  int rem = nr / 255;
  int b2 = rem % 255 + 1;
  rem = rem / 255;
  int b3 = rem % 255 + 1;
  int b4 = rem / 255 + 1;

  if (b4 > 1 || b3 > 0x1f) {    // 4 bytes
    buf[0] = (uint8_t)(0xe0 + b4);
    buf[1] = (uint8_t)b3;
    buf[2] = (uint8_t)b2;
    buf[3] = (uint8_t)b1;
    return 4;
  }
  if (b3 > 1 || b2 > 0x3f) {   // 3 bytes
    buf[0] = (uint8_t)(0xc0 + b3);
    buf[1] = (uint8_t)b2;
    buf[2] = (uint8_t)b1;
    return 3;
  }
  if (b2 > 1 || b1 > 0x7f) {   // 2 bytes
    buf[0] = (uint8_t)(0x80 + b2);
    buf[1] = (uint8_t)b1;
    return 2;
  }
  // 1 byte
  buf[0] = (uint8_t)b1;
  return 1;
}
