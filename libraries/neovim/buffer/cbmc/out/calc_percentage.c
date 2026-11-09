int calc_percentage(int64_t part, int64_t whole)
{
  // With 32 bit longs and more than 21,474,836 lines multiplying by 100
  // causes an overflow, thus for large numbers divide instead.
  return (part > 1000000) ? (int)(part / (whole / 100))
                          : (int)((part * 100) / whole);
}
