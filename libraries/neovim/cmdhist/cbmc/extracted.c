HistoryType hist_char2type(const int c)
  FUNC_ATTR_CONST FUNC_ATTR_WARN_UNUSED_RESULT
{
  switch (c) {
  case ':':
    return HIST_CMD;
  case '=':
    return HIST_EXPR;
  case '@':
    return HIST_INPUT;
  case '>':
    return HIST_DEBUG;
  case NUL:
  case '/':
  case '?':
    return HIST_SEARCH;
  default:
    return HIST_INVALID;
  }
  // Silence -Wreturn-type
  return 0;
}
static int get_history_idx(int histype)
{
  if (hislen == 0 || histype < 0 || histype >= HIST_COUNT
      || hisidx[histype] < 0) {
    return -1;
  }

  return history[histype][hisidx[histype]].hisnum;
}
static int calc_hist_idx(int histype, int num)
{
  int i;

  if (hislen == 0 || histype < 0 || histype >= HIST_COUNT
      || (i = hisidx[histype]) < 0 || num == 0) {
    return -1;
  }

  histentry_T *hist = history[histype];
  if (num > 0) {
    bool wrapped = false;
    while (hist[i].hisnum > num) {
      if (--i < 0) {
        if (wrapped) {
          break;
        }
        i += hislen;
        wrapped = true;
      }
    }
    if (i >= 0 && hist[i].hisnum == num && hist[i].hisstr != NULL) {
      return i;
    }
  } else if (-num <= hislen) {
    i += num + 1;
    if (i < 0) {
      i += hislen;
    }
    if (hist[i].hisstr != NULL) {
      return i;
    }
  }
  return -1;
}
static int del_history_idx(int histype, int idx)
{
  int i = calc_hist_idx(histype, idx);
  if (i < 0) {
    return false;
  }
  idx = hisidx[histype];
  hist_free_entry(&history[histype][i]);

  // When deleting the last added search string in a mapping, reset
  // last_maptick, so that the last added search string isn't deleted again.
  if (histype == HIST_SEARCH && maptick == last_maptick && i == idx) {
    last_maptick = -1;
  }

  while (i != idx) {
    int j = (i + 1) % hislen;
    history[histype][i] = history[histype][j];
    i = j;
  }
  clear_hist_entry(&history[histype][idx]);
  if (--i < 0) {
    i += hislen;
  }
  hisidx[histype] = i;
  return true;
}
