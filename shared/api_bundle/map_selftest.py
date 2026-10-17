#!/usr/bin/env python3
"""Exercise map analysis across the ZIP boundary, including fail-closed paths."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

import api_bundle as bundle
from map_demo import documents


class MapBundleTests(unittest.TestCase):
    def setUp(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='map-tests-', dir=scratch)
        self.root = Path(self.temp.name)
        _, self.old, self.new = documents()

    def tearDown(self):
        self.temp.cleanup()

    def archive(self, name, document):
        path = self.root / name
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr(zipfile.ZipInfo('docs/openapi.json'), json.dumps(document))
            archive.writestr(zipfile.ZipInfo('inert.py'), 'raise RuntimeError("never execute")')
        return path

    def pair(self, old=None, new=None):
        a = self.archive('old.zip', self.old if old is None else old)
        b = self.archive('new.zip', self.new if new is None else new)
        return a, b, dict(member='docs/openapi.json',
            old_sha256=hashlib.sha256(a.read_bytes()).hexdigest(),
            new_sha256=hashlib.sha256(b.read_bytes()).hexdigest())

    def test_reference_target_and_byte_approvals(self):
        a, b, options = self.pair()
        prior = bundle.compare(a, b, dispatch=True, **options)
        report = bundle.compare(a, b, maps=True, **options)
        self.assertEqual(prior['status'], 'review_required')
        self.assertEqual(report['status'], 'breaking')
        self.assertEqual(report['map_pairs'][0]['direction'], 'response')
        self.assertTrue(any(f['code'] == 'schema_enum_incompatible' and
            '/additionalProperties/enum' in f['location'] for f in report['findings']))
        self.assertTrue(all(f in report['findings'] for f in prior['findings']))
        for side in report['bundle_inputs'].values():
            self.assertTrue(side['approved_sha256_checked'])
            self.assertTrue(side['all_payloads_crc_checked'])
            self.assertEqual(len(side['checked_files']), 2)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ['new.zip', 'old.zip'])

    def test_unchanged_public_capture_and_old_mode(self):
        capture = json.loads(Path(__file__).with_name('imd-openapi.json').read_bytes())
        a, b, options = self.pair(capture, capture)
        report = bundle.compare(a, b, maps=True, **options)
        self.assertEqual(report['status'], 'no_detected_breakage')
        self.assertEqual(report['operations_compared'], 5)
        self.assertEqual(report['map_pairs'], [])
        self.assertTrue(bundle.compare(a, b, dispatch=True, **options)[
            'extension'].startswith('dispatchcheck-v1'))

    def test_request_closing_and_response_opening(self):
        for direction in ('request', 'response'):
            old = copy.deepcopy(self.old)
            op = old['paths']['/requests/quote']['post']
            body = op['responses']['200']
            if direction == 'request':
                op['requestBody'] = body
                op['responses'] = {}
            body['content']['application/json']['schema']['additionalProperties'] = direction == 'request'
            new = copy.deepcopy(old)
            op = new['paths']['/requests/quote']['post']
            body = op['requestBody'] if direction == 'request' else op['responses']['200']
            body['content']['application/json']['schema']['additionalProperties'] = direction != 'request'
            a, b, options = self.pair(old, new)
            report = bundle.compare(a, b, maps=True, **options)
            self.assertIn('map_value_policy_incompatible', {f['code'] for f in report['findings']})

    def test_status_fallback_header_traversal(self):
        old = copy.deepcopy(self.old)
        op = old['paths']['/requests/quote']['post']
        schema = op['responses']['200']['content']['application/json']['schema']
        op['responses'] = {'2XX': {'description': 'example', 'headers': {
            'X-Map': {'schema': schema}}}}
        new = copy.deepcopy(old)
        responses = new['paths']['/requests/quote']['post']['responses']
        responses['200'] = copy.deepcopy(responses['2XX'])
        responses['200']['headers']['X-Map']['schema']['additionalProperties'] = {'type': 'string'}
        a, b, options = self.pair(old, new)
        report = bundle.compare(a, b, maps=True, **options)
        self.assertTrue(any('/headers/x-map/schema/additionalProperties/type' in f['location']
            and f['severity'] == 'breaking' for f in report['findings']))
        self.assertTrue(report['selector_groups'])

    def test_approval_directory_crc_before_analyzer(self):
        a, b, options = self.pair()
        with mock.patch.object(bundle.mapcheck, 'compare') as analyzer:
            with self.assertRaises(ValueError):
                bundle.compare(a, b, maps=True, **{**options, 'old_sha256': '0' * 64})
            with self.assertRaises(ValueError):
                bundle.compare(a, b, maps=True, directory_bytes=1, **options)
            with self.assertRaises(ValueError):
                bundle.compare(a, b, maps=True, nodes=1, **options)
            b.write_bytes(b.read_bytes().replace(b'never execute', b'NEVER EXECUTE'))
            with self.assertRaises(zipfile.BadZipFile):
                bundle.compare(a, b, maps=True,
                    **{**options, 'new_sha256': hashlib.sha256(b.read_bytes()).hexdigest()})
            analyzer.assert_not_called()

    def test_remote_malformed_and_exhausted_maps_refuse(self):
        for value in (None, [], {'$ref': 'https://example.invalid/map'}):
            old = copy.deepcopy(self.old)
            old['paths']['/requests/quote']['post']['responses']['200']['content'][
                'application/json']['schema']['additionalProperties'] = value
            a, b, options = self.pair(old, old)
            with self.assertRaises(ValueError):
                bundle.compare(a, b, maps=True, **options)
        a, b, options = self.pair()
        with mock.patch.object(bundle.mapcheck, 'MAX_MAP_PAIRS', 0), self.assertRaises(ValueError):
            bundle.compare(a, b, maps=True, **options)

    def test_cli_all_exits_and_map_precedence(self):
        a, _, _ = self.pair(self.old, self.old)
        review = copy.deepcopy(self.old)
        review['info'] = {'title': 'Changed description metadata', 'version': 'example'}
        # Component documentation changes retain review without a value break.
        review['components']['schemas']['MapValueExample']['description'] = 'Changed'
        for doc, expected in ((self.old, 0), (self.new, 1), ({}, 2), (review, 3)):
            b = self.archive('new.zip', doc)
            cmd = [sys.executable, '-B', bundle.__file__, str(a), str(b),
                '--member', 'docs/openapi.json', '--maps', '--dispatch', '--statuses',
                '--old-sha256', hashlib.sha256(a.read_bytes()).hexdigest(),
                '--new-sha256', hashlib.sha256(b.read_bytes()).hexdigest()]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
            if expected != 2:
                self.assertTrue(json.loads(result.stdout)['extension'].startswith('mapcheck-v1'))

    def test_updated_gate_counts_snapshot_including_comment(self):
        a, _, options = self.pair()
        with zipfile.ZipFile(a, 'a') as archive:
            archive.comment = b'An illustrative envelope comment'
        raw = a.read_bytes()
        result = bundle.zipgate.process(a, expected_sha256=hashlib.sha256(raw).hexdigest())
        self.assertEqual(result['preflight']['archive_bytes'], len(raw))
        self.assertLess(result['preflight']['directory_bytes'], len(raw))


if __name__ == '__main__':
    unittest.main(verbosity=2)
