// ---- check_digraph_chars_valid (verbatim, sha256 37e33da7bbe51002f0f3dd34fd7e2d124de5d5927209b17c14d61c9485701e2f)
bool check_digraph_chars_valid(int char1, int char2)
{
  if (char2 == 0) {
    char msg[MB_MAXCHAR + 1];
    msg[utf_char2bytes(char1, msg)] = NUL;
    semsg(_(e_digraph_must_be_just_two_characters_str), msg);
    return false;
  }
  if (char1 == ESC || char2 == ESC) {
    emsg(_("E104: Escape not allowed in digraph"));
    return false;
  }
  return true;
}
// ---- registerdigraph (verbatim, sha256 4d9fe3a34884387c4381ebaebf768d8cd76961772148af94f7e67ffe84bcb7d4)
static void registerdigraph(int char1, int char2, int n)
{
  // If the digraph already exists, replace "result".
  digr_T *dp = (digr_T *)user_digraphs.ga_data;
  for (int i = 0; i < user_digraphs.ga_len; i++) {
    if ((int)dp->char1 == char1 && (int)dp->char2 == char2) {
      dp->result = n;
      return;
    }
    dp++;
  }

  // Add a new digraph to the table.
  dp = GA_APPEND_VIA_PTR(digr_T, &user_digraphs);
  dp->char1 = (uint8_t)char1;
  dp->char2 = (uint8_t)char2;
  dp->result = n;
}
