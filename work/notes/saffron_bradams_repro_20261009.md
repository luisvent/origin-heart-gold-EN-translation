# Saffron relearner: Bradams NoBigText reproduces — 2026-10-09

Follow-up to D-1589 and the historical research branch `codex/saffron-relearner-investigation`
(`76295b3`). The user suspected that reports from Bradams' fork had been attributed to our build.
Fresh evidence is recorded as **D-2299**, related to D-1589 and the existing msgload decision D-1390.

## Result

The locally supplied **NoBigText** ROM black-screens when opening Saffron's move relearner for a
level-100 Gallade. The relearner's heap 66 fails a **27,016-byte allocation**, matching message
bank 739 (move names). The native application never returns to field movement.

**Speedoption and RC7 pass** the same six-visit full-party stress sequence. A causal control on
the exact NoBigText ROM passes when only message loading is forced to on-demand mode through
a RAM execution hook. No ROM file or heap-size constant was changed.

This reproduces a failure in an older locally supplied fork build, not a current RC7 defect.
It supports the user's concern about mixed report provenance. It does **not** establish that
Bradams' enlarged buffers caused this crash: this NoBigText ROM has the Chinese root-heap size
and the unchanged relearner heap. The immediate cause is loading expanded English banks into a
fixed-size heap without the global per-line loading fix already present in our RC4+ releases.
Which earlier release introduced or inherited the omission is not established.

## Local artifacts

No download was performed. Both supplied patches remain in `/Users/contributor/Downloads/`.

| Artifact | SHA-256 |
|---|---|
| `Pokemon Origin HeartGold NoBigText.xdelta` | `4b537e721a0e9065b1a9141d14e2ea7068efc8a682695c05b64289109ba5ddf2` |
| `Speedoption.xdelta` | `dea9758315c1345e13c1199268cda33517148ab98d3d27526c570b41bf3e8c4e` |
| Decoded NoBigText ROM, `work/build/bradams-audit/nobigtext.nds` | `5e7de6aac1a8d83276a709b4a3ab1e3a55d6adff10a890d22b339b10c951dd2b` |
| Decoded Speedoption ROM, `work/build/bradams-audit/speedoption.nds` | `c95961d1b335e351299750676037a1348dfb3f449162dbf3021751c47c4afe3f` |
| RC7 candidate ROM, `work/build/rc7/candidate/origin_hg_v4.0.3_en_wip.nds` | `b16f81bec13b07730ee544fbe24aead4229eccf04368f186aa71abe0b48710df` |
| Original Chinese ROM | `4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8` |
| Source battery save, `work/build/origin_hg_v4.0.3_en_wip.sav` | `969c722ae83595bdb4af476d0b03d6048c41cdcec8f345788fa90c13080f4b51` |

ROM and source-save hashes are checked before and after each completed run. The harness uses a
private save copy with 20 Heart Scales. Generated Pokémon are created by the game's native debug
generator; the tested Gallade is valid and has 27 eligible moves. No bank translation was changed.

## Fresh runtime results

Native DeSmuME 0.9.12. RTC fixed to 2026-10-09 12:00. Evidence directory:
`work/build/saffron-bradams-20261009/` (ignored; contains private game data).

| Run directory | Interaction | Result | Live heap checks |
|---|---|---|---:|
| `speedoption-retry` | Full party; Bag before each visit; no reset; Gallade, repeat, Gardevoir, Alolan Ninetales, Mewtwo, repeat | **6/6 pass** | 668 |
| `rc7` | Same sequence | **6/6 pass** | 668 |
| `nobigtext` | Same sequence | First Gallade opens the app, allocation fails, both screens black. Later failures are consequences, not independent reproductions. | 121 |
| `nobigtext-simple-v3` | Fresh boot; original party selection then separately reset/generated Gallade; no Bag or full-party pressure | Original lead correctly has no eligible moves; **Gallade reproduces the allocation failure** | 195 |
| `nobigtext-on-demand-v3` | Same simple sequence; only force constructor input mode 1 in RAM | Original lead correctly rejected; **Gallade opens, scrolls every move description, cancels and walks away** | 194 |
| `chinese-v3` | Same simple sequence on untouched Chinese | Original lead correctly rejected; **Gallade passes** | 194 |

The passing opened-app cases require the selected native party pointer to match, every eligible
move description to be read, no native assertion/allocation failure/string overflow/heap corruption,
20 Heart Scales after cancellation, and resumed field movement. The empty-list control is recorded
as a rejection, not counted as a successful app-opening test.

The failure is during initialization, not caused by pressing Cancel. The harness reports
“No field movement after cancel” because that is its final completion check. The earlier event
log and screenshot establish the actual trigger.

## Failure trace and causal isolation

`nobigtext-simple-v3/events.jsonl`, generated Gallade:

1. Frame 9750: relearner opens; bank 736, heap 66, constructor mode 0.
2. Frame 9750: bank 739, heap 66, mode 0.
3. Frame 9755: bank 738, heap 66, mode 1.
4. Frame 9762: bank 739 requested again, heap 66, mode 0.
5. Frame 9762: allocator returns NULL for **27,016 bytes**, heap 66, caller `0x0201B2CD`.
6. Screenshot is black on both screens; field movement does not resume.

The earlier full-party reproduction also failed heap 66 immediately after app opening.
The simplified reproduction removes previous Bag use and full-party pressure as prerequisites.

| Inspected region/value | Chinese | NoBigText | Speedoption | RC7 |
|---|---|---|---|---|
| ARM9 `0x0200BA9A` | `adds r5,r0,#0` | same | `movs r5,#1` | `movs r5,#1` |
| Root heap 3 size | `0x11D000` | `0x11D000` | `0x125000` | `0x11D000` |
| Relearner heap 66 size | 147,456 bytes | same | same | same |
| Move-name bank 739 bytes | 15,226 | 27,016 | 27,016 | 27,016 |
| Whole overlay 65 SHA-256 | `e5f01613eed0588738140d9ab144c227d41ac3058e0b8db1c1f0f121d07d4469` | same | same | same |

The diagnostic hook runs at `0x0200BA9A`, immediately before the original instruction copies
the mode from r0 to r5; it sets r0 to 1. All other code and data remain NoBigText's. This is
the existing `msgload-all` behavior tested without changing a ROM or importing Speedoption's
heap/task/pacing changes. It is sufficient for the reproduced case to pass.

See [existing msgload registry](../patches/msgload/fix.toml) and
[heap audit](heap_audit.md) for the production fix's earlier provenance.

## Why the earlier investigation missed this

The 53-run D-1589 matrix included Chinese, RC4, RC5, develop and **Speedoption**, not a NoBigText
runtime run. The later research branch also ran Speedoption, with four generated species.
Its static audit correctly found identical relearner code in both fork ROMs, but that does not
make their global text-loading modes identical. The present comparison establishes the difference.

Keep D-1589's other player reports unresolved as to exact provenance unless their ROM/save can be
identified. This does not prove every reported Saffron failure was the same defect. Historical
MoreSpace/AntiPirate/intermediate builds were not available for this test.

## Reproduction code and limits

The fresh stress runs reuse `work/build/saffron-retry-checkout/work/tools/emu_saffron_retry.py`.
The bounded diagnostic copy is `work/build/saffron-bradams-20261009/probe.py`; it adds allocator
request-size tracing, message-mode tracing, optional RAM-only mode forcing and stops after the
first failed case. `run_followup.py` runs the simple comparison and Chinese control. All commands
were launched from the repository root; the old harness internally uses a temporary directory.

The initial sandboxed emulator process aborted before gameplay; reruns required sandbox escalation.
The first two diagnostic attempts stopped before gameplay because a relative command-table path
did not survive the harness's internal directory change; only `*-v3` results are evidence.

These fresh runs test app opening, scrolling, rejection and cancellation. They do not newly test
actually spending a Heart Scale, every party slot, other emulators, or hardware. Earlier successful
learning/replacement tests remain separate historical evidence. No production tools or ROM patches
were changed, no ROM was built, and nothing was committed or published.
