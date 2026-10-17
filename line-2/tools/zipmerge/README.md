# ZipMerge

Combine several independently approved ZIP archives into one new workspace
directory. ZipMerge checks every archive and payload through the shipped
ZipGate/SafeZip tools, refuses a repeated file, file/directory conflict or
case-colliding path across archives, and enforces shared entry, output node and
uncompressed byte limits and a shared whole-archive input budget. Identical shared parent directories are allowed. It
publishes the joined tree only after all checks and extraction passes succeed.
Python 3.9+ standard library only; no installation, account or network needed.

Run this one command from the repository root to see it work:

```sh
python3 -B line-2/tools/zipmerge/input_demo.py
```

Tried here: two illustrative ZIP packages contain the shipped historical public
IMD OpenAPI capture (23,132 bytes) and its source record. ZipMerge joined their
shared `docs/imd` directory, reproduced both files byte for byte, and refused a
shared whole-archive input budget one byte too small for both (11,325 bytes).
The exact 11,326-byte allowance succeeds, including archive comments and headers. The demo creates and removes disposable
data only under `test/scratch/`; it makes no fresh network observation. The
capture and provenance are in `../safezip/`.

## Shared metadata budget (round 36)

`merge_directory_bytes` / `--merge-directory-bytes` now caps the sum of all
central-directory byte lengths, defaulting to **2 MiB for the whole merge**.
The per-archive `directory_bytes` cap still applies. Before each archive is
parsed, ZipGate receives the smaller of its individual allowance and the shared
remaining allowance. Oversized later metadata is refused before ZipInfo objects
or payload streams for that archive are created; no output tree is published.
A zero-byte directory in an empty ZIP is allowed even after the allowance is
exhausted. Repeated shared directories count once as output nodes but their ZIP
metadata counts in every archive. Member names, comments and extra fields in
the central directory count; local headers and the final archive comment do not.
The existing per-archive compressed-input cap still bounds those other bytes.

The JSON report adds `metadata.directory_bytes` and
`metadata.directory_byte_limit`; existing `totals` fields keep their meaning.
This tightens the default for merges whose combined metadata exceeds 2 MiB;
raise the shared cap explicitly when that much reviewed metadata is intended.
It is a logical input budget, not a cap on peak RAM or on repeated I/O. The
existing digest-bound extraction pass rereads the same approved archives.

Tried the command above: the historical real public API capture and its source
record extracted byte-identically with exactly **6,925** metadata bytes. A
6,924-byte shared allowance was refused before ZIP parsing of the later archive
and left no destination. Added comments in these ZIP packages are illustrative;
the capture itself is unchanged. The original `demo.py` also still passes.

## Use

First inspect each archive with ZipGate and review its inventory and
`archive_sha256`. Each approval below must be the actual reviewed digest of its
matching archive; replace the example paths and destination with yours.

```sh
python3 -B line-2/tools/zipmerge/zipmerge.py plan --archive first.zip --sha256 FIRST_REVIEWED_SHA256 --archive second.zip --sha256 SECOND_REVIEWED_SHA256 --merge-nodes 100 --merge-bytes 1048576 --seconds 10
python3 -B line-2/tools/zipmerge/zipmerge.py extract combined --archive first.zip --sha256 FIRST_REVIEWED_SHA256 --archive second.zip --sha256 SECOND_REVIEWED_SHA256 --merge-nodes 100 --merge-bytes 1048576 --seconds 10
```

`combined` must not exist; its parent must already exist. All input and output
paths must be inside the current workspace with no existing symlink component.
Plan mode creates nothing. Python callers use `process(specs, output=None,
merge_nodes=..., merge_bytes=..., merge_directory_bytes=...,
merge_archive_bytes=..., seconds=...)`, where each spec is exactly
`{'archive': path, 'sha256': reviewed_digest}`. Omitting `output` plans only.

By default, at most 32 archives, 1,000 combined entries, 32,000 distinct output
nodes and 64 MiB of combined uncompressed data are accepted. The output root is
excluded from the node count. Per-archive limits retain ZipGate's defaults:
1,000 entries, 2 MiB central directory, 32 MiB archive snapshot, 32,000 nodes,
16 MiB per file, 64 MiB total bytes and 200:1 compression ratio. Every limit is
a positive integer. The central-directory gate runs before ZIP parsing. Its
snapshot digest must match the reviewed digest, and the extractor repeats that
approval and complete payload validation before staging. Input order determines
report order but never grants overwrite priority.

Exit 0 emits a JSON plan or extraction report. Exit 2 emits `ok: false` for
refusal, corruption or I/O failure. Untrusted archive content is never executed.

## Checks and limits

```sh
python3 -B line-2/tools/zipmerge/selftest.py
python3 -B line-2/tools/zipmerge/metadata_selftest.py
```

Observed 15 focused tests: exact shared limits, shared directories, no-output
plan, collisions, replaced/incorrect approvals, unsafe later archives, symlink
and corrupt members, later extraction failure cleanup, preexisting outputs,
cancellation, deadline, invalid
options and CLI success/refusal. This is an ordinary cooperative workspace
tool: a hostile concurrent process changing filesystem paths can race its
checks. The optional deadline is cooperative, not a hard CPU or memory sandbox.
Temporary staging needs disk space for the extracted inputs and joined tree;
there is no disk reservation. Only classic stored/deflated ZIP layouts accepted
by ZipGate are supported. Content hashes establish byte identity, not publisher
trust or content safety. No ZTO or IMD payment is needed for local extraction.

Round 36 verification: all 15 original merge tests, 10 new metadata tests and
28 unchanged ZipGate tests passed (53 total). New checks independently count
classic directory bytes, cover exact/one-under limits, empty archives at an
exhausted allowance, invalid options before input I/O, retained per-archive
bounds, CLI reporting and two large-comment archives that each fit individually
but exceed the shared default. A parser spy confirms the later refusal occurs
before SafeZip parsing. These are local observations, not certification.

## Shared whole-archive input budget (round 37)

`merge_archive_bytes` / `--merge-archive-bytes` defaults to **64 MiB for the
whole merge**. Each archive receives the smaller of its individual `archive_bytes`
cap and the remaining shared allowance, before its first read or ZIP parsing.
The count includes every byte of each approved ZIP: local headers, compressed
or stored payloads, central directory, end record and final archive comment.
Repeated inputs count each time; even an empty ZIP costs 22 bytes. If fewer
than 22 bytes remain, the next archive is refused without opening it.

ZipGate's process report now adds `preflight.archive_bytes`, measured from its
bounded captured snapshot rather than a later pathname stat. ZipMerge sums
those counts into `input.archive_bytes` and reports the configured cap as
`input.archive_byte_limit`. Existing totals and metadata fields retain their
meaning. The additional field does not change the standalone `directory_gate`
return value. Keep the updated shipped ZipGate and ZipMerge folders together.

This tightens the default for combined archives larger than 64 MiB, even if
individually allowed; raise the shared cap explicitly for reviewed larger input.
It is a logical input-size budget, **not** a cap on total bytes read, peak RAM,
disk use or CPU time. Gate inspection and digest-bound extraction reread inputs.
All original payload, path, metadata, digest, collision and staging checks still
apply. Filesystem checks assume a cooperative workspace.

Tried locally: `input_demo.py` extracted the saved public IMD API capture and
source record byte-identically, with 11,326 bytes of ZIP input and 23,441 bytes
of output. Its illustrative final ZIP comments are included in the input cap
but not the 125-byte shared central directory. A cap of 11,325 refused before
parsing the second archive and left no output. This is offline historical public
data, not a fresh API observation. No secret, wallet, coin or network is needed.

```sh
python3 -B line-2/tools/zipmerge/input_selftest.py
```

All 11 new input-budget tests passed, as did the 15 original merge tests,
10 metadata tests, 28 ZipGate tests and 44 SafeZip tests: **108 tests total**.
The three merge demos passed. New tests exercise exact and one-under boundaries,
parser refusal, exhausted allowance without opening later input, empty/repeated
archives, retained individual limits, invalid options before I/O, snapshot counts
after pathname replacement, extraction digest binding and CLI report/refusal.
These are local check results, not independent certification.
