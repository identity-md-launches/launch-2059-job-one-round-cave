# MapCheck

Find potential breaking changes inside OpenAPI `additionalProperties` value
schemas. MapCheck extends DispatchCheck and retains every earlier line 4
analyzer. Python 3.9+ and the standard library are sufficient; keep the sibling
tool folders beside this one. It reads JSON descriptions and executes no API
operation.

From the repository root, run this offline demonstration:

```sh
python3 -B line-4/tools/mapcheck/mapcheck.py demo
```

The demo starts with the bundled real public IMD description. It adds a
**hypothetical** response map to a saved operation, with integer values allowed
by a referenced component. The reference text stays identical, but the
component's enum grows from `[1, 2]` to `[1, 2, 3]`. The demo finds **one
potential break** at `additionalProperties/enum` and retains the earlier
component-change review. It exits 0 after confirming the intended finding.
This example does not describe a change observed on the running service.

Compare local descriptions with:

```sh
python3 -B line-4/tools/mapcheck/mapcheck.py compare old.json new.json
```

Output is deterministic JSON with exact input-byte SHA-256 values. Compare
exits: **0** no detected break within the subset, **1** potential break,
**2** invalid/unsupported input or resource refusal, **3** review only.
Paths must resolve inside the current workspace. Neither inputs nor earlier
tool sources are modified. No third-party dependency, environment variable,
credential, coin, balance, payment or network access is needed.

## Supported behavior

The [JSON Schema object reference](https://json-schema.org/understanding-json-schema/reference/object#additionalproperties)
defines additional values as values of keys unmatched by the same schema's
`properties` and `patternProperties`. For each visited pair of schema objects,
MapCheck resolves both additional-value policies independently and:

- Traverses object-valued schemas, even when reference strings are unchanged.
- Uses the inherited request-narrowing and response-widening checks for types,
  enums, bounds, constants, uniqueness, dependencies and nested schemas.
- Treats omitted policies and `true` as unrestricted values. Closing requests
  or opening responses produces a potential policy break, including through
  references resolving to booleans. Existing reviews remain in the report.
- Follows nested maps, arrays, named properties and explicit discriminator
  mapping targets through the inherited local-reference and cycle guards.
- Reaches inherited request-body, parameter, response-body and response-header
  sites, including remapped response status fallbacks.

`map_pairs` records each visited nontrivial additional-value comparison's
location, direction and open/closed policies. Locations under
`additionalProperties` describe constraints on an arbitrary unmatched key's
value. The report also keeps dispatch pairs and response-selector groups.
Boolean schema support follows the inherited analyzer's conservative subset;
this is not validation of version-specific OpenAPI keyword legality.

## Limits and interpretation

A finding concerns a potentially used region of a schema. It does **not** prove
whole-schema incompatibility: other constraints can forbid objects, forbid
extra keys, or make the value schema unreachable. MapCheck does not infer
key-name migrations between `properties` and additional values, evaluate
`patternProperties`, merge compositions or implement `unevaluatedProperties`.
Arbitrary union branches, callbacks/webhooks and unused components remain
outside inherited traversal. An unsupported change can remain a review;
unchanged remote targets in unvisited regions are not checked. Exit 0 is not a
runtime or complete semantic compatibility guarantee.

Only local object-member JSON pointers are resolved; remote references,
unresolved pointers, alias cycles and semantic `$ref` siblings are refused
when visited. No reference is fetched. Bounds include **1,024 map pairs**,
512 dispatch pairs, 64 explicit mappings per discriminator, 20,000 schema
visits, 2,000 findings, 1 MiB/input, 50,000 input nodes, depth 80, and all
inherited operation/header/security/server limits. Budget refusal returns no
partial success report.

## What happened when tried

On 2026-10-17:

- `python3 -B line-4/tools/mapcheck/selftest.py`: **16 tests passed**, including
  **200** independently evaluated request/response policy pairs over **25**
  finite map payloads. Cases include recursive maps, local targets, booleans,
  malformed inputs, budgets, header fallbacks, discriminator nesting,
  determinism, nonmutation, retained findings and all CLI outcomes.
- `python3 -B line-4/check-37.py --live`: **266 tests passed in 17 suites**.
  Earlier suites ran unchanged, with temporary files redirected into
  `test/scratch/`. The demo found its intended break and review.
- A read-only GET of `https://api.imd.fun/openapi.json`, with User-Agent
  `Pepeolithic-MapCheck/37.0`, returned **23,132 bytes**, SHA-256
  `be142840c010710cb2a5b9e5c73e71d8e79ec4054c15661699d60bfa627be96a`.
  It matched the historical capture; five operations compared with zero
  findings. This description has no nontrivial visited map pairs, so it
  checks integration and unchanged behavior rather than live map semantics.
  No described endpoint was called. Evidence is in
  `line-4/check-results-37.json` and `line-4/live-openapi-37.json`.
