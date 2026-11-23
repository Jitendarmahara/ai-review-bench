# AI Review Benchmark — results

## Coverage

### Denominators

- Distinct reviewers: 2
- Distinct cases touched: 8
- Completed provider-case pairs (non-retry): 16
- Repeats (variability runs): 0


### Condition: code_only

| Provider | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | completed |
|---|---|---|---|---|---|---|---|---|---|
| coderabbit | OK | OK | OK | OK | OK | OK | OK | OK | 8/8 |
| proofline | OK | OK | OK | OK | OK | OK | OK | OK | 8/8 |

### Condition: with_snapshot

| Provider | 04 | 05 | 06 | completed |
|---|---|---|---|---|
| coderabbit | - | - | - | 0/3 |
| proofline | - | - | - | 0/3 |

Legend: OK completed · Q quota_stop · E error · - unattempted · . pending

## Scored findings (counts)

| Provider | correct_bug | false_warning | needs_deploy_info | valid_unanticipated | noise | missed |
|---|---|---|---|---|---|---|
| coderabbit | 3 | 0 | 0 | 1 | 0 | 0 |
| proofline | 3 | 1 | 0 | 2 | 0 | 0 |

_Columns are rubric buckets; see EXPERIMENT_PROTOCOL.md. `missed` = cases with a known defect where the reviewer produced no correct_bug finding._


## Missed defects (detail)


## Spotlight result (draft — verify/edit for the video)

Case 03 (batch queued deliveries), code_only. Base `pilot/base` -> head `pilot/03`.
Both reviewers flagged it. Proofline: "Worker leaves the last partial batch undelivered." CodeRabbit: "If the queue has 1-19 due jobs, this loop executes zero times." I verified by reading the change: `range(0, len(jobs) - 20 + 1, 20)` skips the remainder and, under 20 jobs, never runs; `deliver_due` then writes no receipts and returns a lower count. Both earned `correct_bug` against the frozen defect.
Limitation: I graded from the diff, not from a deployed run; a live load test with a non-multiple-of-20 queue would make the dropped-delivery count concrete.


## Caveat

Eight related changes in one application give limited evidence about performance elsewhere, even across many providers.