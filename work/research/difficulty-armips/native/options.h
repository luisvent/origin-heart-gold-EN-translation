#ifndef DG_OPTIONS_H
#define DG_OPTIONS_H
#include "settings.h"
/* All functions use ordinary AAPCS. Native callbacks keep their original
 * manager/state arguments. Hooks are exclusively native/options_hooks.json.
 * Resident singleton is BSS initialized, never placed in the Options object. */
uint16_t *dg_menu_field_getter(void *save);
void dg_menu_launch(void *field, void *args);
int dg_menu_init(void *manager, int *step);
int dg_menu_exit(void *manager, int *step);
void dg_menu_load_rows(void *state);
void dg_menu_draw(void *state);
void dg_menu_cursor_plane(unsigned bg, unsigned enabled);
void dg_menu_input(void *state);
int dg_menu_exit_animation(void *state);
/* Observe results in debugger/tests; no flags or UI outcome injection API. */
int dg_menu_last_apply_result(void);
#ifdef DG_OPTIONS_HOST_TEST
/* Replace only native ABI primitives, not transaction/input/render logic. */
uintptr_t dg_menu_test_call(uintptr_t address, uintptr_t a, uintptr_t b,
    uintptr_t c, uintptr_t d, uintptr_t e, uintptr_t f, uintptr_t g, uintptr_t h);
void *dg_menu_test_pointer(uint32_t address);
uint32_t dg_menu_test_read32(uintptr_t address);
uint16_t dg_menu_test_read16(uintptr_t address);
#endif
#endif
