#!/usr/bin/env python3
"""Verify a RewardLedger CSV against a recomputed exact ZTO allocation."""
import argparse
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys

TOOLS = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('ledgercheck_receipt', TOOLS / 'rewardreceipt/rewardreceipt.py')
rr = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rr)
rs = rr.rs
FIELDS = ['id', 'address', 'weight_fraction', 'units', 'amount', 'rounding_unit_awarded']


def read_bytes(path):
    with rs.workspace_path(path).open('rb') as stream:
        data = stream.read(rs.MAX_BYTES + 1)
    rs.require(len(data) <= rs.MAX_BYTES, 'input exceeds 256 KiB')
    return data


def expected_rows(report_bytes, report):
    return [['report_sha256', hashlib.sha256(report_bytes).hexdigest()], FIELDS] + [
        [row['id'], row.get('address', ''), row['weight_fraction'], row['units'],
         row['amount'], str(row['rounding_unit_awarded']).lower()]
        for row in report['allocations']]


def check(request, report_bytes, metadata, csv_bytes):
    """Return a receipt after arithmetic, byte provenance and every CSV cell agree."""
    rs.require(isinstance(report_bytes, bytes) and isinstance(csv_bytes, bytes), 'byte inputs required')
    rs.require(max(len(report_bytes), len(csv_bytes)) <= rs.MAX_BYTES, 'input exceeds 256 KiB')
    report = rs.parse_json(report_bytes)
    receipt = rr.verify(request, report, metadata)
    try:
        # newline='' preserves CSV newline semantics, including embedded newlines.
        stream = io.StringIO(csv_bytes.decode('utf-8'), newline='')
        reader = csv.reader(stream, strict=True)
        expected = expected_rows(report_bytes, report)
        for index, row in enumerate(expected):
            rs.require(next(reader, None) == row, 'CSV differs at logical row ' + str(index + 1))
        rs.require(next(reader, None) is None, 'CSV has extra rows')
    except (UnicodeError, csv.Error) as exc:
        raise rs.Invalid('invalid UTF-8 CSV') from exc
    return {'schema': 'ledgercheck-v1', 'result': 'verified exact allocation and CSV cells',
            'rows': len(report['allocations']), 'budget_units': receipt['budget_units'],
            'token': receipt['token'], 'report_file_sha256': hashlib.sha256(report_bytes).hexdigest(),
            'csv_file_sha256': hashlib.sha256(csv_bytes).hexdigest(),
            'arithmetic_receipt': receipt,
            'scope': 'unsigned offline review; no entitlement, authorization, balance or payment verified'}


def demo_inputs():
    request = rs.read_json(TOOLS / 'rewardsplit/example.json')
    metadata = rs.read_json(TOOLS / 'rewardsplit/zto-mainnet.json')
    report = rs.allocate(request, metadata)
    raw = (json.dumps(report, indent=2) + '\n').encode('utf-8')
    stream = io.StringIO(newline='')
    csv.writer(stream, lineterminator='\n').writerows(expected_rows(raw, report))
    return request, raw, metadata, stream.getvalue().encode('utf-8')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo')
    verify = sub.add_parser('check')
    for name in ('request', 'report', 'csv'):
        verify.add_argument('--' + name, required=True)
    verify.add_argument('--metadata', default=str(TOOLS / 'rewardsplit/zto-mainnet.json'))
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            inputs = demo_inputs()
        else:
            inputs = (rs.read_json(args.request), read_bytes(args.report),
                      rs.read_json(args.metadata), read_bytes(args.csv))
        result = check(*inputs)
        if args.command == 'demo':
            bad = inputs[3].replace(b'333333333333333334', b'333333333333333335', 1)
            try:
                check(*inputs[:3], bad)
            except rs.Invalid:
                result['demo_changed_unit_refused'] = True
            else:
                raise rs.Invalid('demo tamper was not detected')
        rs.write_json(result)
    except (OSError, ValueError, OverflowError, RecursionError) as exc:
        print('ledgercheck: ' + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
