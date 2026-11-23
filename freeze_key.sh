#!/usr/bin/env bash
# Freeze the ground-truth key into the benchmark DB BEFORE running any reviewer.
# Verdicts and reasoning: ANSWER_KEY_ANALYSIS.md. VERIFY each call yourself first.
# Run from the repo root after `python3 -m benchmark init`.
set -euo pipefail
B="python3 -m benchmark"

$B freeze-key 01 code_only defect \
  --expected "Keyset pagination orders by (scheduled_at DESC, id DESC) but the cursor filters WHERE scheduled_at < ? only. scheduled_at is non-unique, so rows sharing the boundary second are skipped across pages. Needs a compound (scheduled_at,id) cursor."

$B freeze-key 02 code_only defect \
  --expected "Manual ','.join replaces csv.writer, dropping quoting/escaping. A report name with a comma, quote, or newline corrupts the CSV structure."

$B freeze-key 03 code_only defect \
  --expected "range(0, len-batch+1, batch) drops the final partial batch; with fewer than 20 due jobs it delivers nothing. Receipts/updates skipped for the remainder; deliveries silently lost."

$B freeze-key 04 code_only depends \
  --expected "Dropping legacy_format is safe within this app (never read here) but unsafe if other deployments read it. Correct code-only answer: needs deployment info."
$B freeze-key 04 with_snapshot defect \
  --expected "Snapshot: elm workers-17 (2 replicas) polls 'SELECT id, legacy_format ...'. Online DROP COLUMN breaks workers-17 on elm. Unsafe until workers-17 retired (cedar is fine)."

$B freeze-key 05 code_only depends \
  --expected "Batch 25->50 is safe only if the archive receiver accepts >=50 rows per request. Needs deployment info."
$B freeze-key 05 with_snapshot defect \
  --expected "Snapshot: cedar max_rows_per_request=40. With 70 ready rows the first 50-row request exceeds 40 and is rejected in full, breaking export on cedar (elm max 100 is fine)."

$B freeze-key 06 code_only depends \
  --expected "Changing DELIVERY_QUEUE to 'report-dispatch' is safe only if consumers subscribe to it. Needs deployment info."
$B freeze-key 06 with_snapshot defect \
  --expected "Snapshot: elm subscribes only to 'reports'. New jobs tagged 'report-dispatch' have no consumer on elm (8 due in window stranded). cedar subscribes to both and is fine."

$B freeze-key 07 code_only safe \
  --expected "Partial index (queue, scheduled_at, id) WHERE delivered_at IS NULL exactly matches the deliver_due query and ORDER BY, and is covering. Correct and appropriate; no defect."

$B freeze-key 08 code_only safe \
  --expected "total = sent + waiting = count(delivered_at) + (count(*) - count(delivered_at)) = count(*). Arithmetically exact; no defect."

echo
echo "Frozen key:"
python3 -m benchmark status | head -2
echo "Dump and commit it as proof-of-freeze:"
echo "  sqlite3 \"\${BENCH_DB:-bench.db}\" .dump > frozen_key.sql && git add frozen_key.sql"
