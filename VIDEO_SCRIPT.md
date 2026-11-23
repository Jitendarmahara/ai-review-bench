# 2-minute walkthrough — recording script

Record with any screen recorder (Loom, OBS, QuickTime). Keep it ~2 min, one take
is fine — Proofline says production polish isn't needed. Read the **Say** lines
in your own voice; do the **Show** actions as you talk. Have these tabs/windows
open before you start: your terminal in `ai-review-bench`, the GitHub repo page,
one run-repo PR with a real review, and the Cloud Run verify output.

---

### 0:00–0:15 — What this is
**Show:** the repo README / file tree.
**Say:** "I built a harness that runs several AI pull-request reviewers over the
same eight changes and scores them against a key I froze before any review. The
whole point is a fair, reproducible experiment — not clever code."

### 0:15–0:40 — The experiment is fair by construction
**Show:** `ANSWER_KEY_ANALYSIS.md`, then `git log --oneline` highlighting the
"Freeze answer key before any review run" commit.
**Say:** "First I read all eight diffs and decided ground truth up front — three
are real code bugs, three are safe-or-not depending on deployment, two are fine.
I committed that key before running anything, so the freeze is provable in git
history. Grading is blind: the provider name is hidden when I score each finding."

### 0:40–1:05 — A real review, scored against the key
**Show:** a run-repo PR where a bot flagged case 03; then the terminal:
`python3 -m benchmark capture ...` and `add-finding ...`.
**Say:** "Here's case 03 — batching deliveries. The change drops the final partial
batch, and with fewer than twenty jobs it delivers nothing. This reviewer caught
it. I capture the review verbatim, split it into findings, and grade it blind —
this one is a correct_bug because it matches the frozen defect."

### 1:05–1:25 — Coverage with honest denominators
**Show:** `python3 -m benchmark coverage`.
**Say:** "The coverage table is one row per reviewer, one column per case, split
by condition. I show raw counts including what hit a quota or never ran — nothing
hidden. On the deploy-dependent cases, a reviewer that asks for deployment info is
scored correct, not evasive."

### 1:25–1:45 — The evidence trace
**Show:** the Cloud Run `verify` output (commit + request_id + receipt), or the
Actions run.
**Say:** "I also traced one commit end to end — built it, deployed it to Cloud
Run, invoked it, and got back the deployed commit with a receipt. I used Google
Cloud because I had credits; the starter's AWS path ships unchanged."

### 1:45–2:00 — One decision and the limitation
**Show:** the "Caveat" line in the report.
**Say:** "The call I'm most deliberate about: I decide what earns credit before
reading any output, so scoring can't drift. And the honest limit — eight related
changes in one app is weak evidence about performance elsewhere, so I don't
over-claim. That's the benchmark."

---

## Checklist before you hit record
- [ ] Frozen key committed and visible in `git log` (done: commit 7e639cb area).
- [ ] At least one run repo has a real review on a PR.
- [ ] `coverage` / `report` show real captured data.
- [ ] Cloud Run `verify` output saved (or the Actions run link).
- [ ] Keep it under ~2:15. If you fluff a line, keep going — it's fine.
