# Sanitizer fuzzing for regexp.c, search.c and fuzzy.c

1. Build Neovim's dependencies and an ASan + UBSan build of `nvim_bin` whose objects also
   carry libFuzzer coverage (`-fsanitize=fuzzer-no-link` added to the nvim_bin objects only;
   the build-time Lua module must stay uninstrumented). See the thread notes for the exact
   cmake lines; GitHub archive downloads may need to be replaced by `git clone` tarballs
   (`-D<DEP>_URL=file://...` with `-DDEPS_IGNORE_SHA=ON`).
2. `bash build.sh <build dir> fuzz_regexp.c fuzz_regexp` (same for `fuzz_search.c`). It links
   the harness with every nvim_bin object except main.c, plus `main_shim.c`, which includes
   main.c with `main` renamed so the harness can call `early_init()`.
3. Run, for example:
   `FUZZ_SKIP_COMPOSING=1 FUZZ_SKIP_LONGNUM=1 FUZZ_SKIP_BSMB=1 ./fuzz_regexp -dict=dict.txt -max_len=512 -timeout=20 -rss_limit_mb=3000 -malloc_limit_mb=1000 corpus`
   The `FUZZ_SKIP_*` switches silence findings already recorded in `../../findings/`
   (composing characters, 19+ digit numbers, backslash before a multibyte character).

Seeds: the `[pattern, text]` pairs from `test/old/testdir/test_regexp*.vim` and
`test_search*.vim`.
