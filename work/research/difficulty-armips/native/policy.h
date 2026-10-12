#ifndef DIFFICULTY_POLICY_H
#define DIFFICULTY_POLICY_H

#include <stdint.h>

/* Logical option bits only; this header does not define a storage format. */
#define DG_SHARE_OFF 1u
#define DG_CAP_ON 2u
#define DG_ITEMS_ALL 4u
#define DG_KNOWN_MASK (DG_SHARE_OFF | DG_CAP_ON | DG_ITEMS_ALL)

/*
 * Stateless policy shared by the native runtime and host tests. All predicate
 * arguments use zero for false and any nonzero value for true. Callers extract
 * the relevant option bit before calling; do not pass the complete flags word.
 * In particular, share_enabled is true when DG_SHARE_OFF is NOT set.
 * No function accesses game memory, allocates, or requires a C runtime.
 */

/*
 * Return the EXP award, not the resulting total EXP.
 * Disabled: return requested exactly, even if current + requested would wrap.
 * Enabled: return min(requested, max(0, ceiling - current)), with mathematical
 * subtraction (no unsigned underflow). Never compute current + requested.
 * At or above the ceiling the award is zero; existing EXP/levels are untouched.
 * The caller supplies the species/growth-specific absolute EXP ceiling and
 * applies the returned award. This function does not choose a level cap.
 */
uint32_t dg_clamp_exp(uint32_t current, uint32_t requested,
                      uint32_t ceiling, uint32_t enabled);

/*
 * Filter native eligibility for BOTH the EXP and EV award paths. A native zero
 * is always denied. With sharing enabled, or for a participant, return the
 * native value unchanged; otherwise return zero to suppress bench EXP and EVs.
 * Native checks (including empty slots, eggs and other exclusions) remain the
 * caller's responsibility. A cap is deliberately not an eligibility input:
 * cap-clamped zero EXP must not suppress otherwise eligible EVs.
 */
uint32_t dg_exp_eligible(uint32_t native_eligible, uint32_t participated,
                        uint32_t share_enabled);

/*
 * Select battle-use metadata for an item. player_trainer_bag is true ONLY for
 * the player's Bag action in a trainer battle. Outside that context return
 * original_mask exactly, including wild/field uses, held items and opponent AI.
 *
 * Within that context, DEFAULT returns original_mask exactly, preserving the
 * untouched Chinese hack's permissions for every item. Invalid IDs remain
 * the caller's responsibility.
 *
 * ALL mode returns all_mask exactly. The caller must derive and validate it
 * from the actual expanded ordinary battle-use metadata for this item; it is
 * NOT a universal allow bit, a guessed category mask, or necessarily the
 * trainer-restricted original_mask. Pass zero for invalid/unusable items.
 * Native special-mode bans, target validation and effect handling must still
 * be enforced separately by the caller; ALL must not bypass them.
 */
uint32_t dg_item_battle_mask(uint32_t item_id, uint32_t original_mask,
                            uint32_t all_mask, uint32_t player_trainer_bag,
                            uint32_t items_all);

#endif
