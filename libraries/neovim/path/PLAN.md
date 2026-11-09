# path.c verification plan

Claimed by draft PR (this branch). Upstream pinned at neovim 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd, Linux x86_64 (UNIX, no BACKSLASH_IN_FILENAME).
Tool: Frama-C WP (loops over NUL-terminated strings).

Progress: 16 / 67 proved (candidate, needs review and owner sign-off), 1 partial, 50 open. See CLAIM.md.

| function | line | status |
|---|---|---|
| path_equal | 56 | open |
| path_tail | 101 | proved (candidate), WP |
| path_tail_with_sep | 127 | proved (candidate), WP |
| invocation_path_tail | 160 | bug found; fix proved memory-safe, quote rules open |
| path_next_component | 194 | proved (candidate), WP |
| path_skip_sep | 211 | proved (candidate), WP |
| path_head_length | 224 | proved (candidate), WP |
| is_path_head | 239 | proved (candidate), WP |
| get_past_head | 252 | proved (candidate), WP |
| vim_ispathsep | 271 | proved (candidate), WP |
| vim_ispathsep_nocolon | 285 | proved (candidate), WP |
| vim_ispathlistsep | 295 | proved (candidate), WP |
| shorten_dir_len | 308 | open |
| shorten_dir | 345 | open |
| dir_of_file_exists | 354 | open |
| do_concat_fnames | 378 | open |
| concat_fnames | 403 | open |
| concat_fnames_realloc | 424 | open |
| add_pathsep | 438 | open |
| FullName_save | 463 | open |
| save_abs_path | 481 | open |
| path_has_wildcard | 499 | open |
| pstrcmp | 518 | open |
| path_expand | 534 | open |
| scandir_next_with_dots | 540 | open |
| do_path_expand | 558 | open |
| find_previous_pathsep | 749 | open |
| is_unique | 770 | open |
| expand_path_option | 802 | open |
| get_path_cutoff | 869 | open |
| uniquefy_paths | 906 | open |
| gettail_dir | 1056 | open |
| expand_in_path | 1084 | open |
| has_env_var | 1122 | open |
| has_special_wildchar | 1139 | open |
| gen_expand_wildcards | 1188 | open |
| FreeWild | 1329 | open |
| vim_backtick | 1341 | open |
| expand_backtick | 1352 | open |
| slash_adjust | 1406 | open |
| path_to_backslash | 1428 | open |
| path_to_slash | 1438 | open |
| path_to_slash_save | 1447 | open |
| addfile | 1461 | open |
| simplify_filename | 1509 | open |
| path_has_drive_letter | 1684 | proved (candidate), WP |
| path_is_url | 1696 | proved (candidate), WP |
| path_with_url | 1713 | proved (candidate), WP |
| path_with_extension | 1739 | open |
| vim_isAbsName | 1750 | proved (candidate), WP |
| vim_FullName | 1766 | open |
| fix_fname | 1803 | open |
| path_fix_case | 1837 | open |
| after_pathsep | 1891 | proved (candidate), WP |
| same_directory | 1900 | open |
| path_fold_char | 1918 | open |
| path_cmp | 1950 | open |
| path_try_shorten_fname | 2012 | open |
| path_shorten_fname | 2034 | open |
| expand_wildcards_eval | 2081 | open |
| expand_wildcards | 2139 | open |
| match_suffix | 2196 | open |
| path_full_dir_name | 2229 | open |
| append_path | 2262 | open |
| path_to_absolute | 2300 | open |
| path_is_absolute | 2353 | proved (candidate), WP |
| path_guess_exepath | 2377 | open |
