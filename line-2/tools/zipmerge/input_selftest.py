#!/usr/bin/env python3
"""Shared archive snapshot budgets and pre-parser refusals."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from zipmerge import Rejected, process
import zipgate


class InputTests(unittest.TestCase):
    def setUp(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=scratch, prefix='merge-input-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.a = self.pack('a.zip', 'a', b'x' * 300)
        self.b = self.pack('b.zip', 'b', b'y' * 500)
        self.total = sum(s['archive'].stat().st_size for s in [self.a, self.b])

    def pack(self, filename, name=None, comment=b''):
        archive = self.root / filename
        with zipfile.ZipFile(archive, 'w') as writer:
            if name is not None:
                writer.writestr(name, b'payload')
            writer.comment = comment
        return dict(archive=archive, sha256=hashlib.sha256(archive.read_bytes()).hexdigest())

    def test_exact_boundary_extracts(self):
        output = self.root / 'out'
        result = process([self.a, self.b], output, merge_archive_bytes=self.total)
        self.assertEqual(result['input'], dict(archive_bytes=self.total,
                                              archive_byte_limit=self.total))
        self.assertEqual((output / 'a').read_bytes(), b'payload')
        self.assertEqual((output / 'b').read_bytes(), b'payload')

    def test_one_under_refuses_before_later_parser(self):
        with patch('zipgate.safe_process', wraps=zipgate.safe_process) as parser:
            with self.assertRaisesRegex(Rejected, 'archive byte limit'):
                process([self.a, self.b], self.root / 'out',
                        merge_archive_bytes=self.total - 1)
            self.assertEqual(parser.call_count, 1)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ['a.zip', 'b.zip'])

    def test_first_input_refused_before_parser(self):
        with patch('zipgate.safe_process') as parser:
            with self.assertRaisesRegex(Rejected, 'archive byte limit'):
                process([self.a], merge_archive_bytes=self.a['archive'].stat().st_size - 1)
            parser.assert_not_called()

    def test_exhausted_allowance_never_opens_next_input(self):
        # Declarations are valid; opening this absent archive would be an OSError.
        missing = dict(archive=self.root / 'absent.zip', sha256=self.b['sha256'])
        size = self.a['archive'].stat().st_size
        for leftover in (0, 1, 21):
            with self.subTest(leftover=leftover), patch(
                    'zipmerge.gate_process', wraps=zipgate.process) as gate:
                with self.assertRaisesRegex(Rejected, 'archive byte limit exhausted'):
                    process([self.a, missing], merge_archive_bytes=size + leftover)
                self.assertEqual(gate.call_count, 1)

    def test_empty_archives_still_cost_22_bytes_each(self):
        empty = self.pack('empty.zip')
        result = process([empty, empty], merge_archive_bytes=44)
        self.assertEqual(result['input']['archive_bytes'], 44)
        with self.assertRaisesRegex(Rejected, 'archive byte limit'):
            process([empty, empty], merge_archive_bytes=43)

    def test_repeated_empty_inputs_are_not_deduplicated(self):
        empty = self.pack('empty.zip', comment=b'z' * 100)
        self.assertEqual(process([empty] * 3, merge_archive_bytes=366)
                         ['input']['archive_bytes'], 366)

    def test_per_archive_cap_still_applies(self):
        with self.assertRaisesRegex(Rejected, 'archive byte limit'):
            process([self.b], archive_bytes=self.b['archive'].stat().st_size - 1,
                    merge_archive_bytes=self.total)

    def test_invalid_options_before_input_io(self):
        for value in (0, -1, True, 1.5, '44', None):
            with self.subTest(value=value), patch('zipmerge.gate_process') as gate:
                with self.assertRaisesRegex(Rejected, 'positive integer'):
                    process([self.a], merge_archive_bytes=value)
                gate.assert_not_called()

    def test_report_counts_snapshot_not_later_stat(self):
        original = zipgate.safe_process
        def replace_after_snapshot(*args, **kwargs):
            result = original(*args, **kwargs)
            # A later pathname size must not replace the inspected byte count.
            self.a['archive'].write_bytes(b'replaced')
            return result
        expected = self.a['archive'].stat().st_size
        with patch('zipgate.safe_process', side_effect=replace_after_snapshot):
            self.assertEqual(process([self.a])['input']['archive_bytes'], expected)

    def test_replaced_input_cannot_publish(self):
        original = zipgate.process
        calls = 0
        def replace_before_extract(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 3:
                self.pack('a.zip', 'a', b'new comment' * 100)
            return original(*args, **kwargs)
        with patch('zipmerge.gate_process', side_effect=replace_before_extract):
            with self.assertRaisesRegex(Rejected, 'SHA-256'):
                process([self.a, self.b], self.root / 'out',
                        merge_archive_bytes=self.total)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ['a.zip', 'b.zip'])

    def test_cli_report_and_refusal(self):
        command = [sys.executable, '-B', str(Path(__file__).with_name('zipmerge.py')),
                   'plan', '--archive', str(self.a['archive']), '--sha256', self.a['sha256'],
                   '--archive', str(self.b['archive']), '--sha256', self.b['sha256'],
                   '--merge-archive-bytes']
        good = subprocess.run(command + [str(self.total)], capture_output=True, text=True)
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertEqual(json.loads(good.stdout)['input']['archive_bytes'], self.total)
        bad = subprocess.run(command + [str(self.total - 1)], capture_output=True, text=True)
        self.assertEqual(bad.returncode, 2, bad.stderr)
        self.assertFalse(json.loads(bad.stdout)['ok'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
