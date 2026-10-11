#ifndef DG_SETTINGS_H
#define DG_SETTINGS_H
#include <stdint.h>
#include "policy.h"
#define DG_DIFFICULTY_MASK 0x8028u
/* Never serialized. Caller owns lifetime; zero initialize before first begin.
 * options_identity prevents substituting another standalone two-byte object.
 * draft_flags is deliberately wide so invalid flags cannot truncate to valid. */
struct DG_SettingsTxn {
    uintptr_t owner, options_identity;
    uint32_t epoch;
    uint16_t original_word;
    uint8_t original_flags, active;
    uint32_t draft_flags;
};
enum DG_SettingsResult {
    DG_SETTINGS_INVALID = -1, DG_SETTINGS_STALE = -2,
    DG_SETTINGS_NO_CHANGE = 0, DG_SETTINGS_CHANGED = 1
};
uint32_t dg_settings_decode(uint16_t word);
/* Invalid flags return word unchanged. Use set_draft/apply for error reporting. */
uint16_t dg_settings_merge(uint16_t word, uint32_t flags);
int dg_options_begin(const uint16_t *options, uintptr_t owner, uint32_t epoch,
                     struct DG_SettingsTxn *txn);
int dg_options_set_draft(struct DG_SettingsTxn *txn, uintptr_t owner,
                         uint32_t epoch, uint32_t flags);
int dg_options_apply(uint16_t *options, uintptr_t owner, uint32_t epoch,
                     struct DG_SettingsTxn *txn);
void dg_options_cancel(struct DG_SettingsTxn *txn);
#endif
