# regexp.c, search.c, fuzzy.c: plan and progress

Claimed by the draft PR "neovim: verify src/nvim/regexp.c, src/nvim/search.c, src/nvim/fuzzy.c".
Pinned upstream: neovim 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd (see ../vpipe.toml).

Functions in scope (from ../inventory.tsv): regexp.c 176 (backtracking + NFA engines and the
shared helpers), search.c 57, fuzzy.c 21. Total 254. None is done until its full functional
contract is proved; progress is tracked per function in ../status.tsv.

Order:
1. Sanitizer fuzzing (ASan + UBSan, libFuzzer) of both regex engines (compile + match),
   fuzzy matching and the pure search helpers, with a differential check between the
   backtracking and NFA engines. Every crash gets a finding and a fix branch on the fork.
2. Proofs, leaves first: byte/char-class helpers and fuzzy scoring with CBMC, loops over
   unbounded strings with Frama-C WP.

## Progress (2026-11-02)

**0 of 254 functions done.** 3 have a proof waiting for review and owner sign-off
(`getdecchrs` fixed-candidate, `gethexchrs`, `getoctchrs` candidate; see `../regexp/CLAIM.md`).

### Fuzzing (step 1)

Harnesses in `fuzz/` (libFuzzer, ASan + UBSan, linked against an instrumented Neovim build;
`fuzz/build.sh`). About 1.1 million regexp runs and 1.4 million search/fuzzy runs so far.

- `fuzz_regexp.c`: compiles and runs every input with both engines (`vim_regcomp`,
  `vim_regexec_nl`, `vim_regexec_multi` on buffer lines, `vim_regsub` length pass vs copy pass)
  and compares the two engines' match and sub-match positions on valid UTF-8.
- `fuzz_search.c`: `searchit` (both directions, 4 option sets), `findmatchlimit` (every brace,
  comment and preprocessor kind), `search_for_exact_line`, `fuzzy_match`, `fuzzy_match_str`,
  `fuzzy_match_str_with_pos`, `search_for_fuzzy_match`; checks positions stay inside the buffer
  and fuzzy positions are increasing character indexes.

Findings (in `../findings/`):

| Finding | Status |
|---|---|
| `regexp-getdecchrs-overflow.md`: signed overflow on 19+ digit numbers | fixed (fork 3336e2d), fix proved for every input |
| `regexp-nfa-backslash-multibyte.md`: NFA never matches `\é` | fixed (fork dd5213f), proof pending (NFA compiler spec) |
| `regexp-bt-position-wrap.md`: `\%4294967297l` means `\%1l` (backtracking) | fixed (fork b2bbb00), proof pending |
| `regexp-bt-composing-atom-ends-match.md`: composing-char atom ends the whole match (backtracking) | open; first fix broke an upstream test, needs redesign |
| `regexp-nfa-huge-count-exit.md`: `\%#=2x\{3,15555555}` makes Neovim exit (E41) | open; limit needs a decision |
| `regexp-nfa-lone-composing-at-start.md`: engines disagree on a leading lone composing char | open; spec question |
| `search-csearch-overflow.md`: `setcharsearch()` with 40 composing chars writes past `lastc_bytes`; stale bytes after a shorter char | fixed (fork 01c749d), proved with CBMC for every input (`../search/`) |

Not yet triaged: engine differences on `\%'(`/`\%')` mark atoms that depend on state left by
earlier inputs (not reproducible from a single input), and regexp timeouts (exponential
backtracking, expected for some patterns). No memory-safety error (ASan) in regexp.c or
fuzzy.c so far; one in search.c (`set_last_csearch`, above). Neovim's own regexp, search, substitute, gn, search-stat and
matchfuzzy tests pass with the three fixes.

Note for `fuzzy_match`: callers always pass `maxMatches == FUZZY_MATCH_MAX_LEN`; with a smaller
value `match_positions` could write past `matches` (latent, not reachable today). The proof will
state this precondition.

## Functions still unverified

### src/nvim/fuzzy.c: 0 of 21 with a proof (none done yet), 21 unverified

`fuzzy_match`, `fuzzy_match_item_compare`, `fuzzy_match_in_list`, `do_fuzzymatch`, `f_matchfuzzy`, `f_matchfuzzypos`, `fuzzy_match_str_compare`, `fuzzy_match_str_sort`, `fuzzy_match_func_compare`, `fuzzy_match_func_sort`, `fuzzy_match_str`, `fuzzy_match_str_with_pos`, `fuzzy_match_str_in_line`, `search_for_fuzzy_match`, `fuzmatch_str_free`, `fuzzymatches_to_strmatches`, `has_match`, `compute_bonus_codepoint`, `setup_match_struct`, `match_row`, `match_positions`

### src/nvim/regexp.c: 11 of 176 with a proof (none done yet), 165 unverified

`get_char_class`, `init_class_tab`, `get_equi_class`, `get_coll_element`, `get_cpo_flags`, `skip_anyof`, `skip_regexp`, `skip_regexp_err`, `skip_regexp_ex`, `initchr`, `save_parse_state`, `restore_parse_state`, `peekchr`, `skipchr`, `skipchr_keepstart`, `getchr`, `ungetchr`, `read_limits`, `reg_breakcheck`, `reg_iswordc`, `reg_getline_common`, `reg_getline`, `reg_getline_len`, `make_extmatch`, `ref_extmatch`, `unref_extmatch`, `reg_prev_class`, `reg_match_visual`, `prog_magic_wrong`, `cleanup_subexpr`, `cleanup_zsubexpr`, `reg_nextline`, `match_with_backref`, `re_mult_next`, `mb_decompose`, `cstrncmp`, `cstrchr`, `do_upper`, `do_lower`, `regtilde`, `fill_submatch_list`, `clear_submatch_list`, `vim_regsub`, `vim_regsub_multi`, `free_resub_eval_result`, `vim_regsub_both`, `reg_getline_submatch`, `reg_getline_submatch_len`, `reg_submatch`, `reg_submatch_list`, `init_regexec_multi`, `get_char_class_bits`, `bt_recognize_char_class`, `vim_regcomp`, `use_multibytecode`, `regc`, `regmbc`, `reg_equi_class`, `regnode`, `re_put_uint32`, `regnext`, `regtail`, `regoptail`, `reginsert`, `reginsert_nr`, `reginsert_limits`, `seen_endbrace`, `regatom`, `regpiece`, `regconcat`, `regbranch`, `reg`, `bt_regcomp`, `coll_get_char`, `bt_regfree`, `reg_save`, `reg_restore`, `reg_save_equal`, `save_se_multi`, `save_se_one`, `regrepeat`, `regstack_push`, `regstack_pop`, `save_subexpr`, `restore_subexpr`, `regmatch`, `regtry`, `bt_regexec_both`, `bt_regexec_nl`, `bt_regexec_multi`, `regdump`, `regprop`, `nfa_regcomp_start`, `nfa_get_reganch`, `nfa_get_regstart`, `nfa_get_match_text`, `realloc_post_list`, `nfa_recognize_char_class`, `nfa_emit_equi_class`, `nfa_regatom`, `nfa_regpiece`, `nfa_regconcat`, `nfa_regbranch`, `nfa_reg`, `nfa_set_code`, `nfa_postfix_dump`, `nfa_print_state`, `nfa_print_state2`, `nfa_dump`, `re2post`, `alloc_state`, `frag`, `list1`, `patch`, `append`, `st_error`, `st_push`, `st_pop`, `nfa_max_width`, `post2nfa`, `nfa_postprocess`, `log_subsexpr`, `log_subexpr`, `pim_info`, `copy_pim`, `clear_sub`, `copy_sub`, `copy_sub_off`, `copy_ze_off`, `sub_equal`, `open_debug_log`, `report_state`, `has_state_with_pos`, `pim_equal`, `match_follows`, `state_in_list`, `addstate`, `addstate_here`, `check_char_class`, `match_backref`, `match_zref`, `nfa_save_listids`, `nfa_restore_listids`, `recursive_regmatch`, `failure_chance`, `skip_to_start`, `find_match_text`, `match_composing`, `nfa_did_time_out`, `nfa_regmatch`, `nfa_regtry`, `nfa_regexec_both`, `nfa_regcomp`, `nfa_regfree`, `nfa_regexec_nl`, `nfa_regexec_multi`, `vim_regcomp`, `vim_regfree`, `free_regexp_stuff`, `report_re_switch`, `vim_regexec_string`, `vim_regexec_prog`, `vim_regexec`, `vim_regexec_nl`, `vim_regexec_multi`

### src/nvim/search.c: 14 of 57 with a proof (none done yet), 43 unverified

`search_regcomp`, `save_re_pat`, `save_search_patterns`, `restore_search_patterns`, `free_spat`, `free_search_patterns`, `save_last_search_pattern`, `restore_last_search_pattern`, `save_incsearch_state`, `restore_incsearch_state`, `ignorecase`, `ignorecase_opt`, `pat_has_uppercase`, `last_search_pat`, `reset_search_dir`, `set_last_search_pat`, `last_pat_prog`, `searchit`, `set_vv_searchforward`, `parse_search_pattern_offset`, `do_search`, `search_for_exact_line`, `searchc`, `findmatch`, `check_prevcol`, `find_rawstring_end`, `find_mps_values`, `findmatchlimit`, `showmatch`, `current_search`, `is_zero_width`, `linewhite`, `cmdline_search_stat`, `update_search_stat`, `f_searchcount`, `get_line_and_copy`, `find_pattern_in_path`, `show_pat_in_path`, `get_search_pattern`, `get_substitute_pattern`, `get_search_pattern_timestamp`, `set_search_pattern`, `set_substitute_pattern`
