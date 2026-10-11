#ifndef DIFFICULTY_GROWTH_H
#define DIFFICULTY_GROWTH_H

#include <stdint.h>

/* Integration-owned immutable view, not a persisted settings representation.
 * ARM ABI: offsets 0/4/8/12/16, sizeof 20. Host root is pointer-sized.
 * allowed is a positive ordinary-battle classification shared with item policy;
 * absence of the native reward veto alone does not establish allowed context.
 */
typedef struct DG_GrowthSnapshot {
    uint32_t flags;
    uint32_t cap_level;
    uint32_t allowed;
    uintptr_t root;
    uint32_t epoch;
} DG_GrowthSnapshot;

/* Runtime must return NULL unless this is the CURRENT live battle generation.
 * Capture settings/cap/context before the first item/reward operation. Keep the
 * view immutable during a hook; reset on battle entry/end and reset/load, even
 * if the heap reuses root. Epoch zero is invalid. Growth cannot establish epoch
 * freshness from an address: that guarantee belongs to this provider.
 */
const DG_GrowthSnapshot *dg_growth_snapshot(void);

/* Overlay 14 BL 0x022289EA (original ec f7 e9 fe -> 0x022157C0).
 * Native participation/formula logic controls BOTH bench EXP and bench EVs.
 */
uint32_t dg_growth_share_enabled(void);

/* Overlay 14 BL 0x0221F778 (ff f7 b8 ff) and 0x0221F83E (ff f7 55 ff).
 * Both replace calls to 0x0221F6EC with its exact r0-r3 ABI. Original native
 * argument validity preconditions still apply; the original runs first.
 * Change only the output amount, after native eligibility/formula, before its
 * message/application/accumulator consumers. Preserve original return/deferred.
 * NEVER hook EV call 0x0221F682 or mutate the raw reward/Pokemon/cache here.
 */
uint32_t dg_growth_eligible(uint32_t *amount, uint32_t *deferred,
                            void *battle_mon, const void *raw_reward);

#ifdef DG_GROWTH_HOST_TEST
/* Tests supply these primitives plus dg_growth_snapshot and link policy.c.
 * Reads use synthetic DS addresses (including root slot 0x02255BAC); the same
 * 0x02000000..0x02400000 bounds/alignment guards execute on host and ARM.
 * Output amount/deferred and raw_reward can be ordinary host buffers. Native
 * eligibility mocks must preserve the native ABI; all policy is in growth.c.
 * Resolver must only be called with checked IDs 1..6. Reward gate corresponds
 * to native 0x02215A78, including its 0x2A4 veto, not an allowlist substitute.
 */
uint8_t dg_growth_test_read8(uintptr_t address);
uint16_t dg_growth_test_read16(uintptr_t address);
uint32_t dg_growth_test_read32(uintptr_t address);
uint32_t dg_growth_test_native_share(void);
uint32_t dg_growth_test_native_reward_allowed(void);
uintptr_t dg_growth_test_native_resolve(uint32_t id);
uint32_t dg_growth_test_native_threshold(uint32_t species, uint32_t level);
uint32_t dg_growth_test_native_eligible(uint32_t *amount, uint32_t *deferred,
                                       void *battle_mon, const void *raw_reward);
#endif

#endif
