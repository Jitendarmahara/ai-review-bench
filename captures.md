# Captured reviews and grades

Raw reviewer output from the run-repo PRs, with the blind grade against the frozen key.
Full reviews live on the PRs. Grades flagged **[FLAG: verify]** are deliberately debatable.


# Condition: code_only


## Case 01 (code_only) — key: defect
_Keyset pagination orders by (scheduled_at DESC, id DESC) but the cursor filters WHERE scheduled_at < ? only. scheduled_at is non-unique, so rows sharing the boundary second are skipped across pages. Needs a compound (scheduled_at,id) cursor._

### proofline  ([PR](https://github.com/Jitendarmahara/bench-run-proofline/pull/1))
- **correct_bug** — History skips reports tied at a page boundary
  - _reason:_ Matches key.
### coderabbit  ([PR](https://github.com/Jitendarmahara/bench-run-coderabbit/pull/1))
- **correct_bug** — Pagination skips deliveries sharing a scheduled_at at a page boundary
  - _reason:_ Matches key.

## Case 02 (code_only) — key: defect
_Manual ','.join replaces csv.writer, dropping quoting/escaping. A report name with a comma, quote, or newline corrupts the CSV structure._

### proofline  ([PR](https://github.com/Jitendarmahara/bench-run-proofline/pull/2))
- **correct_bug** — Report names with commas break CSV (no quoting)
  - _reason:_ Matches key.
### coderabbit  ([PR](https://github.com/Jitendarmahara/bench-run-coderabbit/pull/2))
- **correct_bug** — Fields not CSV-escaped; comma/quote/newline corrupts output
  - _reason:_ Matches key.

## Case 03 (code_only) — key: defect
_range(0, len-batch+1, batch) drops the final partial batch; with fewer than 20 due jobs it delivers nothing. Receipts/updates skipped for the remainder; deliveries silently lost._

### proofline  ([PR](https://github.com/Jitendarmahara/bench-run-proofline/pull/3))
- **correct_bug** — Worker leaves last partial batch undelivered (only full batches of 20)
  - _reason:_ Matches key.
### coderabbit  ([PR](https://github.com/Jitendarmahara/bench-run-coderabbit/pull/3))
- **correct_bug** — Final partial batch undelivered; <20 jobs delivers nothing
  - _reason:_ Matches key; caught <20 case too.

## Case 04 (code_only) — key: depends
_Dropping legacy_format is safe within this app (never read here) but unsafe if other deployments read it. Correct code-only answer: needs deployment info._

### proofline  ([PR](https://github.com/Jitendarmahara/bench-run-proofline/pull/4))
- **valid_unanticipated** **[FLAG: verify]** — Concurrent console startup can replay migration 002 and fail dropping already-removed column
  - _reason:_ Real concurrency race, but did not address deploy-dependency or ask for deploy info. FLAG.
### coderabbit  ([PR](https://github.com/Jitendarmahara/bench-run-coderabbit/pull/4))
- quiet review (no finding)

## Case 05 (code_only) — key: depends
_Batch 25->50 is safe only if the archive receiver accepts >=50 rows per request. Needs deployment info._

### proofline  ([PR](https://github.com/Jitendarmahara/bench-run-proofline/pull/5))
- quiet review (no finding)
### coderabbit  ([PR](https://github.com/Jitendarmahara/bench-run-coderabbit/pull/5))
- quiet review (no finding)

## Case 06 (code_only) — key: depends
_Changing DELIVERY_QUEUE to 'report-dispatch' is safe only if consumers subscribe to it. Needs deployment info._

### proofline  ([PR](https://github.com/Jitendarmahara/bench-run-proofline/pull/6))
- **valid_unanticipated** — New queue report-dispatch breaks documented worker (README uses work --queue reports)
  - _reason:_ Surfaces the consumer mismatch from README; key had code_only as depends.
### coderabbit  ([PR](https://github.com/Jitendarmahara/bench-run-coderabbit/pull/6))
- **valid_unanticipated** — New default queue leaves deliveries undelivered by documented worker
  - _reason:_ Same, via documented worker command.

## Case 07 (code_only) — key: safe
_Partial index (queue, scheduled_at, id) WHERE delivered_at IS NULL exactly matches the deliver_due query and ORDER BY, and is covering. Correct and appropriate; no defect._

### proofline  ([PR](https://github.com/Jitendarmahara/bench-run-proofline/pull/7))
- **false_warning** **[FLAG: verify]** — Concurrent upgrades can abort a console command (index already exists on race)
  - _reason:_ Key=safe: index is correct; race is pre-existing to the migration harness. FLAG.
### coderabbit  ([PR](https://github.com/Jitendarmahara/bench-run-coderabbit/pull/7))
- quiet review (no finding)

## Case 08 (code_only) — key: safe
_total = sent + waiting = count(delivered_at) + (count(*) - count(delivered_at)) = count(*). Arithmetically exact; no defect._

### proofline  ([PR](https://github.com/Jitendarmahara/bench-run-proofline/pull/8))
- quiet review (no finding)
### coderabbit  ([PR](https://github.com/Jitendarmahara/bench-run-coderabbit/pull/8))
- quiet review (no finding)

# Condition: with_snapshot


## Case 04 (with_snapshot) — key: defect
_Snapshot: elm workers-17 (2 replicas) polls 'SELECT id, legacy_format ...'. Online DROP COLUMN breaks workers-17 on elm. Unsafe until workers-17 retired (cedar is fine)._

### proofline  ([PR](https://github.com/Jitendarmahara/bench-run-proofline/pull/9))
- **valid_unanticipated** **[FLAG: verify]** — Active reader can fail during the online upgrade (framed via summary/migration concurrency), plus column-drop table rewrite
  - _reason:_ Grasped that concurrent readers break during the online drop, but did NOT identify the snapshot's workers-17/legacy_format reader. Run counts as missed for the keyed defect. FLAG.
### coderabbit  ([PR](https://github.com/Jitendarmahara/bench-run-coderabbit/pull/9))
- **correct_bug** — Migration breaks Elm's workers-17 replicas (poll SELECT id, legacy_format); retire/replace them and confirm no other reader before applying
  - _reason:_ Matches key exactly, citing the snapshot's workers-17.

## Case 05 (with_snapshot) — key: defect
_Snapshot: cedar max_rows_per_request=40. With 70 ready rows the first 50-row request exceeds 40 and is rejected in full, breaking export on cedar (elm max 100 is fine)._

### proofline  ([PR](https://github.com/Jitendarmahara/bench-run-proofline/pull/10))
- quiet review (no finding) — **MISSED** (key=defect)
### coderabbit  ([PR](https://github.com/Jitendarmahara/bench-run-coderabbit/pull/10))
- **correct_bug** — Batch 50 exceeds Cedar's 40-row receiver limit; first request rejected in full, cutover export to Cedar fails
  - _reason:_ Matches key exactly, citing Cedar's 40 limit.

## Case 06 (with_snapshot) — key: defect
_Snapshot: elm subscribes only to 'reports'. New jobs tagged 'report-dispatch' have no consumer on elm (8 due in window stranded). cedar subscribes to both and is fine._

### proofline  ([PR](https://github.com/Jitendarmahara/bench-run-proofline/pull/11))
- **correct_bug** — New jobs scheduled on report-dispatch but documented worker only selects reports; jobs left pending
  - _reason:_ Correctly identifies the stranding defect (via the quickstart rather than the snapshot's Elm data).
### coderabbit  ([PR](https://github.com/Jitendarmahara/bench-run-coderabbit/pull/11))
- **correct_bug** — Elm has no worker subscribed to report-dispatch; its 8 newly due jobs remain pending during the window
  - _reason:_ Matches key exactly, citing Elm's subscriptions from the snapshot.
