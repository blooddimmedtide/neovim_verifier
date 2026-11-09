// Globals, macros and reduced buf_T for undo_allowed / corruption_error / expr_map_locked, as
// Neovim defines them (files per line). emsg/semsg only record their arguments.
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <string.h>
#define FUNC_ATTR_NONNULL_ALL
#define BF_DUMMY        0x80                                  // nvim/buffer_defs.h
#define MODIFIABLE(buf) (buf->b_p_ma)                         // nvim/buffer_defs.h
#define _(x) (x)                                              // gettext: identity in the proof
typedef struct { int b_p_ma; int b_flags; } buf_T;
buf_T *curbuf;                                                // nvim/globals.h
int textlock, sandbox, expr_map_lock;                         // nvim/globals.h
const char e_modifiable[] = "E21: Cannot make changes, 'modifiable' is off";   // nvim/errors.h
const char e_sandbox[] = "E48: Not allowed in sandbox";
const char e_textlock[] = "E565: Not allowed to change text or change window";
int msg_calls; const char *msg_fmt; const char *msg_a1; const char *msg_a2;
static inline bool emsg(const char *s) { msg_calls++; msg_fmt = s; return true; }
static inline bool semsg(const char *fmt, const char *a1, const char *a2) {
  msg_calls++; msg_fmt = fmt; msg_a1 = a1; msg_a2 = a2; return true; }
