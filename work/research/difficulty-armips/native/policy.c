#include "policy.h"

uint32_t dg_clamp_exp(uint32_t current, uint32_t requested,
                      uint32_t ceiling, uint32_t enabled)
{
    uint32_t remaining;

    if (enabled == 0u) {
        return requested;
    }
    if (current >= ceiling) {
        return 0u;
    }
    remaining = ceiling - current;
    return requested < remaining ? requested : remaining;
}

uint32_t dg_exp_eligible(uint32_t native_eligible, uint32_t participated,
                        uint32_t share_enabled)
{
    if (native_eligible == 0u ||
        (share_enabled == 0u && participated == 0u)) {
        return 0u;
    }
    return native_eligible;
}

uint32_t dg_item_battle_mask(uint32_t item_id, uint32_t original_mask,
                            uint32_t all_mask, uint32_t player_trainer_bag,
                            uint32_t items_all)
{
    if (player_trainer_bag == 0u) {
        return original_mask;
    }
    if (items_all != 0u) {
        return all_mask;
    }
    /* DEFAULT preserves the untouched Chinese hack's item metadata. */
    (void)item_id;
    return original_mask;
}
