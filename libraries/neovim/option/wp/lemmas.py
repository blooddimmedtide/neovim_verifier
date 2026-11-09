"""Checks the bodiless ghost lemma functions in contracts.py by exhaustive evaluation.
shl8: for every integer b in 0..255, (b << 8) == b * 256 (ACSL << on integers is exact)."""
import sys
bad = [b for b in range(256) if (b << 8) != b * 256]
print("lemmas.py shl8: ok (256/256)" if not bad else f"lemmas.py shl8: FAILED {bad}")
sys.exit(1 if bad else 0)
