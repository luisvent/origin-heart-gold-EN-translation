#include "growth.h"
#include "policy.h"

#define DG_BATTLE_ROOT_SLOT ((uintptr_t)0x02255BACu)
#define DG_RAM_START ((uintptr_t)0x02000000u)
#define DG_RAM_END ((uintptr_t)0x02400000u)
#define DG_ITEM_EXP_SHARE 216u

#ifdef DG_GROWTH_HOST_TEST
#define read8 dg_growth_test_read8
#define read16 dg_growth_test_read16
#define read32 dg_growth_test_read32
#define native_share dg_growth_test_native_share
#define native_mon_item dg_growth_test_native_mon_item
#define native_reward_allowed dg_growth_test_native_reward_allowed
#define native_resolve dg_growth_test_native_resolve
#define native_threshold dg_growth_test_native_threshold
#define native_eligible dg_growth_test_native_eligible
#else
static uint8_t read8(uintptr_t address)
{
    return *(const volatile uint8_t *)address;
}

static uint16_t read16(uintptr_t address)
{
    return *(const volatile uint16_t *)address;
}

static uint32_t read32(uintptr_t address)
{
    return *(const volatile uint32_t *)address;
}

/* Actual native Thumb callees, not stubs or a global EXP setter. */
#define native_share ((uint32_t (*)(void))(uintptr_t)0x022157C1u)
/* 0x0206D848 GetMonData(Pokemon *, field, void *): field 6 = held item. The
 * same call reads Lucky Egg at 0x02228A18 in the per-recipient routine. */
#define native_mon_item \
    ((uint32_t (*)(uintptr_t, uint32_t, uint32_t))(uintptr_t)0x0206D849u)
#define native_reward_allowed ((uint32_t (*)(void))(uintptr_t)0x02215A79u)
#define native_resolve ((uintptr_t (*)(uint32_t))(uintptr_t)0x022151BDu)
#define native_threshold \
    ((uint32_t (*)(uint32_t, uint32_t))(uintptr_t)0x0206F09Du)
#define native_eligible \
    ((uint32_t (*)(uint32_t *, uint32_t *, void *, const void *)) \
     (uintptr_t)0x0221F6EDu)
#endif

/* Bounds cover every byte used below, without unsigned end-address overflow.
 * Range validity is necessary, not proof of allocation/lifetime ownership:
 * integration's epoch contract and the resolver identity provide that proof.
 */
static uint32_t ram_words(uintptr_t address, uint32_t bytes)
{
    return (address & 3u) == 0u && address >= DG_RAM_START &&
           address <= DG_RAM_END - bytes;
}

static const DG_GrowthSnapshot *validated_snapshot(void)
{
    const DG_GrowthSnapshot *snapshot = dg_growth_snapshot();
    uintptr_t root;
    uintptr_t setup;

    if (snapshot == 0 || snapshot->epoch == 0u || snapshot->allowed == 0u ||
        (snapshot->flags & ~DG_KNOWN_MASK) != 0u) {
        return 0;
    }
    root = (uintptr_t)read32(DG_BATTLE_ROOT_SLOT);
    /* Include root's resolver slot for ID6: +0x1D0 + 4*6, four bytes. */
    if (root != snapshot->root || !ram_words(root, 0x1ECu)) {
        return 0;
    }
    setup = (uintptr_t)read32(root + 0x10u);
    if (!ram_words(setup, 4u)) {
        return 0;
    }
    /* Native reads flags at [[root+0x10]], NOT the setup pointer as flags. */
    if (native_reward_allowed() == 0u) {
        return 0;
    }
    return snapshot;
}

uint32_t dg_growth_share_enabled(uintptr_t battle_mon)
{
    const DG_GrowthSnapshot *snapshot = validated_snapshot();
    uint32_t id;
    uintptr_t backing;

    if (snapshot == 0) {
        return native_share();
    }
    if ((snapshot->flags & DG_SHARE_OFF) == 0u) {
        return 1u;
    }
    /* SHARE OFF: only a local recipient holding an Exp. Share keeps the
     * native bench share (D-2346, amends D-2301). Anything unverifiable
     * stays off, exactly as before. */
    if (!ram_words(battle_mon, 0x1Cu)) {
        return 0u;
    }
    id = read8(battle_mon + 0x14u);
    if (id < 1u || id > 6u || native_resolve(id) != battle_mon) {
        return 0u;
    }
    backing = (uintptr_t)read32(battle_mon + 0x10u);
    if (!ram_words(backing, 236u)) {
        return 0u;
    }
    return native_mon_item(backing, 6u, 0u) == DG_ITEM_EXP_SHARE;
}

uint32_t dg_growth_eligible(uint32_t *amount, uint32_t *deferred,
                            void *battle_mon, const void *raw_reward)
{
    uint32_t result = native_eligible(amount, deferred, battle_mon, raw_reward);
    const DG_GrowthSnapshot *snapshot;
    uintptr_t mon = (uintptr_t)battle_mon;
    uint32_t id;
    uint32_t ceiling;

    if (result == 0u || *amount == 0u) {
        return result;
    }
    snapshot = validated_snapshot();
    if (snapshot == 0 || (snapshot->flags & DG_CAP_ON) == 0u ||
        snapshot->cap_level < 1u || snapshot->cap_level > 100u ||
        !ram_words(mon, 0x1Cu)) {
        return result;
    }
    id = read8(mon + 0x14u);
    /* Local owner0 is IDs1..6 in this CN build. No parity/owner fallback. */
    if (id < 1u || id > 6u || native_resolve(id) != mon) {
        return result;
    }
    ceiling = native_threshold(read16(mon), snapshot->cap_level);
    *amount = dg_clamp_exp(read32(mon + 0x18u), *amount, ceiling, 1u);
    return result;
}
