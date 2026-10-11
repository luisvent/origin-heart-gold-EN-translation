#ifndef DG_CAPS_H
#define DG_CAPS_H
#include <stdint.h>
/* Pure next-unfinished resolver: running maximum of actual gym maxima through
 * that guide-order row; 100 after all gyms. Adding completions never lowers it.
 * Later completions cannot bypass an earlier gap. Bitmap bit N is native badge
 * N; flags are booleans for delayed Erika/Clair victories. No EXP writes. */
uint32_t dg_cap_resolve(uint32_t badges, uint32_t erika, uint32_t clair);
/* Returns zero if owner/accessor validation fails; native read-only binding. */
uint32_t dg_cap_for_save(uintptr_t save);
#ifdef DG_CAPS_HOST_TEST
uintptr_t dg_caps_test_profile(uintptr_t save);
uintptr_t dg_caps_test_vars(uintptr_t save);
uint32_t dg_caps_test_badge(uintptr_t profile,uint32_t id);
uint32_t dg_caps_test_flag(uintptr_t vars,uint32_t id);
#endif
#endif
