// Gives the fuzz harnesses Neovim's start-up initialisation without its main().
#define main nvim_unused_main
#include "nvim/main.c"
#undef main
void fuzz_early_init(void);
void fuzz_early_init(void)
{
  early_init(NULL);
}
