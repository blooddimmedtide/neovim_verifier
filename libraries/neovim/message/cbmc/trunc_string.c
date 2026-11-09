void trunc_string(const char *s, char *buf, int room_in, int buflen)
{
  int room = room_in - 3;  // "..." takes 3 chars
  int len = 0;
  int e;
  int i;
  int n;

  if (*s == NUL) {
    if (buflen > 0) {
      *buf = NUL;
    }
    return;
  }

  if (room_in < 3) {
    room = 0;
  }
  int half = room / 2;

  // First part: Start of the string.
  for (e = 0; len < half && e < buflen; e++) {
    if (s[e] == NUL) {
      // text fits without truncating!
      buf[e] = NUL;
      return;
    }
    n = ptr2cells(s + e);
    if (len + n > half) {
      break;
    }
    len += n;
    buf[e] = s[e];
    for (n = utfc_ptr2len(s + e); --n > 0;) {
      if (++e == buflen) {
        break;
      }
      buf[e] = s[e];
    }
  }

  // Last part: End of the string.
  half = i = (int)strlen(s);
  while (true) {
    half = half - utf_head_off(s, s + half - 1) - 1;
    n = ptr2cells(s + half);
    if (len + n > room || half == 0) {
      break;
    }
    len += n;
    i = half;
  }

  if (i <= e + 3) {
    // text fits without truncating
    if (s != buf) {
      len = (int)strlen(s);
      if (len >= buflen) {
        len = buflen - 1;
      }
      len = len - e + 1;
      if (len < 1) {
        buf[e - 1] = NUL;
      } else {
        memmove(buf + e, s + e, (size_t)len);
      }
    }
  } else if (e + 3 < buflen) {
    // set the middle and copy the last part
    memmove(buf + e, "...", 3);
    len = (int)strlen(s + i) + 1;
    if (len >= buflen - e - 3) {
      len = buflen - e - 3 - 1;
    }
    memmove(buf + e + 3, s + i, (size_t)len);
    buf[e + 3 + len - 1] = NUL;
  } else {
    // can't fit in the "...", just truncate it
    buf[buflen - 1] = NUL;
  }
}
