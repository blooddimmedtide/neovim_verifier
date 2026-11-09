// WP model for read_string (src/nvim/fileio.c): the file is the ghost array fdata[0..flen-1]
// read from fpos; getc follows C11 7.21.7.1 on a regular file with no I/O error.
// xmallocz/xfree as in memory.c (never NULL: Neovim exits on out-of-memory). WP does not
// implement \fresh/\freeable, so the allocation is modelled as a valid block disjoint from
// the file state; that it is fresh and freed exactly once is covered by the CBMC harness
// (leak and pointer options) for small files, not here.
#include <stddef.h>
#define EOF (-1)
typedef struct file_s FILE;
extern unsigned char fdata[];
extern size_t flen, fpos;

/*@ assigns fpos;
    behavior more: assumes fpos < flen;
      ensures \result == fdata[\old(fpos)] && fpos == \old(fpos) + 1;
    behavior end: assumes fpos >= flen;
      ensures \result == EOF && fpos == \old(fpos);
    complete behaviors; disjoint behaviors; */
int getc(FILE *fd);

/*@ requires size < SIZE_MAX;
    assigns \nothing;
    ensures \valid((char *)\result + (0 .. size)) && ((char *)\result)[size] == 0;
    ensures \separated((char *)\result + (0 .. size), fdata + (0 .. flen - 1), &fpos, &flen); */
void *xmallocz(size_t size);

/*@ assigns \nothing; */
void xfree(void *p);
