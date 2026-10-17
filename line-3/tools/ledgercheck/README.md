# LedgerCheck

LedgerCheck verifies a saved RewardLedger CSV against the original RewardSplit request, exact report file and token metadata. It recomputes the allocation through RewardReceipt, checks the CSV's source-file SHA-256, then checks every cell, header and row in order. It catches spreadsheet rounding, altered amounts, omitted zero-share contributors, changed addresses, missing/extra rows and stale exports. Python 3.9+ and the standard library only; keep the sibling rewardsplit and rewardreceipt folders.

Run from the repository root:

```sh
python3 -B line-3/tools/ledgercheck/ledgercheck.py demo
```

Tried here: exit **0**, checking three illustrative roles sharing **1 ZTO** (1000000000000000000 atomic units) using the inherited real Ethereum ZTO metadata capture at block 26205319. The demo also changed one atomic unit and confirmed refusal. Roles and budget are illustrative, no recipient is invented, and no live chain observation is claimed. The demo renders a CSV in memory; the tests separately run the actual RewardLedger exporter and verify its output.

For your saved inputs:

```sh
python3 -B line-3/tools/ledgercheck/ledgercheck.py check --request REQUEST.json --report REPORT.json --csv LEDGER.csv
```

Create REPORT.json with RewardSplit's `allocate` command and LEDGER.csv with RewardLedger. Supply `--metadata METADATA.json` if allocation used another capture. The default is the bundled ZTO metadata. RewardLedger's old standalone example is only a partial export example: it cannot pass a full arithmetic check. Supply the complete allocation report and original request. Metadata validation also supports the inherited IMD option.

The input files must resolve inside the current working directory, with at most 256 KiB each. JSON duplicate keys and non-finite values are refused. Allocation limits are inherited: 1–1000 contributors, exact decimal weights and uint256 budget. CSV must be UTF-8 without a BOM, with precisely RewardLedger's six columns. Quoting and LF/CRLF serialization may vary if the parsed cells remain identical. Blank trailing rows, reordered rows, extra columns, whitespace changes inside cells and scientific notation are refused. CSV cells are never evaluated as formulas.

The CSV header contains a hash of the **exact report file bytes**. Even a whitespace-only report edit requires a fresh export. The nested arithmetic receipt instead uses canonical JSON hashes; its `report_sha256` is deliberately different from the top-level `report_file_sha256`. The returned CSV hash identifies the exact checked CSV bytes. Retain the original input files with the receipt.

Exit **0** prints an unsigned JSON receipt. Exit **2** prints a refusal on stderr. The CLI writes no files and performs no network access. It never reads environment variables, wallets, keys or secrets, signs, sends, pays or posts. Agreement is with the supplied request and historical metadata; hashes do not authenticate a requester, establish entitlement, prove a balance or attest payment. The arithmetic implementation is reused from RewardReceipt, not independently reimplemented.

```sh
python3 -B line-3/tools/ledgercheck/selftest.py
```

All **11 tests** passed, including every contributor cell, source-byte provenance, full arithmetic tampering with a matching CSV, missing/extra/reordered rows, malformed encoding/CSV, duplicate JSON keys, resource bounds, equivalent CSV quoting/newlines, actual exporter compatibility, changed requests and the demo refusal.
