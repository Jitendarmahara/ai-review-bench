# Captured reviews and grades

Raw reviewer output pulled from the run-repo PRs, with the blind grade against the frozen key.
Full reviews live on the PRs (links below). Grades flagged `review` are deliberately debatable — verify them.


## Case 01 — key: defect
_Keyset pagination orders by (scheduled_at DESC, id DESC) but the cursor filters WHERE scheduled_at < ? only. scheduled_at is non-unique, so rows sharing the boundary second are skipped across pages. Needs a compound (scheduled_at,id) cursor._

### proofline  ([PR](https://github.com/Jitendarmahara/bench-run-proofline/pull/1))
- **correct_bug** — History skips reports tied at a page boundary: sorts by scheduled_at+id but resumes strictly before the cursor timestamp, excluding same-second rows
  - _grade reason:_ Matches key: keyset pagination on non-unique scheduled_at drops boundary-tied rows.
### coderabbit  ([PR](https://github.com/Jitendarmahara/bench-run-coderabbit/pull/1))
- **correct_bug** — Pagination skips deliveries sharing a scheduled_at value at a page boundary
  - _grade reason:_ Matches key: non-unique scheduled_at cursor drops rows.

## Case 02 — key: defect
_Manual ','.join replaces csv.writer, dropping quoting/escaping. A report name with a comma, quote, or newline corrupts the CSV structure._

### proofline  ([PR](https://github.com/Jitendarmahara/bench-run-proofline/pull/2))
- **correct_bug** — Report names containing commas break CSV exports (no quoting; keep cursor but use csv.writer)
  - _grade reason:_ Matches key: manual join drops CSV escaping.
### coderabbit  ([PR](https://github.com/Jitendarmahara/bench-run-coderabbit/pull/2))
- **correct_bug** — Fields not escaped as CSV; a comma/quote/newline corrupts the output
  - _grade reason:_ Matches key: missing CSV escaping.

## Case 03 — key: defect
_range(0, len-batch+1, batch) drops the final partial batch; with fewer than 20 due jobs it delivers nothing. Receipts/updates skipped for the remainder; deliveries silently lost._

### proofline  ([PR](https://github.com/Jitendarmahara/bench-run-proofline/pull/3))
- **correct_bug** — Worker leaves the last partial batch undelivered; loop visits only full batches of 20
  - _grade reason:_ Matches key: dropped final partial batch.
### coderabbit  ([PR](https://github.com/Jitendarmahara/bench-run-coderabbit/pull/3))
- **correct_bug** — Final partial batch undelivered; queues with 1-19 jobs deliver nothing (loop runs zero times)
  - _grade reason:_ Matches key, and also caught the <20 case.

## Case 04 — key: depends
_Dropping legacy_format is safe within this app (never read here) but unsafe if other deployments read it. Correct code-only answer: needs deployment info._

### proofline  ([PR](https://github.com/Jitendarmahara/bench-run-proofline/pull/4))
- **valid_unanticipated** **[FLAG: verify]** — Concurrent console startup can replay migration 002 and fail dropping the already-removed legacy_format column
  - _grade reason:_ Real migration-concurrency race, but did NOT address the keyed deploy-dependency (external readers of legacy_format) or ask for deploy info. FLAG for your review.
### coderabbit  ([PR](https://github.com/Jitendarmahara/bench-run-coderabbit/pull/4))
- quiet review (no finding)

## Case 05 — key: depends
_Batch 25->50 is safe only if the archive receiver accepts >=50 rows per request. Needs deployment info._

### proofline  ([PR](https://github.com/Jitendarmahara/bench-run-proofline/pull/5))
- quiet review (no finding)
### coderabbit  ([PR](https://github.com/Jitendarmahara/bench-run-coderabbit/pull/5))
- quiet review (no finding)

## Case 06 — key: depends
_Changing DELIVERY_QUEUE to 'report-dispatch' is safe only if consumers subscribe to it. Needs deployment info._

### proofline  ([PR](https://github.com/Jitendarmahara/bench-run-proofline/pull/6))
- **valid_unanticipated** — New queue report-dispatch breaks the documented worker (README runs work --queue reports); scheduled report left pending
  - _grade reason:_ Correctly surfaces the queue/consumer mismatch from the repo README — essentially the with_snapshot concern from code alone. Key had code_only as depends.
### coderabbit  ([PR](https://github.com/Jitendarmahara/bench-run-coderabbit/pull/6))
- **valid_unanticipated** — New default queue leaves scheduled deliveries undelivered by the documented worker (work --queue reports)
  - _grade reason:_ Same as above; found via the documented worker command.

## Case 07 — key: safe
_Partial index (queue, scheduled_at, id) WHERE delivered_at IS NULL exactly matches the deliver_due query and ORDER BY, and is covering. Correct and appropriate; no defect._

### proofline  ([PR](https://github.com/Jitendarmahara/bench-run-proofline/pull/7))
- **false_warning** **[FLAG: verify]** — Concurrent upgrades can abort a console command: migration 002 index already exists on a race
  - _grade reason:_ Key=safe: the partial index itself is correct. The migration-concurrency race is pre-existing to the migration harness, not a defect this change introduces. FLAG for your review.
### coderabbit  ([PR](https://github.com/Jitendarmahara/bench-run-coderabbit/pull/7))
- quiet review (no finding)

## Case 08 — key: safe
_total = sent + waiting = count(delivered_at) + (count(*) - count(delivered_at)) = count(*). Arithmetically exact; no defect._

### proofline  ([PR](https://github.com/Jitendarmahara/bench-run-proofline/pull/8))
- quiet review (no finding)
### coderabbit  ([PR](https://github.com/Jitendarmahara/bench-run-coderabbit/pull/8))
- quiet review (no finding)
