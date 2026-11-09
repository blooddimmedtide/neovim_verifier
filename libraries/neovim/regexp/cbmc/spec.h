// Independent reference for regexp.c's hex and octal readers, written from the
// documented meaning (hex digits 0-9 a-f A-F; "\%o" reads at most 3 octal digits
// and stops before a digit that would take the value past 0377), not from the code.
#include <stdint.h>

static int spec_hexdigit(unsigned char c) {   // value of a hex digit, or -1
  switch (c) {
  case '0': return 0; case '1': return 1; case '2': return 2; case '3': return 3;
  case '4': return 4; case '5': return 5; case '6': return 6; case '7': return 7;
  case '8': return 8; case '9': return 9;
  case 'a': case 'A': return 10; case 'b': case 'B': return 11; case 'c': case 'C': return 12;
  case 'd': case 'D': return 13; case 'e': case 'E': return 14; case 'f': case 'F': return 15;
  default: return -1;
  }
}

static int spec_octdigit(unsigned char c) {   // value of an octal digit, or -1
  return (c >= '0' && c <= '7') ? c - '0' : -1;
}
