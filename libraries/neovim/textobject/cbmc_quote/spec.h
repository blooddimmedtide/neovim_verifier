// Reference for find_next_quote / find_prev_quote, from their doc comments and
// :help 'quoteescape': a quote preceded by an odd number of escape characters
// is escaped and does not count; an escape character escapes the one after it.
#include <stdbool.h>
#include <string.h>
static bool is_esc(const char *escape, char c) { return escape && c && strchr(escape, c); }
// Forward: column of the first unescaped quotechar at or after col, -1 if none.
// An escape char at position i makes i+1 literal.
static int ref_next(const char *line, int col, int q, const char *escape) {
  for (int i = col; line[i]; i++) {
    if (is_esc(escape, line[i])) { i++; if (!line[i]) return -1; continue; }
    if ((unsigned char)line[i] == (unsigned)q) return i;
  }
  return -1;
}
// Backward: the largest j < col with line[j] == quotechar and an even number of
// escape chars right before j; 0 when there is none (the doc: "found column or zero").
static int ref_prev(const char *line, int col, int q, const char *escape) {
  for (int j = col - 1; j >= 0; j--) {
    if ((unsigned char)line[j] != (unsigned)q) continue;
    int n = 0;
    while (j - n > 0 && is_esc(escape, line[j - n - 1])) n++;
    if (n % 2 == 0) return j;
  }
  return 0;
}
