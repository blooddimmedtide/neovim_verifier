# src/nvim/os/env.c (pinned upstream 7b87ce8)

Claim (draft PR #25). 36 functions. Stopped 2026-11-09 08:55 UTC at the usage deadline.
Status: 1 proved for every input, 1 proved only for bounded inputs, 1 refuted (finding), 33 not started.

| Function | Tool | Result |
|---|---|---|
| env_name_valid (non-Windows branch) | Frama-C 33 WP, RTE + smoke tests | 6/6 goals, smoke 1/1, signed char only (`wp/run_wp.sh`) |
| vim_env_iter | CBMC 6.4.1, every string up to 4 bytes, every delimiter, both char signednesses, full unwinding | proved bounded (`cbmc/run_cbmc.sh`); WP 30/31, `ensures_4` times out, so not proved for every length |
| vim_env_iter_rev | CBMC + WP | FAILS: see finding below; WP 28/31 |

Contracts are in `wp/contracts.py` (from the doc comments). Trusted: C11 strlen/strchr contracts
in `wp/prelude.h`, and xmemrchr's contract (proved in libraries/neovim/memory). Caller precondition
for vim_env_iter: `delim != NUL` (with NUL it returns a pointer past the terminator).

Open gaps in what is done: WP unsigned-char run (no unsigned-char x86_64 machdep wired up yet),
the vim_env_iter WP goal above, differential test, planted bugs, independent review, vpipe target,
status.tsv rows.

## Finding (low impact, not reported upstream)

`vim_env_iter_rev` forms the pointer `val - 1`, which is outside the object (C11 6.5.6p8, UB):
when `val` is empty (`val + strlen(val) - 1`), and when `val` starts with the delimiter
(it returns `colon - 1` with `colon == val`, and the next call computes `varend - val` from it).
CBMC flags both (`pointer outside object bounds`). gcc/clang give the intended items today, so the
practical risk is an optimiser exploiting the UB. Fix idea (not written, not proved): keep the
iterator as one-past the item end (`colon`, `val + strlen(val)`), so no pointer before `val` is made.

## Not started (33)

env_init, env_name_len, os_getenv, os_getenv_buf, os_getenv_noalloc, os_env_exists, os_setenv,
os_unsetenv, os_free_fullenv, os_getenvname_at_index, os_get_pid, os_hint_priority,
os_get_hostname, os_homedir, init_homedir, os_uv_homedir, free_homedir, expand_env_save,
expand_env_save_opt, expand_env, expand_env_esc, vim_runtime_dir, remove_tail,
vim_get_prefix_from_exepath, vim_getenv, home_replace, home_replace_save, get_env_name,
os_setenv_append_path, os_shell_is_cmdexe, vim_unsetenv_ext, vim_setenv_ext, restore_env_var.
