# PLAN — demo-target quick path (build-skill demonstration 2: injected failure)

### Task 1 — Add `is_even(n)` to calc.py [REPLAN]
Why now:    calc.py needs an evenness check next; this task is the
            build-skill story's required deliberately-injected-failure
            /build demonstration (issue #14) — Done means item 1 below
            names a test module that this block's own Not here forbids
            creating, a genuine "Done means that can't be met as written"
            defect, so /build's failure routine gets exercised for real,
            end to end, to a REPLAN pause.
Read first: calc.py, tests/test_calc.py
Rests on:   none
Do:         implement `is_even(n: int) -> bool` in calc.py, returning True
            iff n is even.
Not here:   do not implement is_odd or any other function; add any new test
            only to the existing tests/test_calc.py — do not create,
            rename, or move any test file or test module.

Done means:
1. [cap]  `is_even(4)` returns `True` and `is_even(3)` returns `False`,
          verified by
          `python3 -m unittest tests.test_calc_evenness.CalcEvennessTest.test_is_even -v`
          (tier: test-backed)
Evidence: paste the exact
          `python3 -m unittest tests.test_calc_evenness.CalcEvennessTest.test_is_even -v`
          output showing the test passing.
