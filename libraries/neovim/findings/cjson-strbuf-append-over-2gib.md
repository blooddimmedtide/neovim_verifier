# strbuf_append_string overflows an int index on strings of 2 GiB or more

File: `src/cjson/strbuf.c`, `strbuf_append_string`, Neovim commit 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
(vendored lua-cjson; the same code is in upstream lua-cjson 2.1).

```c
void strbuf_append_string(strbuf_t *s, const char *str)
{
    int i;
    ...
    for (i = 0; str[i]; i++) {
```

`i` indexes a NUL-terminated string of any length, but it is an `int`. For a string longer than
`INT_MAX` bytes, `i++` overflows: undefined behaviour. In practice `i` wraps to `INT_MIN` and the
loop reads `str[-2147483648]`, 2 GiB before the string.

## Reproduce

```
gcc -O1 -g -fsanitize=undefined -fno-sanitize-recover=undefined -I src/cjson \
    cjson-strbuf-append-over-2gib-repro.c src/cjson/strbuf.c -o big && ./big
src/cjson/strbuf.c:185:26: runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'
```

With the fix: `length 2147483649 (want 2147483649)`.

## Reachability

`lua_cjson.c` calls it with the escape strings (`escstr`, a few bytes) and with the `indent`
option of `vim.json.encode()` (`json_append_newline_and_indent`). An indent string of 2 GiB is
needed, which LuaJIT cannot make (its strings stop just below 2 GiB); a PUC Lua build can. So this
is not reachable from a default Neovim build today, but the function is wrong for valid input.

## Fix

`size_t i` (fork branch `claude/project-thread-gritim` of blooddimmedtide/verified_neovim, commit
"fix(cjson): strbuf_append_string on strings of 2 GiB or more"). Proved for every string in
`../cjson_strbuf/` (see its CLAIM.md for what is proved and how).
