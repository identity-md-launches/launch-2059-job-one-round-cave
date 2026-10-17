#!/usr/bin/env python3
"""Build a deterministic offline plan with renewable resource reservations."""
import argparse
from decimal import Decimal
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lockcheck'))
import lockcheck as lc
pc = lc.pc


def solve(data, limits, workers, budget=None):
    """Greedy completion-event list schedule; no optimality/infeasibility claim."""
    graph = pc.graph(data)
    if type(workers) is not int or not 1 <= workers <= 64:
        raise ValueError('workers must be an integer from 1 to 64')
    deadline = None if budget is None else pc.number(budget, 'budget')
    if deadline is not None and deadline < 0:
        raise ValueError('budget must be nonnegative')
    durations = {}
    for name, (minutes, _) in graph.items():
        if minutes.denominator != 1 or minutes > 10**9:
            raise ValueError('task minutes must be integer minutes from 1 to 1000000000')
        durations[name] = int(minutes)
    caps, demands = lc.resources(limits, set(graph))
    for name, row in demands.items():
        if any(units > caps[resource] for resource, units in row.items()):
            raise ValueError('task demand exceeds capacity: ' + name)

    pending, done, running = set(graph), set(), {}
    usage = {resource: 0 for resource in caps}
    now, rows = 0, []
    while pending or running:
        # Releases at t precede starts at t: reservations are half-open.
        for worker, (name, finish) in list(running.items()):
            if finish == now:
                done.add(name)
                del running[worker]
                for resource, units in demands[name].items():
                    usage[resource] -= units
        free = [worker for worker in range(1, workers + 1) if worker not in running]
        for name in sorted(pending):
            if not free:
                break
            if not all(dep in done for dep in graph[name][1]):
                continue
            if any(usage[r] + units > caps[r] for r, units in demands[name].items()):
                continue
            worker = free.pop(0)
            finish = now + durations[name]
            rows.append({'task': name, 'worker': worker, 'start': now, 'finish': finish})
            running[worker] = (name, finish)
            pending.remove(name)
            for resource, units in demands[name].items():
                usage[resource] += units
        if running:
            now = min(finish for _, finish in running.values())
        elif pending:
            raise RuntimeError('internal scheduling deadlock')
    plan = {'workers': workers, 'finish': now, 'schedule': rows}
    validation = lc.check(data, plan, limits, workers)
    if not validation['valid']:
        raise RuntimeError('generated plan failed independent validation')
    meets = deadline is None or now <= deadline
    return {'status': 'feasible' if meets else 'deadline_not_met_by_heuristic',
            'plan': plan, 'validation': validation, 'deadline_met': meets if deadline is not None else None,
            'optimality_proven': False, 'infeasibility_proven': False,
            'scope': 'Alphabetical ready-task priority, lowest free worker; skips resource-blocked tasks. '
                     'Integer task estimates; full-task renewable reservations; no task execution. '
                     'A missed budget does not rule out a better schedule.'}


def example():
    tasks = {'tasks': [{'id': 'render', 'minutes': 3},
                       {'id': 'preview', 'minutes': 2},
                       {'id': 'notes', 'minutes': 1},
                       {'id': 'deliver', 'minutes': 1, 'after': ['render', 'preview', 'notes']}]}
    limits = {'capacities': {'gpu': 1}, 'demands': {
        'render': {'gpu': 1}, 'preview': {'gpu': 1}, 'notes': {}, 'deliver': {}}}
    return tasks, limits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--tasks')
    parser.add_argument('--limits')
    parser.add_argument('--workers', type=int)
    parser.add_argument('--budget', type=Decimal)
    parser.add_argument('--plan-only', action='store_true', help='emit reusable Plancheck/Lockcheck input')
    args = parser.parse_args()
    try:
        if args.demo:
            if any(x is not None for x in (args.tasks, args.limits, args.workers, args.budget)):
                raise ValueError('--demo cannot be combined with input options')
            data, limits = example()
            result = solve(data, limits, 2, 6)
        else:
            if any(x is None for x in (args.tasks, args.limits, args.workers)):
                raise ValueError('--tasks, --limits and --workers are required')
            result = solve(pc.read_json(args.tasks), pc.read_json(args.limits), args.workers, args.budget)
        print(json.dumps(result['plan'] if args.plan_only else result, indent=2, allow_nan=False))
        return 0 if result['status'] == 'feasible' else 2
    except (ValueError, OSError, OverflowError, RecursionError) as exc:
        print('lockplan: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
