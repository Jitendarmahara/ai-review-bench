# Ground-truth analysis (freeze BEFORE running any reviewer)

My reasoning for each of the 11 (case × condition) cells. **Verify every one
yourself** — the 2-minute video asks you to defend a scoring call, so you must be
able to explain these in your own words. Where I flag confidence, double-check the
lower-confidence ones first. Apply a patch with `git apply -p0 cases/NN/change.patch`
on a branch off the baseline, or read the `pilot/NN` branch, and confirm.

App under test: a scheduled-report service over SQLite. `deliveries(id, report,
scheduled_at, queue, legacy_format DEFAULT 'csv', delivered_at)` and
`receipts(delivery_id, recorded_at)`. The console schedules reports, a worker
delivers due jobs per queue, and there are export/archive/summary paths.

Design of the set (what I inferred): 01–03 are pure-code defects, 04–06 are
deploy-dependent (unknowable from code alone, decidable from the snapshot), 07–08
are safe. A good reviewer catches 01–03, asks for deploy info on 04–06 code-only,
and stays quiet on 07–08.

---

## 01 — Page report history by scheduled time → DEFECT (code_only). High confidence.
The change orders by `scheduled_at DESC, id DESC` (a compound order for stability)
but the cursor filters `WHERE scheduled_at < ?` using only `scheduled_at`, and
sets `next_cursor = rows[limit-1][2]` (the scheduled_at). `scheduled_at` is **not
unique** — the service doc says schedulers can enqueue multiple reports for the
same second. So rows that share the boundary second but fall on the next page are
**skipped**: the next query excludes every row with `scheduled_at == cursor`.
Correct keyset pagination needs a compound cursor `(scheduled_at, id) < (?, ?)`.
A reviewer should flag dropped/duplicated rows at page boundaries.

## 02 — Stream the report export → DEFECT (code_only). Medium-high confidence.
It replaces `csv.writer` with manual `",".join(map(str, row))`. That drops CSV
quoting/escaping. `report` is arbitrary user text; a name containing a comma,
double-quote, or newline corrupts the row/column structure (csv.writer would quote
it). Streaming the cursor instead of `fetchall()` is fine; the escaping loss is the
defect. (Lower confidence only because someone could argue names are controlled —
but the schema allows any text, so it's a real regression.)

## 03 — Batch queued deliveries → DEFECT (code_only). Very high confidence.
`for start in range(0, len(jobs) - batch_size + 1, batch_size)` with `batch_size=20`
drops the final partial batch, and when there are fewer than 20 due jobs it delivers
**nothing** (`range(0, negative, 20)` is empty). Receipts and `delivered_at` updates
are skipped for the remainder, so deliveries are silently lost. `processed` honestly
reports the smaller count, which hides the drop. Canonical off-by-batch bug.

## 04 — Retire the legacy delivery column
`migrations/002` runs `ALTER TABLE deliveries DROP COLUMN legacy_format`.
- **code_only → DEPENDS (needs_deploy_info).** Nothing in this app reads
  `legacy_format`, so it's safe *within the code*. But dropping a column is unsafe
  if another deployment reads it, which code can't reveal. The correct code-only
  answer is "I need deployment info." A confident "safe" is wrong; a confident
  "broken" is also unsupported.
- **with_snapshot → DEFECT.** The inventory shows site `elm` running `workers-17`
  (2 replicas) whose poll is `SELECT id, legacy_format FROM deliveries ...`. The
  migration runs online while that worker polls, so on elm's database the column
  drop breaks `workers-17`. `cedar` only runs `workers-18` (reads `report`), so
  cedar is fine — but elm breaks, so the migration as proposed is unsafe until
  `workers-17` is retired. Reviewer should name elm/workers-17 and cite the poll_sql.

## 05 — Increase export batch size (25 → 50)
`EXPORT_BATCH_SIZE` controls rows per archive request (`export_to_sink` sends one
request per batch).
- **code_only → DEPENDS (needs_deploy_info).** Safe only if the receiver accepts
  ≥50 rows per request; unknowable from code.
- **with_snapshot → DEFECT.** Receiver limits: `elm` max 100, `cedar` max 40, each
  with 70 ready rows. "An oversized request is rejected in full." With batch 50 and
  70 ready rows, the first request is 50 rows. On `cedar` (max 40), a 50-row request
  is rejected in full → export breaks on cedar. The old value 25 stayed under 40.
  elm (max 100) is fine. cedar breaks → unsafe. Reviewer should cite cedar's 40 limit.

## 06 — Use the new delivery queue ("reports" → "report-dispatch")
`schedule()` tags new deliveries with `DELIVERY_QUEUE`.
- **code_only → DEPENDS (needs_deploy_info).** Safe only if consumers subscribe to
  `report-dispatch`; unknowable from code.
- **with_snapshot → DEFECT.** Subscriptions: `elm` subscribes to `["reports"]` only;
  `cedar` subscribes to `["reports","report-dispatch"]`. New jobs tagged
  `report-dispatch` have **no consumer on elm** (8 new jobs due in the window would be
  stranded). cedar is fine. elm breaks → unsafe. Reviewer should name elm's missing
  subscription.

## 07 — Index pending deliveries → SAFE (code_only). High confidence.
`migrations/002` creates a partial index `deliveries(queue, scheduled_at, id) WHERE
delivered_at IS NULL`. The worker query is `WHERE queue=? AND delivered_at IS NULL
AND scheduled_at<=? ORDER BY scheduled_at, id`. The index matches exactly: equality
on `queue`, range + order on `scheduled_at, id`, partial predicate on the same
`delivered_at IS NULL`, and it's covering (selects `id`). Correct and appropriate.
A quiet review, or a positive "matches the hot query," is the right outcome. Inventing
a problem here is a `false_warning`.

## 08 — Include a total in the activity summary → SAFE (code_only). High confidence.
`total = sent + waiting = count(delivered_at) + (count(*) - count(delivered_at)) =
count(*)`. Arithmetically exact, no double counting, no NULL edge. Correct. Quiet or
positive review is right; a flagged "bug" is a `false_warning`.

---

## Summary table

| Case | code_only | with_snapshot |
|---|---|---|
| 01 pagination | defect | — |
| 02 streamed export | defect | — |
| 03 batched deliveries | defect | — |
| 04 drop legacy column | depends | defect (elm workers-17) |
| 05 bigger batch | depends | defect (cedar max 40) |
| 06 new queue | depends | defect (elm no subscriber) |
| 07 partial index | safe | — |
| 08 summary total | safe | — |

How to read scores against this key:
- On a `defect` cell, a `correct_bug` finding naming the real issue is the win; a
  completed review with no such finding is a **missed** defect.
- On a `depends` cell (code_only for 04–06), `needs_deploy_info` is the correct
  reviewer behavior; a confident safe/broken verdict is weaker.
- On a `safe` cell, a quiet review (no correctness finding) is good; a correctness
  finding is a `false_warning`.

Run `./freeze_key.sh` to write all 11 cells into the DB (commit the DB dump so the
key is provably frozen before any run — see git history in your submission).
