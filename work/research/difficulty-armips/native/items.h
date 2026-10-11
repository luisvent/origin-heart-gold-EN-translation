#ifndef DIFFICULTY_ITEMS_H
#define DIFFICULTY_ITEMS_H

#include <stdint.h>
#include "growth.h"

/* Call-site adapters only: never replace the global item getter/effect engine.
 * All pointer arguments are native DS addresses, including in host tests.
 * snapshot.allowed certifies an ordinary interactive battle, not merely the
 * absence of known exclusion bits. The growth provider owns epoch freshness.
 */
uint32_t dg_bag_item_attr(uint32_t item, uint32_t attr, uint32_t heap,
                          void *bag_ui);
uint32_t dg_bag_remembered(void *bag, uint32_t item, uint32_t quantity,
                           uint32_t heap, void *bag_ui);
uint32_t dg_bag_accept(void *bag_ui);
/* Return the displaced instruction's output. Only selected item/category may
 * be cleared; neither function touches commands, slot counters or inventory.
 */
uint32_t dg_bag_commit_item(void *bag_args);
uint32_t dg_bag_commit_target(void *controller, void *party_args);
/* Only the attr lookup in 022217C8's item-effect loop. Actor and resolved target
 * are the original caller's stack+8/+20h locals. Never install globally.
 * Suppresses redundant attr38 ONLY for new All/local-trainer revivals28/29/37;
 * preserves attr23 revival and every other native attribute/result.
 */
uint32_t dg_bag_effect_attr(uint32_t item, uint32_t attr, uint32_t heap,
                            void *actor, void *target);

#ifdef DG_ITEMS_HOST_TEST
/* Synthetic DS memory, with the SAME RAM/alignment/identity guards as ARM.
 * Link shipping items.c AND policy.c; supply these primitives and the existing
 * dg_growth_snapshot() provider. Reads/writes must model little-endian DS RAM.
 */
uint8_t dg_items_test_read8(uintptr_t address);
uint16_t dg_items_test_read16(uintptr_t address);
uint32_t dg_items_test_read32(uintptr_t address);
void dg_items_test_write8(uintptr_t address, uint8_t value);
void dg_items_test_write16(uintptr_t address, uint16_t value);
uint32_t dg_items_test_native_attr(uint32_t item, uint32_t attr, uint32_t heap);
uint32_t dg_items_test_native_count(void *bag, uint32_t item,
                                   uint32_t quantity, uint32_t heap);
uint32_t dg_items_test_native_accept(void *bag_ui);
#endif

#endif
