// Minimal stand-in for the examiner test framework that telescope-fzf-native's
// test/test.c uses (TEST, ASSERT_EQ, ASSERT_TRUE/FALSE, ASSERT_EQ_MEM), so the
// upstream tests can run here unchanged.
#ifndef EXAMINER_SHIM_H
#define EXAMINER_SHIM_H
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
typedef void (*exam_fn)(void);
static struct { const char *name; exam_fn fn; } exam_tests[512];
static int exam_n = 0, exam_fail = 0, exam_cur_fail = 0;
#define TEST(a, b)                                                             \
  static void test_##a##_##b(void);                                            \
  __attribute__((constructor)) static void reg_##a##_##b(void) {               \
    exam_tests[exam_n].name = #a "." #b;                                       \
    exam_tests[exam_n++].fn = test_##a##_##b;                                  \
  }                                                                            \
  static void test_##a##_##b(void)
static int exam_eq_str(const char *a, const char *b) { return a && b && strcmp(a, b) == 0; }
#define EXAM_EQ(a, b)                                                          \
  _Generic((a), char *: exam_eq_str((const char *)(uintptr_t)(a), (const char *)(uintptr_t)(b)), \
           const char *: exam_eq_str((const char *)(uintptr_t)(a), (const char *)(uintptr_t)(b)), \
           void *: (const void *)(uintptr_t)(a) == (const void *)(uintptr_t)(b), \
           default: (long long)(a) == (long long)(b))
#define EXAM_FAIL(what)                                                        \
  do { fprintf(stderr, "  %s:%d: %s\n", __FILE__, __LINE__, what); exam_cur_fail = 1; } while (0)
#define ASSERT_EQ(a, b) do { if (!EXAM_EQ(a, b)) EXAM_FAIL("ASSERT_EQ(" #a ", " #b ")"); } while (0)
#define ASSERT_TRUE(a) do { if (!(a)) EXAM_FAIL("ASSERT_TRUE(" #a ")"); } while (0)
#define ASSERT_FALSE(a) do { if (a) EXAM_FAIL("ASSERT_FALSE(" #a ")"); } while (0)
#define ASSERT_EQ_MEM(a, b, n) do { if (memcmp(a, b, n)) EXAM_FAIL("ASSERT_EQ_MEM"); } while (0)
static void exam_init(int argc, char **argv) { (void)argc; (void)argv; }
static int exam_run(void) {
  const char *skip = getenv("EXAM_SKIP");   // skip suites whose name starts with this
  int ran = 0;
  for (int i = 0; i < exam_n; i++) {
    if (skip && !strncmp(exam_tests[i].name, skip, strlen(skip))) continue;
    ran++;
    exam_cur_fail = 0;
    exam_tests[i].fn();
    if (exam_cur_fail) { exam_fail++; fprintf(stderr, "FAIL %s\n", exam_tests[i].name); }
  }
  printf("%d tests, %d failed\n", ran, exam_fail);
  return exam_fail != 0;
}
#endif
