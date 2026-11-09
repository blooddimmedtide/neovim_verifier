# spellfile.c offset2bytes: silent wrong encoding for nr >= 248,720,625

Pinned commit 7b87ce8. `offset2bytes` (writer of `.sug` `<sugnr>`) and its reader `bytes2offset`
(spellsuggest.c) agree only for 0 <= nr < 15*255^3. Above that the 4-byte lead `0xe0 + b4` has
b4 >= 16, the reader masks `c & 0x0f`, and a different number is read back; at b4 >= 32 the
`(uint8_t)` cast wraps the lead byte. Negative nr yields NUL bytes in 8,421,505 cases, ending a
`<sugline>` early. Data integrity only; no out-of-bounds access (checked with UBSan, exhaustive).
Reproducer: `spellfile_writer/exhaustive/run.sh`. Reachability (word lists of 248M+ words, or a
negative gap in sug_filltable) not established. Upstream issue: not drafted for filing yet.
