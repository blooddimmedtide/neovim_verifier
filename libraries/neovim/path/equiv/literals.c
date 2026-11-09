// The tool patch in ../wp/tool_patches.py swaps path_is_url's string literals (and the
// prelude's PATHSEPSTR) for compound literals. This checks both spell the same bytes, terminator included.
// Run: gcc -std=c11 -Wall -Werror literals.c -o literals && ./literals
#include <stdio.h>
#include <string.h>
int main(void)
{
  int bad = 0;
  bad |= sizeof(":/") != sizeof((const char[]){':', '/', '\0'})
         || memcmp(":/", (const char[]){':', '/', '\0'}, sizeof(":/")) != 0;
  bad |= sizeof(":\\\\") != sizeof((const char[]){':', '\\', '\\', '\0'})
         || memcmp(":\\\\", (const char[]){':', '\\', '\\', '\0'}, sizeof(":\\\\")) != 0;
  // PATHSEPSTR (ascii_defs.h "/") and the prelude's compound literal
  bad |= sizeof("/") != sizeof((const char[]){'/', '\0'})
         || memcmp("/", (const char[]){'/', '\0'}, sizeof("/")) != 0;
  puts(bad ? "literals differ" : "literals equal");
  return bad;
}
