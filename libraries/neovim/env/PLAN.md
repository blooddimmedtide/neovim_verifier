# src/nvim/os/env.c (pinned upstream 7b87ce8)

Claim. 36 functions, none proved yet. Started 2026-11-09 08:35 UTC with a 09:00 UTC stop.

First targets (small, libc-only): env_name_valid, env_name_len, vim_env_iter, vim_env_iter_rev,
remove_tail. Then expand_env_esc and home_replace.

Hand-review notes (not proofs):
- vim_env_iter_rev with an empty `val` and iter == NULL computes `val + strlen(val) - 1`, i.e.
  `val - 1`, a pointer before the object (UB in C11 6.5.6p8). The result is still varlen 0 and
  xmemrchr(.., 0) returns NULL, so behaviour is benign on gcc/clang. Callers to be checked.
