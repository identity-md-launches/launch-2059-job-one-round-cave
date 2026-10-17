#!/usr/bin/env python3
"""MapCheck regressions and an independent finite map-payload oracle."""
import contextlib
import copy
import io
import itertools
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import mapcheck as tool


def doc(value=None, direction='response', version='3.1.0'):
    schema = {'type': 'object'}
    if value is not None:
        schema['additionalProperties'] = copy.deepcopy(value)
    media = {'application/json': {'schema': schema}}
    op = {'responses': {}}
    if direction == 'response':
        op['responses']['200'] = {'description': 'test', 'content': media}
    else:
        op['requestBody'] = {'content': media}
    return {'openapi': version, 'paths': {'/probe': {'post': op}}}


def root(d, direction='response'):
    op = d['paths']['/probe']['post']
    body = op['responses']['200'] if direction == 'response' else op['requestBody']
    return body['content']['application/json']['schema']


def codes(report):
    return {f['code'] for f in report['findings']}


class Tests(unittest.TestCase):
    def test_finite_map_payload_oracle(self):
        subsets = [list(c) for n in range(1, 4) for c in itertools.combinations(range(3), n)]
        policies = [False, True, {}] + [{'enum': s} for s in subsets]
        # Exhaustively enumerate maps with two possible keys and four values.
        # Missing and string-valued entries distinguish empty/closed/open maps.
        missing = object()
        payloads = [dict((k, v) for k, v in zip(('a', 'b'), values) if v is not missing)
                    for values in itertools.product([missing, 0, 1, 2, 'x'], repeat=2)]
        def accepted(policy, payload):
            if policy is False:
                return not payload
            if policy is True or not policy:
                return True
            return all(value in policy['enum'] for value in payload.values())
        cases = 0
        for direction, a, b in itertools.product(('request', 'response'), policies, policies):
            aset = {i for i, p in enumerate(payloads) if accepted(a, p)}
            bset = {i for i, p in enumerate(payloads) if accepted(b, p)}
            unsafe = bool(aset - bset) if direction == 'request' else bool(bset - aset)
            r = tool.compare(doc(a, direction), doc(b, direction))
            self.assertEqual(bool(r['counts']['breaking']), unsafe, (direction, a, b))
            cases += 1
        self.assertEqual(cases, 200)

    def test_same_reference_changed_target_both_directions(self):
        for direction in ('request', 'response'):
            a = doc({'$ref': '#/components/schemas/V'}, direction)
            a['components'] = {'schemas': {'V': {'type': 'string'}}}
            b = copy.deepcopy(a)
            b['components']['schemas']['V']['type'] = 'integer'
            r = tool.compare(a, b)
            self.assertIn('schema_type_incompatible', codes(r))
            self.assertTrue(any('/additionalProperties/type' in f['location'] for f in r['findings']))
            self.assertEqual(root(a, direction), root(b, direction))
            self.assertNotIn('schema_type_incompatible', codes(tool.previous.compare(a, b)))

    def test_omission_true_and_empty_schema_equivalence(self):
        for direction, a, b in itertools.product(('request', 'response'), (None, True, {}), (None, True, {})):
            r = tool.compare(doc(a, direction), doc(b, direction))
            self.assertEqual(r['counts']['breaking'], 0)

    def test_true_to_constraint_request_and_reverse_response(self):
        self.assertIn('schema_type_incompatible', codes(tool.compare(doc(None, 'request'), doc({'type': 'string'}, 'request'))))
        self.assertIn('schema_type_incompatible', codes(tool.compare(doc({'type': 'string'}), doc(True))))
        self.assertEqual(tool.compare(doc({'type': 'string'}, 'request'), doc(None, 'request'))['counts']['breaking'], 0)
        self.assertEqual(tool.compare(doc(True), doc({'type': 'string'}))['counts']['breaking'], 0)

    def test_boolean_reference_policy_changes(self):
        for direction in ('request', 'response'):
            a = doc({'$ref': '#/components/schemas/V'}, direction)
            a['components'] = {'schemas': {'V': direction == 'request'}}
            b = copy.deepcopy(a)
            b['components']['schemas']['V'] = direction != 'request'
            r = tool.compare(a, b)
            self.assertIn('map_value_policy_incompatible', codes(r))
            self.assertNotIn('map_value_policy_incompatible', codes(tool.compare(b, a)))

    def test_nested_properties_arrays_and_recursive_maps(self):
        a = doc({'type': 'object', 'properties': {'a/~': {'type': 'array', 'items': {'enum': [1]}}}})
        b = copy.deepcopy(a)
        root(b)['additionalProperties']['properties']['a/~']['items']['enum'].append(2)
        r = tool.compare(a, b)
        self.assertTrue(any('/additionalProperties/properties/a~1~0/items/enum' in f['location'] for f in r['findings']))
        a = doc({'$ref': '#/components/schemas/Node'})
        a['components'] = {'schemas': {'Node': {'type': 'object', 'properties': {'value': {'type': 'string'}},
            'additionalProperties': {'$ref': '#/components/schemas/Node'}}}}
        b = copy.deepcopy(a)
        b['components']['schemas']['Node']['properties']['value']['type'] = 'integer'
        r = tool.compare(a, b)
        self.assertIn('schema_type_incompatible', codes(r))
        self.assertLess(r['schema_visits'], 30)
        self.assertEqual(len(r['map_pairs']), 2)

    def test_recursive_one_sided_unconstrained_schema(self):
        a = doc(True, 'request')
        b = doc({'$ref': '#/components/schemas/Node'}, 'request')
        b['components'] = {'schemas': {'Node': {'type': 'object',
            'additionalProperties': {'$ref': '#/components/schemas/Node'}}}}
        r = tool.compare(a, b)
        self.assertIn('schema_type_incompatible', codes(r))
        self.assertLess(r['schema_visits'], 30)

    def test_map_inside_discriminator_and_discriminator_inside_map(self):
        a = doc({'oneOf': [{'$ref': '#/components/schemas/V'}],
                 'discriminator': {'propertyName': 'kind', 'mapping': {'v': 'V'}}})
        a['components'] = {'schemas': {'V': {'type': 'object', 'properties': {'kind': {'enum': ['v']}},
            'additionalProperties': {'type': 'integer', 'enum': [1]}}}}
        b = copy.deepcopy(a)
        b['components']['schemas']['V']['additionalProperties']['enum'].append(2)
        r = tool.compare(a, b)
        self.assertTrue(any('/additionalProperties/discriminator/mapping/v/target/additionalProperties/enum' in f['location'] for f in r['findings']))
        self.assertEqual(len(r['dispatch_pairs']), 1)

    def test_bounds_and_unique_constraints_inside_values(self):
        for direction in ('request', 'response'):
            a = doc({'type': 'array', 'uniqueItems': direction == 'response',
                     'minItems': 2 if direction == 'response' else 1}, direction)
            b = copy.deepcopy(a)
            root(b, direction)['additionalProperties']['uniqueItems'] = direction == 'request'
            root(b, direction)['additionalProperties']['minItems'] = 1 if direction == 'response' else 2
            r = tool.compare(a, b)
            self.assertTrue(any('unique' in f['code'] and f['severity'] == 'breaking' for f in r['findings']))
            self.assertGreaterEqual(r['counts']['breaking'], 2)

    def test_malformed_values_and_remote_references_refused(self):
        for value in (None, [], 1, 'string', {'$ref': 'https://example.invalid/schema'},
                      {'$ref': '#/components/schemas/Missing'}, {'$ref': '#/bad~2escape'},
                      {'$ref': '#/components/schemas/V', 'type': 'object'}):
            a = doc(True)
            root(a)['additionalProperties'] = value
            with self.subTest(value=value), self.assertRaises(tool.api.Invalid):
                tool.compare(a, a)
        a = doc({'$ref': '#/components/schemas/V'})
        a['components'] = {'schemas': {'V': {'$ref': '#/components/schemas/V'}}}
        with self.assertRaises(tool.api.Invalid):
            tool.compare(a, a)

    def test_alias_to_nonschema_is_refused(self):
        a = doc({'$ref': '#/components/schemas/V'})
        a['components'] = {'schemas': {'V': []}}
        with self.assertRaises(tool.api.Invalid):
            tool.compare(a, a)

    def test_budgets_refuse_instead_of_partial_pass(self):
        a = doc({'type': 'integer'})
        with patch.object(tool, 'MAX_MAP_PAIRS', 0), self.assertRaises(tool.api.Invalid):
            tool.compare(a, a)
        with patch.object(tool.api, 'MAX_STEPS', 0), self.assertRaises(tool.api.Invalid):
            tool.compare(a, a)
        b = doc({'type': 'string'})
        with patch.object(tool.api, 'MAX_FINDINGS', 0), self.assertRaises(tool.api.Invalid):
            tool.compare(a, b)

    def test_previous_reviews_retained_and_versions(self):
        for version in ('3.0.3', '3.1.0'):
            a = doc({'type': 'string'}, version=version)
            b = doc({'type': 'integer'}, version=version)
            prior = tool.previous.compare(a, b)
            r = tool.compare(a, b)
            self.assertTrue(all(f in r['findings'] for f in prior['findings']))
            self.assertIn('additional_properties_changed', codes(r))
            self.assertIn('schema_type_incompatible', codes(r))

    def test_response_fallback_headers_and_request_parameter_sites(self):
        a = doc()
        op = a['paths']['/probe']['post']
        op['responses'] = {'2XX': {'description': 'test', 'headers': {'X-Map': {
            'schema': {'type': 'object', 'additionalProperties': {'enum': [1]}}}}}}
        b = copy.deepcopy(a)
        b['paths']['/probe']['post']['responses']['200'] = copy.deepcopy(op['responses']['2XX'])
        b['paths']['/probe']['post']['responses']['200']['headers']['X-Map']['schema']['additionalProperties']['enum'].append(2)
        r = tool.compare(a, b)
        self.assertTrue(any('/headers/x-map/schema/additionalProperties/enum' in f['location'] for f in r['findings']))
        a = doc()
        a['paths']['/probe']['post']['parameters'] = [{'name': 'map', 'in': 'query',
            'schema': {'type': 'object', 'additionalProperties': {'enum': [1, 2]}}}]
        b = copy.deepcopy(a)
        b['paths']['/probe']['post']['parameters'][0]['schema']['additionalProperties']['enum'].pop()
        self.assertIn('schema_enum_incompatible', codes(tool.compare(a, b)))

    def test_unchanged_capture_determinism_and_nonmutation(self):
        capture = Path(__file__).resolve().parents[1] / 'apidelta/imd-openapi.json'
        a, _ = tool.api.load(capture)
        snapshot = copy.deepcopy(a)
        r = tool.compare(a, a)
        self.assertEqual(r['operations_compared'], 5)
        self.assertEqual(r['findings'], [])
        self.assertEqual(a, snapshot)
        self.assertEqual(r, tool.compare(a, a))

    def test_cli_demo_and_all_exit_states(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(tool.main(['demo']), 0)
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            p, q = Path(folder) / 'old.json', Path(folder) / 'new.json'
            a = doc({'type': 'string'})
            p.write_text(json.dumps(a))
            for b, expected in ((a, 0), (doc({'type': 'integer'}), 1),
                                (doc({'type': 'string', 'description': 'changed'}), 3), ({}, 2)):
                q.write_text(json.dumps(b))
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(tool.main(['compare', str(p), str(q)]), expected)


if __name__ == '__main__':
    unittest.main()
