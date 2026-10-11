#ifndef DG_RUNTIME_H
#define DG_RUNTIME_H
#include "growth.h"
/* Native lifecycle hooks, shared by growth/items. No lazy capture. */
void dg_battle_begin(void);
uintptr_t dg_battle_root_free(void *root);
void dg_runtime_invalidate(void);
uint32_t dg_runtime_ordinary(uint32_t flags, uint32_t control);
/* Validated published current save only; never the constructor's global. */
uintptr_t dg_runtime_save(void);
uint32_t dg_runtime_ram(uintptr_t p, uint32_t size, uint32_t alignment);
#ifdef DG_RUNTIME_HOST_TEST
uint32_t dg_runtime_test_read32(uintptr_t p);
uint16_t dg_runtime_test_read16(uintptr_t p);
uintptr_t dg_runtime_test_save(void);
uintptr_t dg_runtime_test_options(uintptr_t save);
void dg_runtime_test_begin(void);
uintptr_t dg_runtime_test_free(void *root);
#endif
#endif
