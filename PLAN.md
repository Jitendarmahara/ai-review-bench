# Day-by-day plan (target: 3–4 focused days, $0 spend)

The grade is for a fair, reproducible experiment with traceable evidence — not
clever code. Spend your time on isolation, a fixed rubric, and honest
denominators. Depth over breadth: 2 providers done rigorously beats 5 done
sloppily.

## Day 0 — setup (2–3 h)
- [ ] `Use this template` → private copy of `prooflinedev/ai-review-benchmarks`.
- [ ] Drop in `benchmark/`, EXPERIMENT_PROTOCOL.md, SETUP.md, REPORT_TEMPLATE.md, PLAN.md.
- [ ] `gh auth login`; `python3 -m benchmark init && seed-providers`.
- [ ] Read all 8 cases (apply each patch on a branch; read body.md; read evidence.md for 04–06).
- [ ] Run the sample app once (`docs/report-service.md`) so you understand what it does.

## Day 1 — freeze ground truth + prove the pipeline (4–6 h)
- [ ] For each of the 11 (case × condition) cells, decide the correct verdict and
      `freeze-key` it. This is the most important intellectual work — do it before
      reading any reviewer output. Commit the frozen DB state / a dump.
- [ ] Create `bench-run-proofline` and `bench-run-coderabbit`; push `pilot/*` branches.
- [ ] Install both apps on their repos; verify bot logins with one throwaway PR each.
- [ ] Run cases 01–03 on both providers end to end: open-pr → capture → add-finding.
      Goal today: the loop works and records clean attempts.

## Day 2 — breadth + the AWS evidence trace (5–7 h)
- [ ] Run the remaining cases (04–08) on both providers, both conditions where a
      snapshot exists. Mark quota_stop/error honestly when they happen.
- [ ] Add a 3rd provider (Greptile or Cursor BugBot) on the same batch.
- [ ] Cloud trace: deploy ONE case's revision via GitHub Actions, verify the
      delivered report, save the workflow link + receipt, tear it down.
      Use GCP Cloud Run (`gcp/GCP_SETUP.md`) with your GCP credits, or AWS.
      Smoke it locally first: `python3 gcp/deploy.py smoke --docker`.
- [ ] Run the held-out original change through the pipeline (familiarity probe).

## Day 3 — grade blind + write the report (4–6 h)
- [ ] `grade-export` → grade every finding blind against the key → `grade-import`.
      Second-reader the ambiguous ones.
- [ ] `report --out RESULTS.md`; fill the Spotlight result (one result, commit →
      original comment → verified behavior → score) and one limitation.
- [ ] Tidy rerun instructions so another engineer can reproduce from scratch.
- [ ] Record the ≤2-min narrated walkthrough: show a real review, the coverage
      table, and one scoring decision. Rough is fine; be clear about *why* you
      made each call.

## Day 4 (buffer) — submit
- [ ] Open the submission PR in your private repo; grant hiring-team read access.
- [ ] Email intern-applicants@proofline.sh (see SETUP.md step 9).

## What makes this stand out (do these, skip the rest)
1. Key frozen and committed BEFORE any output — visible in git history.
2. Blind grading with a second reader on disputed calls.
3. Per-provider isolated repos; shared learning turned off and noted.
4. A real AWS deploy→verify→receipt trace for one case.
5. Coverage table with raw denominators, including what you could NOT run.
6. One honest limitation that could flip your conclusion.

## Non-goals (don't sink time here)
- A slick web UI. Markdown tables are enough.
- Running 10 providers. 3 done cleanly is plenty.
- Perfect parsing of review text into findings — hand-splitting is fine and more honest.
