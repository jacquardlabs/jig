# PLAN — demo-target quick path (rough-in-inspector CONCERN demonstration, issue #15)

### Task 1 — Add `safe_divide(a, b)` to parser.py [PASS]
Why now:    a downstream reporting task will rest on `safe_divide`'s
            quotient; this task is the rough-in-inspector story's companion
            `CONCERN` demonstration (issue #15, design doc User journey #5).
            Treated as load-bearing for this companion run — the mechanical
            load-bearing derivation itself is already fully demonstrated
            against a real two-task plan in this evidence folder's primary
            demonstration; this companion plan is deliberately one task so
            its evidence stays focused on the Inspector's verdict lanes.
Read first: parser.py, tests/test_parser.py
Rests on:   none
Do:         implement `safe_divide(a: float, b: float) -> float` in
            parser.py, returning `a` divided by `b`.
Not here:   do not implement any other function; do not modify
            `test_module_imports`.

Done means:
1. [cap]  `safe_divide(10.0, 2.0)` returns `5.0`, verified by
          `python3 -m unittest tests.test_parser.SafeDivideTest -v`
          (tier: test-backed)
Evidence: paste the exact
          `python3 -m unittest tests.test_parser.SafeDivideTest -v` output
          showing the test passing.
