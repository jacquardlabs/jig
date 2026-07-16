# PLAN — demo-target quick path (rough-in-inspector demonstration, issue #15)

### Task 1 — Add `tokenize(line)` to parser.py [PASS]
Why now:    parser.py has no capability yet; tokenize is the smallest real
            groundwork task 2's own contract will consume, and this task is
            the rough-in-inspector story's required load-bearing `/build`
            demonstration (issue #15).
Read first: parser.py, tests/test_parser.py
Rests on:   none
Do:         implement `tokenize(line: str) -> list[str]` in parser.py,
            splitting on whitespace and dropping empty tokens.
Not here:   do not implement count_tokens or any other function; do not
            modify test_module_imports beyond adding one new test class for
            tokenize.

Done means:
1. [cap]  `tokenize("  a  b c ")` returns `["a", "b", "c"]` and
          `tokenize("")` returns `[]`, verified by
          `python3 -m unittest tests.test_parser.TokenizeTest -v`
          (tier: test-backed)
Evidence: paste the exact
          `python3 -m unittest tests.test_parser.TokenizeTest -v` output
          showing the test passing.

### Task 2 — Add `count_tokens(line)` to parser.py [PASS]
Why now:    downstream callers need a token count without re-implementing
            splitting logic.
Read first: parser.py, tests/test_parser.py
Rests on:   Task 1 (`tokenize`)
Do:         implement `count_tokens(line: str) -> int` in parser.py,
            returning `len(tokenize(line))` — reuse `tokenize`, do not
            re-split the line yourself.
Not here:   do not implement `tokenize` itself (already shipped by Task 1);
            do not modify `TokenizeTest`.

Done means:
1. [cap]  `count_tokens("  a  b c ")` returns `3` and `count_tokens("")`
          returns `0`, verified by
          `python3 -m unittest tests.test_parser.CountTokensTest -v`
          (tier: test-backed)
Evidence: paste the exact
          `python3 -m unittest tests.test_parser.CountTokensTest -v` output
          showing the test passing.
