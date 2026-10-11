# RC7 difficulty input compatibility review — 2026-10-10

The completed 47-fix English baseline was compared directly with the historical
difficulty input (`a5a418b277bf07390e7282413923ec34f1c364f4a96c88936d65a73a80d51f40`).
Private byte evidence is in the main checkout under
`work/build/rc7-completion-20261010/input-audit.json`; both input identities and
every changed span are retained there.

All 46 difficulty hook/edit declarations still match their expected bytes.
All 18 compatibility dependency ranges, all ten item-ownership ranges and the
three item-frame ranges are unchanged. Options overlay50, overlay9 and the
complete 4032-byte ITCM section are byte-identical. Autoload, BSS, arena and
overlay bounds satisfy the existing installer checks without changed limits.

ARM9 differs only at the Pryce weather rule's guarded instruction. Every
overlay14 difference lies entirely within a production build-report region of
one of: battle healing, message variants, party-status sync, Cute Charm,
double targeting, faint timing, Honey Gather or zero-PP Struggle. No unattributed
changed byte was accepted. Outside those sections, changes are overlay49
(Honey Gather), the two script-loss fixes in a012 and the approved startup bank
in a027. Installer logical preservation checks cover all those files.

The sole changed revival dependency is `ordinary_hp_dispatch`:
`0221FA1C..0221FA22` now computes the message record address before reading its
first parameter for the message variant; `0221FA4A..0221FA4C` reads the target's
battler for Heal Block. These exactly match battle-message-variant's declared
edits. They preserve HP effect dispatch, frame ownership, callback ancestry and
control flow. All other revival dependency ranges match. The CN hash is retained
separately for original-source checks; production installation always validates
the new English hash. Native item positive/negative validation remains required.

The full-ROM, ARM9 and overlay14 pins were updated only after this review.
Original input metadata remains in `compatibility.json` and revival pins.
No hook guards, overlap checks, memory limits, source/tool checks or final logical
preservation checks were disabled. The production TEXT SPEED verifier's newer
compatible-region checks were source-pinned; its compiled payload and sources
remain unchanged.

This establishes static compatibility, not native acceptance or release readiness.
The comprehensive native suite and production gates must pass on the final
source-bound candidate before publication.
