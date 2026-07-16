# PLAN — demo-target quick path (rough-in-inspector DEFECT/RESAMPLE demonstration, issue #15)

### Task 1 — Add `total_cost(prices)` to parser.py [PASS]
Why now:    a downstream reporting task will rest on `total_cost`'s summed
            total; this task is the rough-in-inspector story's companion
            `DEFECT`→`RESAMPLE` demonstration (issue #15, design doc User
            journey #4). Treated as load-bearing for this companion run —
            the mechanical load-bearing derivation itself (one `Rests on:`
            line naming a task's heading) is already fully demonstrated
            against a real two-task plan in this evidence folder's primary
            demonstration; this companion plan is deliberately one task so
            its evidence stays focused on the Inspector's verdict lanes.
Read first: parser.py, tests/test_parser.py
Rests on:   none
Do:         implement `total_cost(prices: list[float]) -> float` in
            parser.py, returning the sum of every price in the list.
Not here:   do not implement any other function; do not modify
            `test_module_imports`.

Done means:
1. [cap]  `total_cost([10.0, 20.0, 5.0])` returns `35.0`, verified by
          `python3 -m unittest tests.test_parser.TotalCostTest -v`
          (tier: test-backed)
Evidence: paste the exact
          `python3 -m unittest tests.test_parser.TotalCostTest -v` output
          showing the test passing.
