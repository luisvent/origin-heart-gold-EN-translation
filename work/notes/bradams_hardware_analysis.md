# Bradams fork: memory, hardware, reflection and PC binary audit

Audited 2026-10-05. Read-only analysis of decoded `Speedoption.xdelta`, the locally available earlier `NoBigText.xdelta` image, untouched Chinese v4.0.3 and the current translation's patch register. No production code or ROM changes. Addresses below are runtime addresses; overlay-relative offsets are given separately. Static disassembly establishes instructions and control flow, not successful hardware execution. NoBigText is an earlier modified build, not an unmodified translation baseline. Intermediate release patches are needed to date changes accurately.

## Findings at a glance

| Feature | Binary result in Speedoption | Practical interpretation |
|---|---|---|
| Bulbasaur reflection | One conditional branch includes sprite ID 428 | Specific boundary repair exists; unrelated R4 encounter freezes are not explained by it |
| Global task capacity | Main task queue 160 → 255 entries | Actual capacity increase, +3,040 bytes; other queues stay 32/32/4 |
| Failed task/state allocation | Two wrappers retry up to 64 times | Tight synchronous retries, with no frame wait or scheduled cleanup; not a general null-safe recovery |
| Summary/bag memory | Larger heaps plus on-demand text loading | Real changes, but on-demand loading already exists in our translation |
| Alleged unused stack reuse | Main heap 3 +32 KiB; no observed stack-limit change in the localized diff | Do not repeat the chat's stack-safety claim as proven |
| Antipiracy | Six overlay114 routines become constant returns | Clear bypass stubs, separate from heap/task changes; no proof all crashes were AP |
| PC wallpaper | Relevant overlay and wallpaper NARC unchanged | Reporter's suggested repair is absent |
| Original developers removing hardware support | Not established in examined local sources | Compatibility trouble does not establish deliberate removal or author intent |

## Reflection boundary: precise one-byte change

Overlay1 loads at `0x021E4980`. Relative `0x1191A`, runtime `0x021F629A`, changes halfword `DD07` to `DB07`: `ble 0x021F62AC` becomes `blt 0x021F62AC`. Immediately before this, `mov r1,#0x6B; lsl r1,#2; cmp r0,r1` compares with **428**. The old branch excludes values less than or equal to 428 from the following case; the new branch excludes only values less than 428. The upper-bound comparison and selected call `0x0205E588`, followed by `ldr r0,[r0]`, remain unchanged. This matches the author's stated off-by-one repair for the first follower sprite/Bulbasaur. It does not change species stats, party data or general collision logic.

Only one byte differs in the entire overlay between NoBigText and Speedoption. The binary proves the boundary modification; associating it with the observed reflection freeze uses the precise chat reproduction, not a fresh runtime reproduction. [Author diagnosis](https://discord.com/channels/1554815898848731217/1555205598860288140/1555413548128276582).

## Task-capacity increase

ARM9 `0x0201AA1C` and `0x0201AA2E`: `mov r0,#0xA0` → `mov r0,#0xFF`. The first feeds `0x0201FFEC`, which computes `count*32 + 0x34`; the second feeds task-queue initialization `0x0201FFF4`, which stores the count as a halfword and initializes the free/task lists. The resulting queue pointer is stored at main-system structure offset `+0x18`. Task creation `0x0200DE74` reads precisely that pointer before calling `0x02020080`.

Thus this is 160 → 255 task slots, not a heap-size constant or text-speed limit. Its allocation grows from `0x1434` (5,172) to `0x2014` (8,212) bytes, +3,040. Adjacent initializations for the queues at system offsets `+0x1C`, `+0x20`, `+0x24` remain 32, 32 and 4. Saying every queue was enlarged would be incorrect.

## Allocation retry hooks and their limitations

The state/task constructor at `0x0200711C` allocates an optional state block, zeroes it, and creates a task. Two calls are redirected:

| Hook | Old callee | New callee | Purpose |
|---|---|---|---|
| `0x0200712A` | `0x0201B2AC` | ITCM `0x01FF8D4C` | Allocate requested state buffer |
| `0x02007148` | `0x0200DE74` | ITCM `0x01FF8D6C` | Create main-queue task |

Both wrappers save r4–r7/lr, copy r0–r2 into preserved registers, set a counter to `0x40`, repeatedly restore the arguments and call the original routine, return immediately on nonzero r0, and decrement/retry on zero. After 64 failures they still return zero. There is **no VBlank wait, yielding, task-queue processing, garbage collection, freeing of a block, or substitute object** inside either retry loop. An interrupt might change outside state, but no reliable progress mechanism is provided here. Therefore the binary does not support a claim that it "waits a few frames" for memory or guarantees recovery.

The caller already checks allocation failure at `0x02007130` and returns zero; that check is unchanged. The task-creation return is still returned directly to its caller. If task creation fails after allocating its state, this wrapper does not free that state before returning. Static inspection therefore finds an incomplete mitigation rather than comprehensive lifetime/null handling. Raising the queue limit is a much more direct explanation for avoiding task exhaustion than immediately retrying an unchanged full queue. [Task discussion](https://discord.com/channels/1554815898848731217/1555205598860288140/1555416292830347385).

## Memory sizes and text loading

| Location | Previous value | Speedoption | Mechanism |
|---|---:|---:|---|
| Main heap initialization table, `0x020F2EC4` | `0x11D000` = 1,167,360 | `0x125000` = 1,200,128 | Fourth root heap size, +32,768 bytes |
| Summary setup, `0x02087370` | `0x45 << 12` = 282,624 | `0x5A << 12` = 368,640 | Heap19 created from parent3, +86,016 bytes |
| Bag setup, overlay17 `0x021F8716`, rel `0x36` | `0x42 << 12` = 270,336 | `0x50 << 12` = 327,680 | Heap6 created from parent3, +57,344 bytes |

The root heap table begins `0x020F2EAC`, is passed at `0x0201A9E6` to `0x0201AFDC` with count four, and contains size/arena pairs. Only its fourth size changes. This is evidence of additional heap reservation. It is **not** evidence of a proven safe stack-to-heap transfer, nor a lower-screen-exclusive pool. The summary and bag heaps are larger consumers of their parent. Their increments are not proof they coexist, and should not simply be summed as permanent use. Main task storage grows separately. No stack-bound/stack-pointer change is among the observed localized NoBigText→Speedoption ARM9 differences. [MoreSpace author's claim](https://discord.com/channels/1554815898848731217/1555205598860288140/1555491666507599937).

At `0x0200BA9A`, `adds r5,r0,#0` becomes `movs r5,#1`, forcing all calls to the message-data constructor into the on-demand mode. Additional caller changes set r0=1 at summary `0x0208799A`, `0x02087A0C` and bag overlay17 `0x021F9020`, `0x021F9050`, `0x021F9062`. These individual changes are redundant while the global override remains active. They avoid loading complete expanded English message banks into tight screen heaps, at the cost of individual reads.

This is **not a new text-speed feature**. Our `code_patches.json` and `heap_audit.md` already describe the same global message-loading fix and five call-site overrides, with prior emulator measurement. Do not import a duplicate or attribute the concept's origin to Bradams solely from this binary. Similarly, a full fork diff includes inherited translation changes; exact build ancestry remains uncertain. The extra heap sizes and retries should be evaluated separately from our existing fix.

## Six constant-return routines associated with the antipiracy release

Overlay114 loads at `0x02263200`; size stays 4,896 bytes. Its contents match exactly between untouched Chinese and NoBigText. Speedoption changes six 8-byte entry sequences, 48 bytes total:

| Offset | Runtime entry | Return r0 |
|---:|---:|---:|
| `0x864` | `0x02263A64` | 0 |
| `0x94C` | `0x02263B4C` | 1 |
| `0xA34` | `0x02263C34` | 0 |
| `0xB1C` | `0x02263D1C` | 1 |
| `0xC04` | `0x02263E04` | 0 |
| `0xCCC` | `0x02263ECC` | 1 |

Each original entry begins ARM instructions `push {r4,r5,r6,r7,r8,r9,r10,lr}; sub sp,sp,#0x80`. Each replacement is ARM `mov r0,#0` (`00 00 A0 E3`) or `mov r0,#1` (`01 00 A0 E3`), then `bx lr` (`1E FF 2F E1`). The remaining routines' bodies stay in the file but cannot execute through those entries. The original bodies contain address-relative setup and protected-looking code sequences; a six-stub bypass is established, but full deobfuscation of each original predicate and all callsites has not been completed.

Consequently: these are actual runtime code bypasses, not merely changing a ROM header so a flashcart recognizes the title. They are present even in the speed-toggle beta. The AP interpretation fits the author's release account, but which particular predicate detects which cartridge/loader condition, and whether it intentionally fills a buffer, remains unverified. There is no basis here to say all previously observed heap crashes were antipiracy: the task and text allocation changes address independently identifiable constraints. [Author's AP explanation](https://discord.com/channels/1554815898848731217/1555205598860288140/1555823192298491957).

Getting `AntiPirate.xdelta` and its immediate predecessor `PokemonOriginHeartgoldFixed.xdelta` would isolate exactly what the named AP release added. Getting `MoreSpace.xdelta` and `PokemonOriginHeartgoldBulbaFix.xdelta` would determine which capacity/retry/heap changes first shipped and whether any were subsequently lost.

## PC wallpaper repair is absent

Overlay16 is byte-identical across Chinese, NoBigText and Speedoption (SHA-256 `b5ba89bce5ff33c779d4bb84af0d4bc6caba8d2782b740ef59afe847d08b0894`). `a/0/1/9` is also identical (87 members; SHA-256 `f32982d5cc61721c879e037fc80f27cfdbecb0f95a5bff7c9027415a739159ae`). Thus the reporter's proposed changes to `0x021E692E`/palette indexing and archive expansion have not shipped in this beta. Larger unrelated heaps do not validate the out-of-range wallpaper index.

The report describes an invalid member argument, uninitialized output pointer after failed load, then a garbage DMA length/pointer. Those are reporter runtime observations, not reproduced in this static audit. Treat this as an unresolved original-hack investigation, especially because their claim includes untouched Chinese. [Detailed report](https://discord.com/channels/1554815898848731217/1555205598860288140/1555931888198226093).

## Hardware scope and original-author intent

The fork's edited opening post says **3DS compatibility, only tested to a point**, not universal NDS/R4 support. The chat includes successful New2DSXL/TWiLight reports and continuing original DS/R4 freezes after the AP build. The Bulbasaur boundary, text memory and task queue changes can affect emulators too. Hardware-specific causality must be tested, not inferred from the release name.

A targeted search of local project notes and the archived Chinese public-source corpus for hardware/real-console/flashcart compatibility terms did not establish an original-author statement that hardware support was deliberately removed. An archived third-party video title advertises phone/PC NDS emulation; that is not evidence of a developer decision to remove consoles. Binary differences cannot prove that intention either. Correct current position: hardware support/compatibility is unresolved; deliberate removal is unproven. No outside sources were downloaded for this audit.

For our project, adopting a new hardware compatibility objective is a product decision distinct from understanding this fork. The current fidelity policy also distinguishes translation regressions from original-hack bugs. This audit changes neither policy nor game behavior. Already-existing on-demand text loading can be kept on its established translation-memory rationale. New AP bypasses, task-limit changes and original-hack reflection fixes need explicit scope and actual platform tests before being called supported improvements.

## Validation needed before shipping any new compatibility change

Reproduce the exact reflection/water crossing with follower sprite428; test neighboring IDs; drive the Viridian Eevee/Joy sequence while measuring main task high-water mark and creation failures; measure root and screen heap margins rather than guessing from total sizes; exercise summary and bag from field, battle and PC; compare original DS/R4 with the exact New2DSXL/TWiLight setup; exercise fishing and many transitions with and without the six stubs; repeat the PC wallpaper reproduction independently. None of these runtime validations was performed in this static investigation.
