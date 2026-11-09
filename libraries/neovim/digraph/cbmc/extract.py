#!/usr/bin/env python3
"""Verbatim extraction of digraph.c pieces, pinned by sha256 of each extracted span."""
import hashlib, re, sys
src = open(sys.argv[1]).read().split('\n')
def span(a, b):  # 1-based inclusive line numbers
    return '\n'.join(src[a-1:b]) + '\n'
def func(name):
    i = next(n for n, l in enumerate(src) if re.match(r'^(static )?(int|bool|void) %s\(' % name, l))
    j = next(n for n in range(i, len(src)) if src[n] == '}')
    return span(i+1, j+1)
parts = {
  'table': span(62, 1465),
  'getexactdigraph': func('getexactdigraph'),
  'digraph_get': func('digraph_get'),
  'check_digraph_chars_valid': func('check_digraph_chars_valid'),
  'registerdigraph': func('registerdigraph'),
}
PINS = dict(l.split() for l in open(sys.argv[3]).read().split('\n') if l.strip()) if len(sys.argv) > 3 else {}
out = open(sys.argv[2], 'w')
for k, v in parts.items():
    h = hashlib.sha256(v.encode()).hexdigest()
    if PINS and PINS.get(k) != h: sys.exit('pin mismatch for %s: %s' % (k, h))
    print(k, h)
    out.write('// ---- %s (verbatim, sha256 %s)\n' % (k, h))
    out.write(v.replace('FUNC_ATTR_PURE', '').replace('FUNC_ATTR_NONNULL_ALL', ''))
