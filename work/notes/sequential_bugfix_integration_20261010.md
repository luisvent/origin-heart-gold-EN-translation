# Sequential bug-fix integration — 2026-10-10

D-2300 final catalog repair only. The six enabled patches and their preceding
paired-build proofs remain unchanged. No emulator rerun, download, commit,
publication or source-save edit. Existing dirty work is preserved.

`work/tools/test_asmpatch.py` now includes zero-PP Struggle in its 18-source
inventory and isolated/combined GOLDEN snapshots, with the actual 66 regions and
four strings. Assembly against the original Chinese ROM proved the 240-byte
guard SHA-256 is
`4a5379d57c1e260a8d31cac1113f43a0a199fef78371ea7b4e6a9d4972dda050`.
Exactly 193 bytes differ, all within overlay14 offsets 0x2BD70–0x2BE5F
(actual changed offsets 0x2BD8A–0x2BE5F). Outside that region the isolated image
is unchanged; adding Struggle to the preceding combined image changes only that
region, with every other binary and the overlay table unchanged.
Private proof: `work/build/bugfix-sequential-20261009/final-integration/assembly-proof.json`.

| Snapshot | overlay14 SHA-1 | y9 SHA-1 |
|---|---|---|
| Struggle alone | `e795daa8e750b49eda8b48d4e5fc02bf29b10613` | `14a857a74185e918becc63b963a4a7b5a0cf8688` |
| All 18 armips sources | `14bf431f2451fe8d1c8e0d71de1bc3f5cbd0ed9d` | `3483751df97682d807071808d46d411fd316a428` |

`work/tools/emu_fixes.py` now truthfully lists all six patches as gaps in that
unified command, citing their separate verification and its limits. Inventory:
42 enabled fixes, 32 covered by unified scenarios, 10 explicitly listed gaps.
Neither coverage judges nor registry checks were suppressed.

| Patch source (`work/patches/<id>/fix.toml`) | Verification sources |
|---|---|
| `zero-pp-struggle` (+ `.asm` / `.listing`) | `work/tools/emu_struggle.py`, `work/tools/test_zero_pp_struggle.py`; issue03 fix note |
| `rock-tunnel-corner-loss` | `work/tools/emu_rock_tunnel.py`, `work/tools/test_rock_tunnel_corner_loss.py`; issue05 fix note |
| `magcargo-loss-whiteout` | `work/tools/test_magcargo_loss_whiteout.py`; private `work/build/bugfix-sequential-20261009/issue06/fix/runtime.py`; issue06 fix note |
| `expedition-completed-progress` | `work/tools/native_script_state.py`, `work/tools/test_shared_progress.py`; private issue10 paired matrix; issue10 fix note |
| `hooh-panel-silver-marker` | Same issue10 native-handler matrix, 104 cases per build; issue10 fix note |
| `mortar-invalid-flag-noop` | `work/tools/native_script_state.py`, `work/tools/test_story_flags.py`; private issue09 paired matrix, 20 cases per build; issue09 fix note |

The Magcargo runtime source SHA-256 remains
`277643e62576634f562839796a3eb2a67ea6bb199ea97ac927eb506b6545b1d8`.
Rock Tunnel victory evidence remains limited. Magcargo's other battle outcomes
are structurally verified. Complete shared-progress/Mt. Mortar scenes, map
reload and native save/reload remain untested; no full-game coverage is claimed.

Focused armips/emulator-inventory suite: **106 tests pass**. Changed-file ruff
passes. Final command:

```sh
.venv/bin/python work/tools/check.py --full --armips $HOME/Developer/armips/build/armips --work-dir work/build/bugfix-sequential-20261009/final-check-rerun
```

Final full check: **998 tools + 46 docs + 36 site tests = 1080 tests, OK;
26 skipped**. Registry, FIXES.md, synthetic assembly, prerequisites, real
assembly, all 18 listing snapshots, 20 USA claims and build pass. The only
failed step is ruff: **36 preexisting findings, exclusively in untracked
`work/research/difficulty-armips`**. That tree and lint exclusions are untouched.
Overall exit status is therefore 1, not a complete full-check pass.

The final ROM and xdelta are byte-identical to the coordinator's preceding full
build. `expected.toml` was not refreshed by this stage.

| Fingerprint | Value |
|---|---|
| Nontext SHA-1 | `4d3b11d1ce0f1754c4885c115f1a1f40f1614b64` |
| Text SHA-1 | `922a51f5639fda62fce76bc678793c050fac7a46` |
| ROM SHA-1 | `4167ea2c4999edb5359d945977bc7433cad2a91e` |
| ROM SHA-256 (278780608 bytes) | `af0641ced20e830b9f27a4d0771e1478308cfc4dcdd537030d4e50d06e6299bd` |
| Xdelta SHA-1 | `afe14e3519b7535d0bd95b50b9d767cbf9b0cd5c` |
| Xdelta SHA-256 (43561517 bytes) | `082d63f5e056e619650a945344ffc1275728a665c01fe15e3f4e2581bb593d9b` |
| Preserved root ROM SHA-256 | `6fa7b4e739391ca9ea9bfcf90d83eec6407c3c04102e52432bb41bc8ae44a7d3` |
| Preserved RC7 candidate ROM SHA-256 | `b16f81bec13b07730ee544fbe24aead4229eccf04368f186aa71abe0b48710df` |
| Preserved expected.toml SHA-256 | `ae51947956103fbaa3fdb38adab53071a9c2cd63d25f9f0e81a555d355503797` |

Log: `work/build/bugfix-sequential-20261009/final-check-rerun.log`.
Exact machine-readable counts, hashes and preservation checks:
`work/build/bugfix-sequential-20261009/final-integration/final-summary.json`.
