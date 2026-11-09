# src/nvim/os/env.c (claimed)

Claim for verifying the 36 functions of `src/nvim/os/env.c` (environment-variable
expansion, `expand_env_esc`, `home_replace`, `remove_tail`, `vim_getenv`, ...).

Status (2026-11-09 09:00 UTC stop): **0/36 proved.** The thread started at 08:35 UTC with a
hard stop at 09:00 UTC, so only the claim and the plan below exist. No proofs, no findings.

## Plan for the next agent
- Byte-level, bounded: `env_name_valid`, `env_name_len`, `remove_tail`, `get_env_name`,
  `os_shell_is_cmdexe` -> CBMC, like `../mbyte/cbmc/`.
- Unbounded string loops: `expand_env_esc`, `home_replace` -> Frama-C WP with `-wp-smoke-tests`.
  Model output-buffer bounds (`dstlen`) explicitly; check the `~user` and `$VAR` copy paths for
  writes past `dst + dstlen - 1`.
- For any growing-array model use the ghost "avoid" style from `../typval/wp_blob`, not the
  `garray/wp/stubs/vp_garray.h` xrealloc stub (it is contradictory, so proofs on it are vacuous).
- libuv / OS-wrapper functions (`os_getenv`, `os_setenv`, `os_get_hostname`, ...) need a
  libuv contract stub; they stay unverified until one exists.

## Unverified (all 36)
env_init, env_name_valid, env_name_len, os_getenv, os_getenv_buf, os_getenv_noalloc,
os_env_exists, os_setenv, os_unsetenv, os_free_fullenv, os_getenvname_at_index, os_get_pid,
os_hint_priority, os_get_hostname, os_homedir, init_homedir, os_uv_homedir, free_homedir,
expand_env_save, expand_env_save_opt, expand_env, expand_env_esc, vim_runtime_dir,
remove_tail, vim_env_iter, vim_env_iter_rev, vim_get_prefix_from_exepath, vim_getenv,
home_replace, home_replace_save, get_env_name, os_setenv_append_path, os_shell_is_cmdexe,
vim_unsetenv_ext, vim_setenv_ext, restore_env_var
