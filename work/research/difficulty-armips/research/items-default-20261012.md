# Battle items DEFAULT — 2026-10-12

D-2412: the user requested that the former LIMITED choice preserve the Chinese
hack's actual item permissions. The existing settings bit and ALL expansion
are unchanged; existing saves with ITEMS_ALL clear now use the Chinese rules.

`policy.c` returns the original item mask for DEFAULT. ALL still adds exactly
the twenty medicines listed in items.md. Wild, field, held-item, opponent and
special-mode delegation retain their existing paths and validation.

Menu: ITEMS IN BATTLE, DEFAULT / ALL. Help follows the selected draft choice:

- DEFAULT: original Chinese hack rules.
- ALL: enables healing/status/PP items.
- Both: Trainer Bag only. Held items unchanged.

The requested berries/flutes-only description was replaced because the original
Chinese permissions also allow Potion, Super Potion, drinks, Heal Powder and
Berry Juice. Existing source-pin override history is retained.

Validation: 12 focused tests passed: full-width compiled policy checks;
ASan/UBSan item and Options drivers; wrong Bag-offset and wrong Full Restore
category mutation checks. The item driver uses metadata from the identity-checked
untouched Chinese ROM and checks every item/flag combination and all four gates.
DEFAULT category counts now match CN (11/10/25/10); ALL remains 23/19/25/10.
All seven native C modules compile and link; ELF bounds and source guards pass.
Font-0 widths: heading 86 px, DEFAULT 42 px, help lines 199/204/212 px.

No ROM or release patch was rebuilt in this change. Prior emulator captures
and acceptance reports describe the previous behavior. Native recipes that
expect Potion to be denied with ITEMS_ALL clear (including the old persistence
and stale-Potion gate scenarios) must be revised before a new native acceptance
run; their historical results do not validate DEFAULT. The source bindings
invalidate older native evidence rather than carrying its acceptance forward.

Local build/test artifacts: work/build/items-chinese-default-20261012/.
