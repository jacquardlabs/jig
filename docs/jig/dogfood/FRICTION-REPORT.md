# Friction report: paper dogfood of /design + /plan (viva issue #109)

Ran jig's `/design` and `/plan` workflows by hand, for real, against viva
issue #109 (unified Q&A → section-review session) as the test feature —
including live viva sessions, not simulated ones. No plugin code was written;
this is the M0 pre-work deliverable per handoff §10.

Artifacts produced: `design-viva-unified-session.md` (signed off, 2 real
viva review rounds), `PLAN-viva-unified-session.md` (4 checkpoint blocks).

## What held up

- The checkpoint block format (cap/hold, verification tiers) mapped cleanly
  onto real implementation tasks for #109 — writing Task 1-4 was
  straightforward once the design was solid. No item needed a `judgment`
  tier; every method named in Done-means already exists in viva's repo
  (pytest, ps checks, existing test files) or is created by an earlier task.
- viva's round-continuation mechanism (`--prior-input`/`--prior-verdicts`,
  content-and-title-identity carry-forward) genuinely does what jig's
  Revision mode needs: reopen only changed sections, collapse the rest. This
  was empirically verified, not assumed (see below).
- Task-splitting for PLAN.md's `### Task N` blocks **already works today**
  without needing viva issue #110's proposed `--split-on` flag — verified by
  actually parsing the real PLAN.md produced in this exercise. The existing
  "highest heading level that repeats" heuristic naturally lands on `###`
  when `##` doesn't repeat elsewhere in the doc. This narrows #110's scope
  considerably (see below).
- viva doesn't trust caller-supplied claims: my `/complete` call passed
  `sections_revised: 3` by hand, but `revision_history.py` derived `0
  revised` from the actual verdict data and ignored my summary — consistent
  with jig's own principle 6 ("nothing signs off on itself").

## Where the format creaks

**1. `/viva-qa` doesn't register as an invokable Skill — confirmed live, not
hypothetical (viva #101).** I couldn't invoke it via the Skill tool at all;
it's simply absent from the available-skills list. Had to fall back to the
manual steps documented in `brainstorming-qa.md` (write the input JSON, shell
out to `server.py` directly). jig's `/design` spec assumes "batch interview
(viva Q&A mode)" as a clean one-line invocation — today it's a multi-step
manual workaround. **This produced the batch interview: q7's ruling
blocks jig's M2 on #101 closing** — not yet reflected on jig issue #8
(implement `/design`), which should be updated to note this dependency.

**2. QA-mode sessions leak a process — new finding, not in either issue's
original text.** `server.py`'s 2-second shutdown timer only starts inside
the `/complete` handler (confirmed by reading the code, `server.py:3120-
3134`). `brainstorming-qa.md`'s documented qa-mode steps never call
`/complete` — so a qa server runs indefinitely until someone manually kills
it. This wasn't theoretical: this dogfood's own qa session left exactly such
an orphaned process, and **5 more `--mode diff` server processes were
already running on this machine from unrelated sessions, some several days
old** — the same leak shape, pre-existing and unrelated to jig. This became
Task 1 of the plan (a prerequisite for #109, not part of its original ask)
and is worth its own viva issue independent of jig entirely.

**3. I personally destroyed round-1 carry-forward state by following
SKILL.md's own documented steps literally.** SKILL.md's "clear stale state"
block (`rm -f .viva/review-input-r*.json .viva/review-r*.json`) is written
for a genuinely fresh round-1 launch. It doesn't distinguish that case from
"re-reviewing a doc that already completed sign-off" — which needs
`--prior-input`/`--prior-verdicts` pointed at the *previous* session's files,
read *before* they'd be cleared. I ran the generic steps, deleted my own
round-1 signed-off files, and had to reconstruct them from conversation
history to redo the test correctly. A fresh-context executor (exactly what
jig's `/build` dispatches) given only the task block and SKILL.md as
Read-first pointers would make the identical mistake — this isn't a "read
more carefully" problem, it's a documentation gap. Worth a viva issue: SKILL.md
should explicitly cover the "resume review on an already-signed-off doc"
case, not just "round 2 of a still-live session."

**4. Once carry-forward was done correctly, it worked exactly as jig's
Revision mode spec wants** — `approved_ids` correctly listed only the 5
untouched sections; the 3 I'd actually edited reopened for review, and nothing
else. This is a genuine capability, not a gap — but it depends on the caller
never using the generic "clear stale state" launch path for a revision. jig's
own `/design` implementation needs to get this right on the first attempt
(finding #3), since there's no test-and-retry once the file is gone.

**5. Batch interview and fork presentation are conceptually two steps in
jig's spec (§5.1 steps 2 and 3) but mechanically the same thing in viva's qa
schema.** There's no schema distinction between "a question only the human
can answer" and "a fork with a recommendation." I collapsed both into one
7-question round, tagging each `[intent]/[contract]/[experience]/[friction]`
per spec — which worked, and the human answered decisively without a second
round. But: **viva's `choices` schema has no field for "this option is
recommended"** — step 3 explicitly wants "2-3 options... one recommendation
with its reason. Recommend — the human decides," and I didn't encode a
recommendation anywhere (would have needed to prefix it into the choice text
or the hint by convention, and I simply didn't). If jig's `/design`
implementation wants recommendations to actually reach the human, that
needs to become an explicit convention (e.g. `"(recommended) ..."` prefix),
not something left to the calling agent's discretion each time.

**6. Coarser headings above the detected split level get silently absorbed
into the preceding card — new edge case for viva #110.** My PLAN.md's
trailing `## Not-here follow-ups` section (a `##`, coarser than the `###`
split level the parser landed on) didn't get its own card — its content was
silently appended inside Task 4's review card, because content between
split-level headings is captured verbatim regardless of a coarser heading
in between. A reviewer would very plausibly miss it entirely. This means
issue #110 isn't fully resolved by the existing heuristic (finding above)
whenever a plan doc has *any* content at a coarser level than its tasks —
which jig's own "Not-here follow-ups" convention (handoff §5.2 Output)
guarantees it will.

## Open questions this forces

- **jig issue #4 (PLAN.md location, root vs `docs/jig/plans/`):** this
  exercise put artifacts under `docs/jig/dogfood/` for the dogfood itself,
  which says nothing about jig's own future PLAN.md placement — still open.
- **New, not previously tracked:** should jig's `/plan` require Not-here
  follow-ups to live in their own `#### ` (finer-than-task) heading, or a
  fixed non-heading marker, specifically so they can't be silently absorbed
  the way finding 6 describes? This is a concrete design decision `/plan`'s
  own spec needs before implementation, not a viva-side fix.

## Recommendation

DESIGNED for viva #109 itself — the design and plan both hold up and don't
need another round. But this dogfood surfaces enough real, load-bearing
findings (2, 3, 6 especially) that M0's friction review (jig issue #3)
shouldn't rubber-stamp — recommend walking through all six findings above
before M1 (repo & plugin scaffold) starts, since finding 3 in particular is
exactly the kind of trap a fresh-context `/build` executor would fall into
with no way to recover the deleted state.
