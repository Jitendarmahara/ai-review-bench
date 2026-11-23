# AI Review Benchmark — results

## Coverage

### Denominators

- Distinct reviewers: 2
- Distinct cases touched: 8
- Completed provider-case pairs (non-retry): 22
- Repeats (variability runs): 0


### Condition: code_only

| Provider | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | completed |
|---|---|---|---|---|---|---|---|---|---|
| coderabbit | OK | OK | OK | OK | OK | OK | OK | OK | 8/8 |
| proofline | OK | OK | OK | OK | OK | OK | OK | OK | 8/8 |

### Condition: with_snapshot

| Provider | 04 | 05 | 06 | completed |
|---|---|---|---|---|
| coderabbit | OK | OK | OK | 3/3 |
| proofline | OK | OK | OK | 3/3 |

Legend: OK completed · Q quota_stop · E error · - unattempted · . pending

## Scored findings (counts)

| Provider | correct_bug | false_warning | needs_deploy_info | valid_unanticipated | noise | missed |
|---|---|---|---|---|---|---|
| coderabbit | 6 | 0 | 0 | 1 | 0 | 0 |
| proofline | 4 | 1 | 0 | 3 | 0 | 2 |

_Columns are rubric buckets; see EXPERIMENT_PROTOCOL.md. `missed` = cases with a known defect where the reviewer produced no correct_bug finding._


## Missed defects (detail)

- proofline: 04/with_snapshot, 05/with_snapshot

## Spotlight result

Case 05 (increase export batch size 25 -> 50), with_snapshot. Base `pilot/base` -> head `pilot/05-snap` (adds DEPLOYMENT_SNAPSHOT.md).
The snapshot records per-site receiver limits: Elm accepts 100 rows/request, Cedar only 40, each with 70 ready rows, and "an oversized request is rejected in full."
CodeRabbit's finding: "Raising the export batch size to 50 makes the first request to the cedar site exceed its 40-row receiver limit. The receiver rejects that request in full, so the cutover export to cedar is likely to fail." I verified against the snapshot: 70 ready rows at batch 50 sends a first request of 50 rows; 50 > 40, so Cedar rejects it. The old value 25 fit under 40. Graded correct_bug.
Proofline returned no findings on the same PR, so it missed this defect. That is the clearest difference in the run: with deployment context supplied, CodeRabbit resolved all three deploy-dependent cases (04, 05, 06); Proofline resolved one (06) and missed two.
Limitation: I did not stand up the Cedar receiver to observe the rejection; the conclusion rests on the snapshot's stated 40-row limit and reject-in-full rule.


## Caveat

Eight related changes in one application give limited evidence about performance elsewhere, even across many providers.

## Evidence trace (status)

The Cloud Run deploy path (`gcp/`) is built and **verified locally**: `python3 gcp/deploy.py smoke --docker` builds the image, runs the container, and asserts the returned evidence (commit, request_id, report, receipt). The hosted deploy -> verify -> receipt run is pending GCP account verification (India tax/KYC) on the billing account, so it was not run against the cloud. It is a single command once billing is active:
`python3 gcp/deploy.py deploy --project <PROJ> --repo bench --service ai-review-bench && python3 gcp/deploy.py verify --project <PROJ> --service ai-review-bench`
The starter's AWS path (`aws/`) is unchanged and runs the same trace for anyone with an AWS account.
