# PLAN — demo-target quick path (build-skill demonstration 1: red→green)

### Task 1 — Add `add(a, b)` to calc.py [PASS]
Why now:    calc.py has no operations yet; addition is the smallest real
            capability to build first, and this task is the build-skill
            story's required red→green /build demonstration (issue #14).
Read first: calc.py, tests/test_calc.py
Rests on:   none
Do:         implement `add(a: int, b: int) -> int` in calc.py, returning the
            sum of a and b.
Not here:   do not implement subtract, multiply, divide, or any other
            operation; do not modify test_module_imports or its test class
            beyond adding one new test method for add.

Done means:
1. [cap]  `add(2, 3)` returns `5` and `add(-1, 1)` returns `0`, verified by
          `python3 -m unittest tests.test_calc.CalcTest.test_add -v`
          (tier: test-backed)
Evidence: paste the exact `python3 -m unittest tests.test_calc.CalcTest.test_add -v`
          output showing the test passing.
