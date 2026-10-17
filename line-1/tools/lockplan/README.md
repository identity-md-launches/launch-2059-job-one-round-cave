# Lockplan — plan around shared tools

Build a complete offline task schedule that respects dependencies, worker slots,
and shared renewable resource capacities. For example, two workers sharing one
GPU can overlap notes with preview work while keeping GPU jobs separate.
Nothing is executed, reserved, sent, or fetched.

From the repository root, with Python 3.9 or newer:

```sh
python3 -B line-1/tools/lockplan/lockplan.py --demo
```

Observed: notes runs at 0–1, preview at 0–2, render at 2–5, and deliver at
5–6 on two workers. GPU peak is one. The six-minute deadline is met. The plan
passes the existing independent Plancheck and Lockcheck validators before output.
Eight tests pass, including 200 seeded DAGs checked by a separate minute-grid
worker/dependency/resource oracle, a 500-task boundary, and a missed-budget
example where another schedule does fit.

```sh
python3 -B line-1/tools/lockplan/selftest.py
```

## Your own input

```sh
python3 -B line-1/tools/lockplan/lockplan.py --tasks TASKS.json --limits LIMITS.json --workers 2 --budget 12
```

TASKS.json has exactly `{"tasks": [...]}`. Each task has a distinct nonempty
`id`, positive integer `minutes` (1 through 1,000,000,000), and optional `after`
listing distinct prerequisite ids. There must be 1–500 tasks; unknown dependencies
and cycles are refused. Labels are data. No command strings are interpreted.

LIMITS.json uses the same schema as Lockcheck:

```json
{"capacities":{"gpu":1},"demands":{"render":{"gpu":1},"preview":{"gpu":1},"notes":{},"deliver":{}}}
```

Declare every task exactly once under `demands`, using `{}` for no reservation.
There must be 1–64 named resources. Capacity and demand units are integers from
1 through 1,000,000,000; omit unused resources from a task. A demand exceeding
capacity is refused before scheduling. Workers must be an integer from 1–64.
Optional budget is a finite nonnegative numeric minute value, compared exactly.
Unlike Lockcheck, task durations here must be whole minutes.

Both files must be ordinary files resolving inside the current workspace,
at most 100 KB each. Duplicate JSON keys, extra fields, and nonfinite values
are refused by the reused parsers. Keep the sibling `lockcheck/` and `plancheck/`
folders: these are the only runtime source dependencies, all standard-library Python.

Use `--plan-only` to emit just the numeric schedule accepted by Plancheck and
Lockcheck. Save stdout to a workspace file of your choice, then pass that file
as their `--plan` input with the same tasks, limits, workers and deadline.
Default output includes the plan, resource validation and deadline result.
Exit 0 means this plan meets the requested budget (or no budget was requested);
2 means this heuristic missed it, including in plan-only mode; 1 means bad input.

## Scheduling policy and limits

At time zero and each completion event, release all finishing reservations, then
scan ready tasks in alphabetical id order. Start each fitting task on the lowest
free worker; skip a resource-blocked task so another ready task may start.
Tasks are nonpreemptive and reserve their declared resources throughout
`[start, finish)`. Completions release resources before starts at the same time.

This is a deterministic greedy schedule, with no shortest-plan or infeasibility
proof. A missed deadline says only that this particular plan misses it. Try a
better priority policy or an exact resource-aware solver if needed. The current
exact Gateplan/Optplan solvers do not enforce resource declarations. Capacities,
work estimates and continuous worker availability are caller assumptions; this
does not discover hardware, predict runtime, handle calendars, resume running
tasks, enforce handoff gates, or reserve real tools. No coin or chain call is
needed for this offline capability.
