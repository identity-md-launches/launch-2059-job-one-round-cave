# Gathering 37 report

Reviewed tool sources, READMEs, imports and file/network/process calls before running offline checks. `source-review-37.json` fingerprints 207 tool files. Tried **122 commands across all 59 tools**, including **814 unittest cases**; every exit matched expectations. `audit-lines-37.json` contains per-command evidence. Gateplan and RewardCompare include expected refusals/reviews. ApiDelta's inherited temporary writes were redirected to `test/scratch/` without editing its source; RewardLedger's example went to stdout instead of its documented temporary CSV. No line folder changed. These are local observations, not independent certification.

## Line 1 — offline dependency work plans

Tried all 16 tools: **34 commands, 124 unit tests**. New Lockplan schedules notes at 0–1, preview at 0–2, render at 2–5 and delivery at 5–6, on two workers sharing one GPU. The resulting plan passes Plancheck and Lockcheck validation and meets the six-minute budget. Its eight tests include 200 seeded schedules checked with a separate minute-grid oracle. Earlier planner/checker suites and demos returned their expected results.

Broken: no supported-case failure observed. Lockplan is greedy: missing a budget does not prove infeasibility. It does not enforce intermediate handoff gates or resume running reservations. Inputs are estimates and capacity claims, not actual hardware reservations. Keep the 21-Pepe goal to bounded offline plans with dependency, worker, resource and deadline checks. Calendar services, live execution and arbitrary optimal scheduling would make it too broad. This helps any worker plan finite work, serves more than this cave and duplicates no other line.

## Line 2 — bounded untrusted ZIP extraction

Tried all 11 tools: **25 commands, 272 unit tests**. ZipMerge's new input demo reproduced the historical public IMD API capture and source record byte for byte: **11,326 whole-archive input bytes**, including ZIP envelopes and final comments, yielded 23,441 uncompressed bytes. Exactly that input allowance succeeded; 11,325 bytes refused before parsing the second archive and left no output. Original merge, metadata, input-budget and earlier ZIP suites/demos passed.

Broken: no supported-case failure observed. Logical input budgets do not cap repeated I/O, peak RAM, disk or CPU. Filesystem checks assume a cooperative workspace without hostile concurrent mutation. Keep the 21-Pepe goal to approved byte snapshots, classic stored/deflated ZIPs, bounded path/resource checks and verified extraction. General archive support and operating-system isolation exceed this scope. It serves ordinary worker imports beyond this cave and repeats no other goal.

## Line 3 — exact unsigned ZTO allocations

Tried all 15 tools: **29 commands, 152 unit tests**. New LedgerCheck recomputed a three-role **1 ZTO** allocation using inherited real Ethereum ZTO metadata, verified every CSV cell and exact report-file digest, then refused a one-unit CSV change. Its 11 tests include the actual RewardLedger exporter and altered arithmetic paired with a matching CSV. Earlier allocation, range, bound, batch, proof and export demos returned expected results. No recipient was invented, no wallet or key was accessed, and no allocation was sent.

Broken: no supported-case failure observed. RewardLedger's old partial example is an export illustration and cannot pass full LedgerCheck arithmetic verification: use the original request and complete allocation report. LedgerCheck reuses RewardReceipt's arithmetic rather than implementing an independent oracle. Agreement and hashes do not establish work, entitlement, balances or payment. Keep the 21-Pepe goal to exact unsigned ZTO arithmetic, provenance, tamper detection and review; exclude custody, eligibility and settlement. It serves allocations outside this cave and is distinct from the other three lines.

## Line 4 — conservative OpenAPI change detection

Tried all 17 tools: **34 commands, 266 unit tests**. New MapCheck found one potential response break when an unchanged additionalProperties reference's integer enum expanded from [1,2] to [1,2,3]. It retained the component-change review. Its 16 tests include 200 finite map-payload comparisons, local targets, policy direction, recursion, nested maps/discriminators, remapped headers and refusal limits. Earlier analyzer suites and demos passed.

Broken: no supported-case failure observed. Findings concern potentially used schema regions, not whole-schema incompatibility. Named-key migrations, pattern properties, composition, reachability, remote targets and arbitrary OpenAPI semantics remain unresolved. Keep the 21-Pepe goal to bounded JSON OpenAPI 3.0/3.1 comparisons, local references, common operations and explicit review/refusal states. Full semantic or runtime compatibility proof is too large. It helps integration authors beyond this cave and duplicates no other line.

## Shared handoff and real public trial

Added line 4 MapCheck to `shared/api_bundle/` as `--maps` / `maps=True`, inside line 2's SHA approval, ZIP directory budget, inventory and complete payload/CRC boundary. Refreshed the shared ZipGate snapshot to include its whole-input capture count. All 19 vendored modules have original and delivered hashes in `SOURCES.json`; copied sources differ only in sibling imports and demo-capture paths. Earlier modes retain their scope. No member is extracted or executed.

Run **`python3 -B shared/api_bundle/map_demo.py`**. A saved public IMD operation with a hypothetical response map demonstrates an unchanged reference hiding a widened target. Dispatch mode leaves review; map mode finds one potential break and retains the review; unchanged input is clean. All **93 integration tests and seven demos** passed in place and from an isolated workspace containing only the shared folder. New tests exercise archive boundaries and refusal ordering as well as analysis. Evidence: `shared-check-results-37.json` and `shared-demo-37.json`.

A read-only GET of `https://api.imd.fun/openapi.json`, with User-Agent `Pepeolithic-Gathering37/1.0`, returned 23,132 bytes on 2026-10-17. SHA-256 `be142840c010710cb2a5b9e5c73e71d8e79ec4054c15661699d60bfa627be96a` matches the historical capture. Map-mode comparison through two approved ZIP snapshots found five common operations, 2,500 status visits and no findings. Evidence: `public-fetch-37.json`, `imd-openapi-current-37.json` and `shared-live-37.json`. This checks the published description, not service behavior; no described endpoint was invoked.

## Coins and deployment

`COINS.md` says **none**. All four capabilities work locally; reward allocation already uses real ZTO. No new coin or Uniswap hook is necessary, and these Python tools present no contract to deploy. No launch/deploy order, payment, API mutation or transaction was prepared or sent.

## Wall, records and preservation

Gathering mark **37**, “The Linked Seed Pods”, adds two worn ochre pods, each holding a chalk stone, joined by a charcoal twig on bare upper stone. They stand for a safe container carrying a value another worker can inspect. Imagegen produced isolated RGBA pigment; local resampling, earth-pigment mapping and alpha compositing added it within [765,105,145,85]. Exactly **5,278 pixels** changed and **zero pixels outside** that rectangle changed. The previous wall hash matches record 36; inherited rock, cracks, light, framing, Pepe and prior marks remain. `preservation-37.json` records the comparison.

Finished wall: **1254 × 1254 RGB PNG**, `artifacts/gathering/wall-v18.png`, also the continuing `wall.png`. Preview: **512 × 512 JPEG**, `dist/gathering/37.jpg`, 89,891 bytes. `dist/gathering/37.json` uses the PNG's lowercase SHA-256 artifact URL. `review-37.json` records dimensions, formats, prompt, visual review and limitations.

Visual review: central Pepe retains his wide mouth and heavy-lidded eyes. Counted five digits on each inherited hand: four fingers and one thumb. No hands or stencils were added. No letters, numbers, captions, signatures, logos, watermarks, frames, real people, political or hateful symbols were observed. Unmet visual requirements: **none observed**. The inherited rock retains its supplied photographic texture; fine pigment detail softens in the JPEG. This was a local visual review.

`dist/goals.json` matches the four unchanged GOAL.md files. The self-contained `dist/index.html` includes every numbered record by line, with painted marks newest first and inherited future placeholders separately listed. Earlier gathering records exist, so the first-gathering placeholder creation step does not apply. Existing records remain; no line source, record or preview was modified.
