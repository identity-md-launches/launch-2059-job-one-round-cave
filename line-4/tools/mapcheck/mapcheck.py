#!/usr/bin/env python3
"""Bounded offline OpenAPI comparison inside additionalProperties value schemas."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys

spec = importlib.util.spec_from_file_location('mapcheck_previous',
    Path(__file__).resolve().parents[1] / 'dispatchcheck/dispatchcheck.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
api = previous.api
MAX_MAP_PAIRS = 1024


class Analyzer(previous.Analyzer):
    def __init__(self, old, new):
        super().__init__(old, new)
        self.map_pairs = []
        # Reuse a stable identity for unconstrained values in recursive graphs.
        self.any_value = {}

    def _schema(self, old, new, loc, direction):
        super()._schema(old, new, loc, direction)
        if 'additionalProperties' not in old and 'additionalProperties' not in new:
            return
        a = self.old.resolve(old.get('additionalProperties', True))
        b = self.new.resolve(new.get('additionalProperties', True))
        api.require(isinstance(a, (dict, bool)) and isinstance(b, (dict, bool)),
                    'additionalProperties must be a schema object or boolean')
        if a is True and b is True or a is False and b is False:
            return
        api.require(len(self.map_pairs) < MAX_MAP_PAIRS,
                    'map pair limit exceeded; compare a smaller description')
        base = loc + '/additionalProperties'
        self.map_pairs.append(dict(location=base, direction=direction,
                                   old_policy='closed' if a is False else 'open',
                                   new_policy='closed' if b is False else 'open'))
        if a is False or b is False:
            unsafe = (b is False and a is not False) if direction == 'request' else (
                      a is False and b is not False)
            if unsafe:
                self.emit('breaking', 'map_value_policy_incompatible', base,
                          'Potential break for additional keys: request closes previously '
                          'allowed keys.' if direction == 'request' else
                          'Potential break for additional keys: response opens formerly forbidden keys.')
            return
        # true and omission both accept any value. Resolve each side independently
        # before comparison so an unchanged $ref cannot hide a changed target.
        self.schema(self.any_value if a is True else a,
                    self.any_value if b is True else b, base, direction)


def compare(old, new):
    analyzer = Analyzer(old, new)
    report = analyzer.run()
    report.update(extension='mapcheck-v1 (includes dispatchcheck and earlier analyzers)',
                  map_pairs=analyzer.map_pairs, dispatch_pairs=analyzer.dispatch_pairs,
                  schema_visits=analyzer.steps, selector_groups=analyzer.selector_groups,
                  status_visits=analyzer.status_visits,
                  remapped_header_pairs=analyzer.remapped_header_pairs,
                  map_scope='Additional-property value constraints at inherited traversal sites. '
                            'Findings are potential region-level breaks, not whole-schema '
                            'implication. Named-key migrations, patternProperties, composition '
                            'and reachability are not modeled; earlier reviews are retained.')
    return report


def demo():
    capture = Path(__file__).resolve().parents[1] / 'apidelta/imd-openapi.json'
    old, digest = api.load(capture)
    old = copy.deepcopy(old)
    path = sorted(old['paths'])[0]
    method = sorted(old['paths'][path].keys() & api.METHODS)[0]
    schemas = old.setdefault('components', {}).setdefault('schemas', {})
    api.require('MapValueExample37' not in schemas, 'demo component collision')
    schemas['MapValueExample37'] = {'type': 'integer', 'enum': [1, 2]}
    old['paths'][path][method]['responses'] = {'200': {'description': 'Hypothetical map',
        'content': {'application/json': {'schema': {'type': 'object',
            'additionalProperties': {'$ref': '#/components/schemas/MapValueExample37'}}}}}}
    new = copy.deepcopy(old)
    new['components']['schemas']['MapValueExample37']['enum'].append(3)
    report = compare(old, new)
    api.require(any(f['code'] == 'schema_enum_incompatible' and
                    '/additionalProperties/' in f['location'] for f in report['findings']),
                'demo failed to inspect unchanged map reference target')
    report.update(capture_sha256=digest, baseline_source='https://api.imd.fun/openapi.json',
                  demo='Saved real IMD operation with a hypothetical response map. The value '
                       'reference stays unchanged while its allowed integers expand. '
                       'No described endpoint is called.')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('demo')
    diff = commands.add_parser('compare')
    diff.add_argument('old')
    diff.add_argument('new')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            report = demo()
        else:
            old, oh = api.load(args.old)
            new, nh = api.load(args.new)
            report = compare(old, new)
            report.update(old_sha256=oh, new_sha256=nh)
        print(json.dumps(report, indent=2, allow_nan=False))
        return 0 if args.command == 'demo' else {
            'breaking': 1, 'review_required': 3, 'no_detected_breakage': 0}[report['status']]
    except (api.Invalid, OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
        print('mapcheck: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
