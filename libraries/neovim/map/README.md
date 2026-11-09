# src/nvim/map.c and src/klib/kvec.h (in progress)

Claimed for Frama-C WP verification: the hash map/set core in `src/nvim/map.c`
(`mh_realloc`, `mh_clear`, the key-generic `map_key_impl.c.h` functions, the
value-generic `map_value_impl.c.h` functions, `pmap_del2`) and the kvec helpers in
`src/klib/kvec.h` (`_memcpy_free` and the `kv_*` macros as instantiated).
Pinned upstream: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd. Status: see STATUS.md in this folder.
