"""Tool patches: exact text replacements applied before annotation (none change meaning).

Frama-C 33 WP assumes every byte of a string literal is 0 (see
verification-notes/toolchain-bugs/framac33-wp-string-init.md; here it shows up for the
literals passed to strncmp in path_is_url). Each literal becomes the compound literal
with the same bytes, which C11 6.4.5p6 says the string literal is; ../equiv/literals.c
checks the bytes are equal with gcc.
"""
PATCHES = {
"has_env_var": [('vim_strchr("$", ', "vim_strchr(vp_dollar, ")],  # brace-initialized array, see build.py prelude
"path_is_url": [
    ('strncmp(p, ":/", 2)', "strncmp(p, (const char[]){':', '/', '\\0'}, 2)"),
    ('strncmp(p, ":\\\\\\\\", 3)', "strncmp(p, (const char[]){':', '\\\\', '\\\\', '\\0'}, 3)"),
],
}
