#!/usr/bin/env python3
"""Offline behavioral tests, including compatibility with the actual CSV exporter."""
import contextlib
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import ledgercheck as lc


class Checks(unittest.TestCase):
    def setUp(self):
        self.req, self.raw, self.meta, self.csv = lc.demo_inputs()

    def check(self, raw=None, data=None):
        return lc.check(self.req, self.raw if raw is None else raw, self.meta,
                        self.csv if data is None else data)

    def rewrite(self, mutate):
        rows = list(csv.reader(io.StringIO(self.csv.decode())))
        mutate(rows)
        out = io.StringIO(newline='')
        csv.writer(out).writerows(rows)
        return out.getvalue().encode()

    def test_valid_exact_units(self):
        result = self.check()
        self.assertEqual(result['rows'], 3)
        self.assertEqual(result['budget_units'], '1000000000000000000')
        self.assertEqual(result['csv_file_sha256'], hashlib.sha256(self.csv).hexdigest())

    def test_every_cell_checked(self):
        for row in range(2, 5):
            for col in range(6):
                with self.subTest(row=row, col=col), self.assertRaises(ValueError):
                    self.check(data=self.rewrite(lambda rows: rows[row].__setitem__(col, 'changed')))

    def test_structure_and_provenance(self):
        mutations = [lambda r: r.pop(), lambda r: r.append(r[-1]),
                     lambda r: r.reverse(), lambda r: r[1].reverse(),
                     lambda r: r[0].__setitem__(1, '0'*64),
                     lambda r: r[2].append(''), lambda r: r.append([])]
        for mutate in mutations:
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                self.check(data=self.rewrite(mutate))

    def test_report_arithmetic_before_csv(self):
        obj = json.loads(self.raw)
        obj['allocations'][0]['units'] = '1'
        raw = json.dumps(obj).encode()
        out = io.StringIO()
        csv.writer(out).writerows(lc.expected_rows(raw, obj))
        with self.assertRaises(ValueError):
            self.check(raw=raw, data=out.getvalue().encode())

    def test_byte_provenance_not_canonical_digest(self):
        with self.assertRaises(ValueError):
            self.check(raw=self.raw + b' ')

    def test_duplicate_json_keys(self):
        with self.assertRaises(ValueError):
            self.check(raw=b'{"allocations":[],"allocations":[]}')

    def test_csv_encoding_limits_and_syntax(self):
        for bad in (b'\xff', b'"unterminated', b'a'*(lc.rs.MAX_BYTES+1), b'\xef\xbb\xbf'+self.csv):
            with self.subTest(size=len(bad)), self.assertRaises(ValueError):
                self.check(data=bad)

    def test_equivalent_csv_serializations(self):
        self.check(data=self.csv.replace(b'\n', b'\r\n'))
        rows = list(csv.reader(io.StringIO(self.csv.decode())))
        out = io.StringIO(newline='')
        csv.writer(out, quoting=csv.QUOTE_ALL).writerows(rows)
        self.check(data=out.getvalue().encode())

    def test_actual_exporter(self):
        spec = importlib.util.spec_from_file_location('ledger', lc.TOOLS / 'rewardledger/rewardledger.py')
        ledger = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ledger)
        # A virtual source avoids temporary files; run the actual export function.
        with patch.object(Path, 'read_text', return_value=self.raw.decode()), \
             patch.object(Path, 'read_bytes', return_value=self.raw), \
             contextlib.redirect_stdout(io.StringIO()) as out, \
             contextlib.redirect_stderr(io.StringIO()):
            ledger.main(['virtual-report.json'])
        self.check(data=out.getvalue().encode())

    def test_request_changed(self):
        self.req['budget'] = '2'
        with self.assertRaises(ValueError):
            self.check()

    def test_cli_demo(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(lc.main(['demo']), 0)
        self.assertTrue(json.loads(out.getvalue())['demo_changed_unit_refused'])


if __name__ == '__main__':
    unittest.main()
