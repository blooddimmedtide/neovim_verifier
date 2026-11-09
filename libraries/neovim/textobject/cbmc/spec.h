// Independent reference for inmacro(), written from its documentation and the
// meaning of 'sections' / 'paragraphs' (:help 'sections'): the option is a list
// of two-character nroff macro names; a space in a name matches a space in the
// line or the end of the line. The line s is a NUL-terminated string.
// Reference decision: when the line has ended (s[0] == NUL) there is no second
// character, so only a space (or the end of the option) matches it. Nothing
// past the line's NUL is read.
#include <stdbool.h>
static bool ref_inmacro(const char *opt, const char *s) {
  bool e0 = s[0] == '\0';
  bool e1 = e0 || s[1] == '\0';
  for (const char *p = opt; p[0] != '\0'; p += 2) {
    bool first = !e0 ? (p[0] == s[0] || (p[0] == ' ' && s[0] == ' ')) : p[0] == ' ';
    // Second character: equal to the line's second character (which exists
    // only if the line has not ended), or a space/end of option against a
    // space or the end of the line.
    bool blank = p[1] == ' ' || p[1] == '\0';
    bool second = (!e0 && p[1] == s[1]) || (blank && (e1 || s[1] == ' '));
    if (first && second) return true;
    if (p[1] == '\0') return false;
  }
  return false;
}
