# AI Review Benchmark harness

A small, dependency-free harness for the Proofline "AI Review Benchmarks"
application project: run several AI PR reviewers over the same changes, record
every attempt, grade findings blind against a frozen key, and report honest
coverage with a traceable evidence chain.

Built to drop into a private copy of `prooflinedev/ai-review-benchmarks` (the
starter already ships the sample app, the 8 cases, and the AWS deploy).

## Quick look

```sh
python3 -m benchmark init
python3 -m benchmark seed-providers
python3 -m benchmark freeze-key 03 code_only defect --expected "drops final partial batch"
python3 -m benchmark open-pr coderabbit 03 code_only --repo ORG/bench-run-coderabbit --pr 1
python3 -m benchmark capture coderabbit-03-code_only-1          # or --from-file review.txt
python3 -m benchmark add-finding coderabbit-03-code_only-1 "..." --locator reports.py
python3 -m benchmark grade-export to_grade.json                 # provider hidden
python3 -m benchmark grade-import to_grade.json
python3 -m benchmark report --out RESULTS.md
```

## Design in one paragraph

The SQLite DB is the single source of truth (`benchmark/schema.sql`). A **run** is
one attempt `(provider, case, condition, base/head, run_id)`. Providers are thin
adapters (`benchmark/providers/`): `github_bot` reads the earliest review a bot
posted on the PR; `manual` lets you paste a web-only reviewer's output; an `api`
stub is there for Greptile if you want it. Findings are graded **blind** —
exported with the provider hidden, scored against a key frozen *before* any run,
then imported. Coverage and the report are generated from the DB with raw
denominators, including what could not be run.

## Files

- `benchmark/` — the harness package (`python -m benchmark`).
- `gcp/` — Cloud Run deploy path (build→deploy→verify→receipt), the GCP twin of
  the starter's `aws/` trace. See `gcp/GCP_SETUP.md`.
- `tests/` — unittest suite (`python3 -m unittest discover -s tests -v`).
- `EXPERIMENT_PROTOCOL.md` — the frozen rules (isolation, conditions, scoring).
- `SETUP.md` — accounts, run repos, the per-case loop, cloud trace, submission.
- `PLAN.md` — day-by-day (3–4 days, $0).
- `REPORT_TEMPLATE.md` — the narrative wrapper around generated results.

No third-party Python dependencies. Needs Python 3.10+ and the `gh` CLI (plus
Docker + `gcloud` for the GCP trace).

## Tests

```sh
python3 -m unittest discover -s tests -v   # harness
python3 gcp/deploy.py smoke --docker        # cloud-run container
```
