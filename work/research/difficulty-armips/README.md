# Difficulty research: armips migration

This is a static port of the **recovered resident foundation**, not a complete
difficulty-settings patch. It is deliberately outside `work/patches`: applying
the hooks without installing the complete resident autoload payload would branch
into absent code. `enabled = false` alone would not prevent explicit selection,
so do not move this manifest into the production registry yet.

`foundation.asm` replaces the hand-encoded bootstrap words and the GNU wrapper
with armips v0.11.0 mnemonics. It produces an isolated `foundation.bin` loaded at
`0x023DF000`. `BRIDGE_DISPATCH` is a required external symbol, including its ARM/
Thumb state bit; the test value `0x023DF301` is only a comparison fixture. The state
slot at `+0x100` starts zero; the Thumb prefix starts at `+0x200`; the ARM wrapper
starts at `+0x210`. The bootstrap matches the corrected linked-build version,
not the incomplete first recovery with incorrect literal offsets.

`hooks.asm` and `fix.toml` describe the three old ARM9 edits in the current
registry format. All edits have original-byte guards and four-byte `.area`
bounds. They use the canonical `../include/guards.inc` staging convention.
The foundation's `.create` is for isolated research assembly and is intentionally
not a production fix source: the production registry forbids `.create`.
The manifest cites D-1575's optional-feature policy; that citation does not grant
this recovered implementation shipping approval or reinstate its lost evidence.

## Provenance

The historical input is the sibling `poke-difficulty-research` checkout's
`work/build/difficulty-recovery/quarantine/resident-foundation/`:

- `/root/resident_owner`, line 2785: `bridge-linked-v1/wrapper.s`.
- `/root/resident_owner`, line 2818: `bridge-linked-v1/build.py`, corrected
  bootstrap word sequence and hook addresses.
- Its provenance manifest binds these versions to source-record hashes. They
  are historical versions; final identity and runtime acceptance remain lost.

No historical command was replayed. No recovered file was changed. No ROM,
emulator, save or gameplay setting was built or modified by this migration.

## Checks

Run from the repository root with existing local tools:

```sh
python3 work/research/difficulty-armips/check.py \
  --armips /path/to/armips \
  --gnu-wrapper /path/to/recovered/bridge-linked-v1/wrapper.s \
  --linker /path/to/ld.lld \
  --include-dir /path/to/current-checkout/work/patches/include
```

The checker assembles with v0.11.0 and compares the bootstrap with the corrected
historical sequence. It independently compiles/links the recovered GNU wrapper
and compares its prefix and wrapper byte for byte. Synthetic hook checks verify
all targets and allowed regions, and corrupt each guard individually to prove
failure leaves the input unchanged. Missing `BRIDGE_DISPATCH` must fail. Reports
go to ignored `work/build/difficulty-armips-port/check.json`.
The recovery branch predates the armips toolchain; use the current checkout's
includes with `--include-dir` until that branch has been rebased or integrated.

## Remaining full migration

Recover and reconcile the final C dispatcher, codec, policy/menu/gameplay sources,
and their later edits first. Pin and revalidate their input addresses against the
current build, including the current TEXT SPEED Options changes. The current
registry supports ITCM/overlay payload placement but not this research's extra
ARM9 main-memory autoload section: that installation needs an explicit validated
build contract, not raw ROM writes hidden in a generator. Link reviewed C with
the required section layout, place its pinned payload through armips, and ensure
the dispatch symbol and wrapper addresses agree. Re-run memory ownership,
ARM7 exclusions, save lifecycle and UI/gameplay gates with fresh evidence.

The historical 48/24 ownership ledger is not restored by these static checks.
