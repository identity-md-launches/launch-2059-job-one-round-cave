"""Independent grid checks and regressions for renewable resource planning."""
import copy
import json
from pathlib import Path
import random
import subprocess
import sys
import unittest
import lockplan as lp


class Tests(unittest.TestCase):
    def grid(self, tasks, limits, result, workers):
        plan = result['plan']
        rows = {r['task']: r for r in plan['schedule']}
        self.assertEqual(set(rows), {r['id'] for r in tasks['tasks']})
        for task in tasks['tasks']:
            slot = rows[task['id']]
            self.assertEqual(slot['finish'] - slot['start'], task['minutes'])
            self.assertGreaterEqual(slot['start'], 0)
            self.assertTrue(1 <= slot['worker'] <= workers)
            for dep in task.get('after', []):
                self.assertLessEqual(rows[dep]['finish'], slot['start'])
        for time in range(plan['finish']):
            active = [r for r in rows.values() if r['start'] <= time < r['finish']]
            self.assertEqual(len(active), len({r['worker'] for r in active}))
            for resource, cap in limits['capacities'].items():
                self.assertLessEqual(sum(limits['demands'][r['task']].get(resource, 0) for r in active), cap)
        self.assertEqual(plan['finish'], max(r['finish'] for r in rows.values()))

    def test_demo(self):
        data, limits = lp.example()
        result = lp.solve(data, limits, 2, 6)
        self.assertEqual(result['plan']['finish'], 6)
        self.assertTrue(result['deadline_met'])
        self.grid(data, limits, result, 2)

    def test_skip_blocked_and_release(self):
        data = {'tasks': [{'id': n, 'minutes': 2} for n in ['a', 'b', 'c']]}
        limits = {'capacities': {'gpu': 1}, 'demands': {'a': {'gpu': 1}, 'b': {'gpu': 1}, 'c': {}}}
        result = lp.solve(data, limits, 2)
        rows = {r['task']: r for r in result['plan']['schedule']}
        self.assertEqual(rows['c']['start'], 0)
        self.assertEqual(rows['b']['start'], 2)
        self.grid(data, limits, result, 2)

    def test_multicapacity(self):
        data = {'tasks': [{'id': n, 'minutes': 1} for n in ['a', 'b', 'c']]}
        limits = {'capacities': {'gpu': 3, 'disk': 2}, 'demands': {
            'a': {'gpu': 2, 'disk': 1}, 'b': {'gpu': 1, 'disk': 1}, 'c': {'disk': 2}}}
        result = lp.solve(data, limits, 3)
        self.assertEqual(result['plan']['finish'], 2)
        self.grid(data, limits, result, 3)

    def test_miss_is_not_impossibility(self):
        # Alphabetical greedy spends the first minute on an unrelated job.
        data = {'tasks': [{'id': 'a', 'minutes': 1}, {'id': 'b', 'minutes': 1},
                          {'id': 'c', 'minutes': 3}, {'id': 'd', 'minutes': 2, 'after': ['c']}]}
        limits = {'capacities': {'r': 1}, 'demands': {t['id']: {} for t in data['tasks']}}
        result = lp.solve(data, limits, 2, 5)
        self.assertEqual(result['status'], 'deadline_not_met_by_heuristic')
        self.assertFalse(result['infeasibility_proven'])
        better = {'workers': 2, 'finish': 5, 'schedule': [
            {'task': 'c', 'worker': 1, 'start': 0, 'finish': 3},
            {'task': 'd', 'worker': 1, 'start': 3, 'finish': 5},
            {'task': 'a', 'worker': 2, 'start': 0, 'finish': 1},
            {'task': 'b', 'worker': 2, 'start': 1, 'finish': 2}]}
        self.assertTrue(lp.lc.check(data, better, limits, 2, 5)['valid'])

    def test_refusals(self):
        data, limits = lp.example()
        bad = copy.deepcopy(limits)
        bad['demands']['render']['gpu'] = 2
        with self.assertRaises(ValueError): lp.solve(data, bad, 2)
        bad = copy.deepcopy(limits)
        del bad['demands']['notes']
        with self.assertRaises(ValueError): lp.solve(data, bad, 2)
        for workers in [True, 0, 65, 1.5]:
            with self.assertRaises(ValueError): lp.solve(data, limits, workers)
        for budget in [-1, float('nan')]:
            with self.assertRaises(ValueError): lp.solve(data, limits, 2, budget)
        for minutes in [0, .5, 10**9 + 1]:
            bad = copy.deepcopy(data)
            bad['tasks'][0]['minutes'] = minutes
            with self.assertRaises(ValueError): lp.solve(bad, limits, 2)

    def test_random_grid(self):
        rng = random.Random(37)
        for _ in range(200):
            count, workers = rng.randint(1, 10), rng.randint(1, 4)
            names = [str(i) for i in range(count)]
            data = {'tasks': [{'id': name, 'minutes': rng.randint(1, 5),
                'after': [n for n in names[:i] if rng.random() < .2]} for i, name in enumerate(names)]}
            limits = {'capacities': {'a': 3, 'b': 2}, 'demands': {name: {
                r: v for r, cap in [('a', 3), ('b', 2)] if (v := rng.randint(0, cap))} for name in names}}
            original = copy.deepcopy((data, limits))
            result = lp.solve(data, limits, workers)
            self.grid(data, limits, result, workers)
            self.assertEqual((data, limits), original)

    def test_boundaries_and_determinism(self):
        data = {'tasks': [{'id': str(i), 'minutes': 10**9} for i in range(500)]}
        limits = {'capacities': {'r': 1}, 'demands': {t['id']: {'r': 1} for t in data['tasks']}}
        first = lp.solve(data, limits, 64)
        self.assertEqual(first['plan']['finish'], 500 * 10**9)
        self.assertEqual(first, lp.solve({'tasks': list(reversed(data['tasks']))}, limits, 64))

    def test_cli(self):
        proc = subprocess.run([sys.executable, '-B', str(Path(lp.__file__)), '--demo', '--plan-only'],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data, limits = lp.example()
        self.assertTrue(lp.lc.check(data, json.loads(proc.stdout), limits, 2, 6)['valid'])


if __name__ == '__main__':
    unittest.main()
