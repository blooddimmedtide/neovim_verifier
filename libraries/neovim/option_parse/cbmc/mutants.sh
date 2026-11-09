#!/bin/sh
# Plant bugs in extracted.c one at a time; each must make CBMC fail.
run() { cbmc harness.c -DN=9 --bounds-check --pointer-check --unwind 11 --unwinding-assertions >/dev/null 2>&1 && echo "SURVIVED: $1" || echo "caught: $1"; }
cp extracted.c extracted.orig
m() { cp extracted.orig extracted.c; sed -i "$2" extracted.c; cmp -s extracted.c extracted.orig && echo "NOOP: $1" || run "$1"; }
m op-plus      "s/== '+'/== '*'/"
m op-eq        "s/\*(arg + 1) == '='/*(arg + 1) != '='/"
m op-nulchk    "s/\*arg != NUL \&\& //"
m op-swap      "s/op = OP_PREPENDING; /op = OP_REMOVING; /"
m pre-no2      's/argp += 2;/argp += 1;/'
m pre-inv3     's/"inv", 3/"inv", 2/'
m pre-noret    's/return PREFIX_NO;/return PREFIX_NONE;/'
m tty-term     's/sizeof("term") - 1/sizeof("term")/'
m tty-p3       's/p\[2\] \&\& p\[3\]/p[2]/'
m tty-p4       's/p += 4;/p += 3;/'
m tty-gt       "s/\*p != '>') {/*p == '<') {/"
m tty-eqnull   's/arg == p ? NULL : p/p/'
m tty-isnot     's/!= NULL;/== NULL;/'
m foe-notalpha  's/if (!ASCII_ISALPHA(\*p)) {/if (!ASCII_ISLOWER(*p)) {/'
m foe-loop      's/while (ASCII_ISALPHA(\*p)) {/while (*p \&\& *p != 0x20) {/'
m foe-len       's/(size_t)(p - arg))/(size_t)(p - arg) - 1)/'
m foe-ttyidx    '0,/\*opt_idxp = kOptInvalid;/s//*opt_idxp = 0;/'
cp extracted.orig extracted.c; rm extracted.orig
