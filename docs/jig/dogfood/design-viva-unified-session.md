# Design: unified Q&A → section-review session (viva #109)

## Intent

jig's `/design` skill needs step 2 (batch interview) and step 5 (section
review) to run in one continuous browser session instead of two separate
server invocations/tabs — that's viva issue #109, filed as a jig dependency.

Per the batch interview (q1): #109 ranks ahead of viva issue #101 (viva-qa
doesn't register as an invokable Skill) in viva's own build queue. But
separately (q7): jig's own M2 (implement `/design`) is gated on #101 closing,
regardless of #109's status. So the two pieces of viva work that matter to
jig ship in an order where #109 lands *before* the thing (#101) that actually
unblocks jig building against it — a real sequencing risk, not just a
priority call. See Risks.

## Experience

- Same browser tab for the whole session — no new tab, no manual re-invoke
  by the human.
- No visible "mode" indicator during the QA→review transition (q6) — the
  human just sees QA cards, then review cards, with no chrome announcing the
  switch. This departs from viva's own precedent (`DESIGN.md`'s
  `body.mode-diff` stamp for diff mode) — a deliberate exception, not an
  oversight.
- A brief loading/spinner state is acceptable during the gap while Claude
  reads the QA answers and drafts the design doc (q3) — same visual pattern
  review already uses between rounds N and N+1.

## Contracts

- Output stays two files, not a consolidated session file (q5): `answers.json`
  from the QA phase, then `review-input-r1.json` / `review-r1.json` for the
  review phase, unchanged from today's per-mode contracts.
- Session continuity is a **two-process, same-tab client redirect** (q2), not
  a single process serving both phases via a `/next-round`-style endpoint.
  Concretely:
  - The QA server (unchanged) writes `answers.json` on submit.
  - Claude reads it, drafts the design doc, then launches a *second*,
    ordinary review-mode server process (today's existing
    `parse_sections.py` + `server.py --mode review` — unchanged).
  - **New surface needed:** a way for the still-open QA tab to learn the
    review server's URL and navigate to it — a new `POST /handoff {url}`
    endpoint on the QA server that the calling agent hits once the review
    server is up, which the QA tab's JS polls for and then does
    `window.location = url`.
  - **Correction from /plan inventory (server.py:3120-3134):** the 2-second
    shutdown timer only starts inside the `/complete` handler — it never
    fires on its own. `brainstorming-qa.md`'s documented steps never call
    `POST /complete` for QA sessions, so a QA server today already runs
    indefinitely until manually killed. The design risk isn't "suppress an
    auto-shutdown" (there isn't one); it's the inverse — **the handoff step
    must explicitly call `/complete` (or a new equivalent) on the QA server
    after the redirect fires, or every `/design` invocation leaks a QA
    process.** This is not a hypothetical: this dogfood's own QA session
    left exactly such an orphaned process, and 5 more `--mode diff` server
    processes were already running on this machine from unrelated prior
    sessions, going back several days — the same shape of leak, pre-existing
    and unrelated to jig.
  - `.brainstorm-patch-version` retirement is explicitly **not** part of this
    contract (q4) — tracked as a separate follow-up.

## Approach

1. Launch QA server as today (unchanged) — jig's `/design` step 2.
2. Human answers; QA server writes `answers.json` (unchanged).
3. Claude reads `answers.json`, drafts the sectioned design doc — an agent
   step with no server involvement; the human sees a spinner (q3).
4. Claude launches a review-mode server (unchanged CLI) against the drafted
   doc.
5. Claude signals the still-open QA tab to redirect to the review server's
   URL (new surface — see Contracts).
6. Review proceeds exactly as today's `/design` step 5, unmodified.

Where the format creaks: viva's post-submission shutdown timer currently
encodes "done, nothing more is coming" unconditionally. #109 needs a second
lifecycle state — "done, but a handoff may follow shortly" — that doesn't
exist in the server today.

## Assumptions

- Claude's doc-drafting step takes long enough that a spinner beats an
  instant transition — **confirmed** by q3's ruling, not merely assumed.
- `.brainstorm-patch-version` retirement is unrelated engineering —
  **confirmed** out of scope by q4.
- **Falsified by /plan inventory, not merely confirmed:** the assumption was
  that keeping the QA server alive past an auto-shutdown might collide with
  SKILL.md's "previous session may still be running" guard. Reading
  `server.py` shows there is no auto-shutdown for QA mode at all — the timer
  only starts from an explicit `/complete` POST, which QA sessions never
  send. The real requirement is the opposite of what this doc originally
  assumed: the handoff step must *add* an explicit shutdown call, not manage
  an existing one. See Contracts and Risks.

## Not doing

- A fully server-autonomous handoff (server drafts review content itself) —
  ruled out structurally: Claude must always sit between the two phases (see
  Contracts), so "no agent in the loop" was never on the table.
- A consolidated single-file contract merging QA + review output — q5 ruled
  against this.
- Retiring `.brainstorm-patch-version` in this same change — q4 ruled it a
  separate follow-up issue.
- A visible mode-change indicator in the UI — q6 ruled against it.

## Risks

- **REPLAN-RISK, revised:** the risk is no longer "does keeping the server
  alive collide with a shutdown guard" (falsified — see Assumptions). It's a
  correctness requirement instead: the handoff step MUST call `/complete` (or
  a new equivalent) on the QA server post-redirect, as a first-class part of
  this design, not an implementation afterthought — otherwise #109 adds a
  new, guaranteed process leak on every `/design` invocation, compounding the
  same leak pattern already observed on this machine from unrelated prior
  sessions (5 lingering `--mode diff` processes, days old).
- **Program risk (cross-repo, not internal to #109):** per q1 + q7, jig's M2
  is gated on viva #101 closing, and #101 is *not* next in viva's own queue
  (#109 is). jig's `/design` implementation may sit blocked longer than
  #109's own timeline would suggest. Not an ESCALATE-RISK against this
  design — a roadmap risk for jig's M0/M1 sequencing, worth a note back on
  jig's tracking issues.

---

## Revision History

Signed off via viva review — 1 round, 8 sections, 0 revised. 2026-07-11

Signed off via viva review — 2 rounds, 8 sections, 0 revised. 2026-07-11
