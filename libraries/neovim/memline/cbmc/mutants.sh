#!/bin/bash
# Planted bugs for long_to_char / char_to_long; each must make CBMC fail. Exit 0 = all caught.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); W=$(mktemp -d); bad=0
python3 -I "$HERE/build.py" "$1" "$W/b0.c" || exit 1
M=("  s[3] = (uint8_t)(n & 0xff);@@  s[3] = (uint8_t)(n & 0x7f);"
   "  retval |= s[2];@@  retval |= s[1];"
   "  long retval = s[3];@@  long retval = (int8_t)s[3];"
   "  s[1] = (uint8_t)(n & 0xff);@@  s[1] = (uint8_t)(n >> 1 & 0xff);"
   "b0:  return b0p->b0_id[0] == BLOCK0_ID0 && b0p->b0_id[1] == BLOCK0_ID1;@@  return b0p->b0_id[0] == BLOCK0_ID0;"
   "b0:         || b0p->b0_magic_short != (int16_t)B0_MAGIC_SHORT@@         || b0p->b0_magic_short != (int16_t)B0_MAGIC_INT"
   "b0:          && memchr(b0p->b0_hname, NUL, B0_HNAME_SIZE)@@          && memchr(b0p->b0_hname, NUL, B0_HNAME_SIZE + 1)"
   "b0:          && memchr(b0p->b0_fname, NUL, B0_FNAME_SIZE_CRYPT));@@          && memchr(b0p->b0_fname, NUL, B0_FNAME_SIZE_ORG));")
for m in "${M[@]}"; do
  h=harness; case $m in b0:*) h=harness_b0; m=${m#b0:};; esac
  from=${m%%@@*}; to=${m#*@@}
  python3 -I - "$W/b0.c" "$W/m.c" "$from" "$to" <<'PY'
import sys; s=open(sys.argv[1]).read(); assert s.count(sys.argv[3])==1, sys.argv[3]
open(sys.argv[2],"w").write(s.replace(sys.argv[3],sys.argv[4]))
PY
  cat "$W/m.c" "$HERE/$h.c" > "$W/all.c"
  if cbmc "$W/all.c" --bounds-check --pointer-check --unwinding-assertions --unwind 901 2>&1 | grep -q "VERIFICATION SUCCESSFUL"; then
    echo "SURVIVED: $to"; bad=1; else echo "caught: $to"; fi
done
exit $bad
