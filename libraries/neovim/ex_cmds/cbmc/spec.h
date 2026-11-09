// Independent reference for :substitute's [flags] (":help s_flags", ":help :s_c").
// Written from the documentation: '&' first keeps the previous flags, otherwise the defaults
// are g='gdefault', no c, e on (errors reported), no p/l/#/n, case from options.
// g, c and e toggle; n counts only; r selects the last used pattern; p prints; # prints with
// number; l prints like :list; i ignores case; I matches case. Parsing stops at the first other
// character. The reference decides itself that 'n' wins over 'c' (count-only never asks), as
// documented under [n]: "Report the number of matches, do not actually substitute."
#include <stdbool.h>
typedef struct { bool all, ask, count, error, print, list, number; int ic; } ref_flags;
static inline const char *ref_parse(const char *cmd, ref_flags *f, int *which, bool gdefault,
                                    int re_last, int ic_honor, int ic_ignore, int ic_match)
{
  const char *p = cmd;
  if (*p == '&') { p++; }
  else { *f = (ref_flags){ .all = gdefault, .error = true, .ic = ic_honor }; }
  for (;; p++) {
    switch (*p) {
    case 'g': f->all = !f->all; continue;
    case 'c': f->ask = !f->ask; continue;
    case 'n': f->count = true; continue;
    case 'e': f->error = !f->error; continue;
    case 'r': *which = re_last; continue;
    case 'p': f->print = true; continue;
    case '#': f->print = f->number = true; continue;
    case 'l': f->print = f->list = true; continue;
    case 'i': f->ic = ic_ignore; continue;
    case 'I': f->ic = ic_match; continue;
    }
    break;
  }
  if (f->count) { f->ask = false; }
  return p;
}
