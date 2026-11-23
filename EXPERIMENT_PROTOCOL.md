# Experiment protocol (frozen before any run)

This is the contract an engineer reading the results can hold me to. It answers
the two questions from Proofline's experiment guide: *did the tools review the
same change with the same information?* and *could I add a reviewer tomorrow and
get a comparable result?* Freeze this file (commit it) before the first review.

## 1. Unit of observation

One **attempt** = (provider, case, condition, base_sha, head_sha, run_id).
For every attempt I record: trigger, model/plan if visible, settings, timestamps,
terminal outcome, and the verbatim first review. A second delivery of the same
webhook is folded into the primary attempt (`is_retry=0`); an intentional second
review is a separate row with `is_retry=1`. Retries are never silently merged.

## 2. Two conditions

- `code_only` — the reviewer sees only the code (app-only branches `pilot/base`
  and `pilot/NN`). Applies to all 8 cases.
- `with_snapshot` — the reviewer is additionally given the deployment snapshot
  (`cases/04..06/evidence.md`). Only cases 04, 05, 06 have snapshots. Every
  provider in this condition gets the **same** snapshot.

## 3. Isolation (keep answers out of the review)

- Each provider gets its **own private run repo** so it never sees another
  provider's comments.
- The answer key lives only in the benchmark DB (`answer_key` table), frozen via
  `freeze-key`. It is **never** pushed to a run repo a reviewer can read.
- Shared learning / cross-repo indexing is turned **off** where a provider offers
  it; any uncertainty is recorded in that provider's notes.
- Calibration notes, CI failures, and earlier PR comments stay out of run repos.

## 4. Deployment information

For a `code_only` review of 04–06, a reviewer that says "I need to know how this
is deployed to decide" is **correct** (`needs_deploy_info`), not evasive. For the
`with_snapshot` review, I check whether it uses the snapshot to name the affected
deployment and cite the evidence. I label every fact in the report as coming from
the live AWS deploy or from a supplied case snapshot (the two-site records in
04–06 are synthetic).

## 5. Scoring (decided before reading output)

Buckets (finding-level): `correct_bug`, `false_warning`, `needs_deploy_info`,
`valid_unanticipated`, `noise`. Run-level outcomes: `completed`, `quota_stop`,
`error`, `unattempted`. A quiet review on a **safe** change is a good outcome. A
reviewer that never finished is a distinct observation, not a zero.

Grading is **blind**: findings are exported with the provider hidden, graded
against the frozen key, then imported. Ambiguous or surprising calls get a second
reader (`--second-reader`) and the disputed one is written up in the report.

## 6. Breadth and denominators

One row per distinct reviewer, one column per case, per condition. I report raw
counts (completed / quota_stop / error / unattempted) next to any rate, and name
the cases a given pair of providers actually **shared**. Providers are started on
the same batch so partial runs still overlap.

## 7. Familiarity probe

After freezing the rules, I run one **held-out, original** change (not one of the
eight public cases) through the same pipeline to check whether a provider is
leaning on memorized public cases rather than reviewing the diff.

## 8. Honesty caveat (stated in the report)

Eight related changes in one application give limited evidence about performance
elsewhere, even across many providers. The report says so and does not over-claim.
