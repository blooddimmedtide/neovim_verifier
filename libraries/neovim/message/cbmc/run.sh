#!/bin/sh
# Re-run the trunc_string checks. Expect: memsafety PASS (both signednesses), buflen0 FAIL (finding).
set -u
cd "$(dirname "$0")"
sha256sum -c trunc_string.c.sha256 || exit 1
O="--bounds-check --pointer-check --signed-overflow-check --unwind 5 --unwinding-assertions"
cbmc harness.c -DSN=3 -DBN=3 -DMINBUF=1 -DCHECKSPEC=0 $O | tail -1
cbmc harness.c -DSN=3 -DBN=3 -DMINBUF=1 -DCHECKSPEC=0 --unsigned-char $O | tail -1
cbmc harness.c -DSN=3 -DBN=3 -DMINBUF=0 -DCHECKSPEC=0 $O | tail -1
