#!/usr/bin/env python3
"""mutate.py <in> <out> <from> <to>: replace the first <from> (\\n = newline) or exit 2."""
import sys
t = open(sys.argv[1]).read()
f, to = (s.replace("\\n", "\n") for s in sys.argv[3:5])
if f not in t:
    sys.exit(2)
open(sys.argv[2], "w").write(t.replace(f, to, 1))
