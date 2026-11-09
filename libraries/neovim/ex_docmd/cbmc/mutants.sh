#!/bin/bash
# Planted bugs in the extracted code; each must make its harness fail.
# Usage: bash mutants.sh   (after run.sh has written upstream.c)
cd "$(dirname "$0")"
fail=0
m() {  # name harness sed-expression
  n=${4:-8}
  sed "$3" upstream.c > mut.c
  grep -q . <(diff upstream.c mut.c) || { echo "$1: mutation did not apply"; fail=1; return; }
  sed 's/#include "upstream.c"/#include "mut.c"/' harness.c > mut_h.c
  out=$(cbmc mut_h.c -DN=$n --function h_$2 --bounds-check --pointer-check --unwind 30 --unwinding-assertions 2>&1 | tail -1)
  [ "$out" = "VERIFICATION FAILED" ] && echo "$1: caught" || { echo "$1: MISSED"; fail=1; }
}
m tab_not_white      skipwhite        's/return c == .*\\t.; }/return c == '"' '"'; }/'
m ends_no_comment    ends_excmd       "s/|| c == '\"' //"
m ends_no_newline    ends_excmd       "s/|| c == '\\\\n';/;/"
m find_no_newline    find_nextcmd     "s/while (\*p != '|' \&\& \*p != '\\\\n')/while (*p != '|')/"
m find_off_by_one    find_nextcmd     's/return (char \*)p + 1;/return (char *)p;/'
m check_no_skip      check_nextcmd    's/char \*s = skipwhite(p);/char *s = p;/'
m check_newline      check_nextcmd    "s/if (\*s == '|' || \*s == '\\\\n')/if (*s == '|')/"
m colon_no_lead      skip_colon_white 's/if (skipleadingwhite) {/if (0) {/'
m colon_no_white     skip_colon_white 's/p = skipwhite(p + 1);/p = p + 1;/'
m cmd_len_gt         checkforcmd      's/if (i >= len \&\&/if (i > len \&\&/'
m cmd_no_alpha       checkforcmd      's/ \&\& !ASCII_ISALPHA((\*pp)\[i\])//'
m cmd_no_skip        checkforcmd      's/\*pp = skipwhite(\*pp + i);/*pp = *pp + i;/'
m digits_off         skipdigits       "s/while (ascii_isdigit(\*p)) {/while (ascii_isdigit(*p) \&\& *p != '9') {/"
m mod_minlen         modifier_len     's/if (j >= cmdmods\[i\].minlen/if (j > cmdmods[i].minlen/'
m mod_no_count_flag  modifier_len     's/ \&\& (p == cmd || cmdmods\[i\].has_count))/)/'
m mod_no_alpha       modifier_len     's/        \&\& !ASCII_ISALPHA(p\[j\])//'
m mod_table_minlen   modifier_len     's/{ "verbose", 4, true }/{ "verbose", 3, true }/'
m mod_table_count    modifier_len     's/{ "tab", 3, true }/{ "tab", 3, false }/'
m mod_bad_break      modifier_len     's/if (cmdmods\[i\].name\[0\] > \*p) {/if (cmdmods[i].name[0] >= *p) {/'
rm -f mut.c mut_h.c
exit $fail
