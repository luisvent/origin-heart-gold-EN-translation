# English AI build: the recorded references

Recorded by `run.py quick --record` and `run.py deep --record` on 2026-10-13, 3 emulators.

| Input | Identity |
|---|---|
| ROM | `work/build/advanced-ai/layout/rom/rc8_ai.nds` (the rc8 release + the AI installer), sha256 `1e91ce1f7f7f6a45c5b10adae6071395d7d1c1a2bd06a74c8ff200497a98665b`, SHA-1 `22da8052b6719458fb92d7bfaef080b4d163a18a` |
| Payload | `work/advanced-ai/payload/payload.json` at commit `cb4ca7e` (layout `en`) |

| File | Command | Result |
|---|---|---|
| `bench.json`, `bench_record.json` | `aibench --advanced --repeats 1`, 364 scenarios | 98.1%; 0 fallbacks, 364 of 364 decisions from overlay 10, polls max 5, 0 errors; 30 runs with clipped text (below) |
| `aiprops.json` quick | `aiprops --n 20 --seed 1` | 109 checks, 0 violations, every side served |
| `aiprops.json` deep | `aiprops --n 100 --seed 1` | 549 checks, 1 violation, every side served. The violation (`hp p0072 T`) is listed as known: the archived Spanish tool reports the same one on the Spanish rc44 ROM, so it belongs to the Spanish AI, not to the port or our build. A reviewer must confirm it |
| `aivsai.json` | `aivsai 40 --seed 101` | 72 of 80 (90.0%, Wilson 81.5-94.8%); 32 scenarios 2-0, 8 split; 18.5 turns; 0 fallbacks of 1,474 decisions, polls max 8; 0 wrong decisions; 0 asserts, freezes or NULL allocations; 156 clipped-text notes in 63 games |

The other steps of the same runs passed: `aimode_check`, `lead_check`, `read_check`, `menulock` (the four foe cases),
`ai_smoke`, `fscheck`, `storycheck` (its Route 3 case INHERITED), `itcm_arena`, and `aifuzz --double --mode advanced`
after the move-message fix (see below).

## Notes

- **Clipped text.** Our ROM draws some ability pop-ups past the window's declared size (inside its buffer: a 'clipped'
  note, not an 'outside' failure), e.g. 'Blazing Awe', 'PsychicSurge', 'Inner Focus'. The same bench scenarios clip
  with the AI off (the hack's AI deciding), and the Spanish rc44 has none, so it is our build's text, not the AI. The
  bench holds the count to the reference; the AI-vs-AI report lists them for review.
- **Win rate.** 72 of 80 here against 71 of 80 on the Spanish rc44: the same AI code, other data (the Spanish build
  edits Pikachu's and Butterfree's base stats, among others).
- **The fuzz.** The first deep run failed `aifuzz`: four battles had the Searing Shot and Fire Pledge animation
  asserts the Chinese ROM has too, but our ROM breaks 'used' and the move name over two lines, so `lib/failures.py`
  neither found the message nor read the move (and named the battle's previous move instead). Fixed: `USED` also
  matches the line-broken message and `move_id` reads a line break as a space. Rerun (`run.py deep --only fuzz-doubles`): passed, 50 battles, 0 with problems, 6 with the inherited animation asserts, 0 fallbacks of 586 decisions.

## Later runs judged against these references

| Run | Result |
|---|---|
| `run.py static` on `rc8_ai.nds` | 9 of 9 steps passed in 28 s (`hostai/replay.py` and `sim/bench_check.py` replayed `bench_record.json`) |
| `run.py quick --options-receipt work/build/advanced-ai/options/difficulty_dev.receipt.json` on `difficulty_dev_ai.nds` (sha256 `10ad6aab…ae40`: the development difficulty build with the TRAINER AI row + the AI) | 8 of 8 steps passed in 20.3 min: the bench 98.1% with every scenario's action the same as the reference, 0 fallbacks, the same 30 clipped runs; the Options row check passed |
| `run.py deep --only props-full` on `rc8_ai.nds` | passed: the known `hp p0072 T` only |
| `run.py deep --only versus` on `rc8_ai.nds` | passed in 18 min: 72 of 80, 0 fallbacks of 1,474, **all 80 logs byte-identical to the reference** |
| `run.py deep --only fuzz-doubles` on `rc8_ai.nds` | passed (the rerun above) |
