#!/bin/bash
# Usage: bash mutants.sh <neovim checkout> — plants bugs in the annotated copy; each must fail WP.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d); caught=0; total=0
python3 -I "$HERE/build.py" "$NV" "$W/base.c" || exit 1
m() {  # $1 function, $2 old text, $3 new text
  total=$((total+1))
  python3 -I -c 'import sys; t=open(sys.argv[1]).read(); o,n=sys.argv[3],sys.argv[4]; assert t.count(o)>=1, o; open(sys.argv[2],"w").write(t.replace(o,n,1))' "$W/base.c" "$W/m.c" "$2" "$3" || { echo "MUTANT $total not applied"; return; }
  (cd "$W" && frama-c -machdep x86_64 m.c -wp -wp-fct "$1" -wp-rte -warn-signed-downcast -wp-init-const \
     -wp-model Typed+Cast -wp-prover z3,cvc5 -wp-timeout 10 -wp-par "$(nproc)" -wp-cache none > "mut$total.log" 2>&1)
  if grep -qE "Proved goals: +([0-9]+) / \1$" "$W/mut$total.log"; then echo "MUTANT $total SURVIVED: $1: $3"; else caught=$((caught+1)); echo "mutant $total caught ($1)"; fi
}
m name_to_mod_mask "  c = TOUPPER_ASC(c);" "  c = c;"
m name_to_mod_mask "      return mod_mask_table[i].mod_flag;" "      return mod_mask_table[i].mod_mask;"
m name_to_mod_mask "  return 0;
}" "  return 1;
}"
m handle_x_keys "  case K_ZHOME:
    return K_HOME;" "  case K_ZHOME:
    return K_END;"
m handle_x_keys "  case K_S_XF4:
    return K_S_F4;" "  case K_S_XF4:
    return K_F4;"
m handle_x_keys "  case K_XUP:
    return K_UP;" "  case K_XUP:
    return K_DOWN;"
m get_mouse_button "      *is_drag = mouse_table[i].is_drag;" "      *is_drag = mouse_table[i].is_click;"
m get_mouse_button "  return 0;         // Shouldn't get here" "  return 1;         // Shouldn't get here"
m get_mouse_button "  for (int i = 0; mouse_table[i].pseudo_code; i++) {" "  for (int i = 1; mouse_table[i].pseudo_code; i++) {"
m extract_modifiers "    if (!(modifiers & MOD_MASK_CTRL)) {" "    if ((modifiers & MOD_MASK_CTRL)) {"
m extract_modifiers "    if (key == NUL) {  // <C-@> is <Nul>" "    if (key == 1) {  // <C-@> is <Nul>"
m extract_modifiers "      && ((key >= '?' && key <= '_') || ASCII_ISALPHA(key))) {" "      && ((key >= '@' && key <= '_') || ASCII_ISALPHA(key))) {"
m extract_modifiers "    if (did_simplify != NULL) {
      *did_simplify = true;" "    if (did_simplify != NULL) {
      *did_simplify = simplify;"
echo "caught $caught / $total"; [ $caught = $total ]
