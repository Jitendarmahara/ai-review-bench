BEGIN TRANSACTION;
CREATE TABLE answer_key (
    case_id      TEXT NOT NULL,
    condition    TEXT NOT NULL,
    change_is_safe INTEGER,
    expected     TEXT,
    frozen_at    TEXT,
    PRIMARY KEY (case_id, condition)
);
INSERT INTO "answer_key" VALUES('01','code_only',0,'Keyset pagination orders by (scheduled_at DESC, id DESC) but the cursor filters WHERE scheduled_at < ? only. scheduled_at is non-unique, so rows sharing the boundary second are skipped across pages. Needs a compound (scheduled_at,id) cursor.','2026-11-23T19:36:59+00:00');
INSERT INTO "answer_key" VALUES('02','code_only',0,'Manual '',''.join replaces csv.writer, dropping quoting/escaping. A report name with a comma, quote, or newline corrupts the CSV structure.','2026-11-23T19:36:59+00:00');
INSERT INTO "answer_key" VALUES('03','code_only',0,'range(0, len-batch+1, batch) drops the final partial batch; with fewer than 20 due jobs it delivers nothing. Receipts/updates skipped for the remainder; deliveries silently lost.','2026-11-23T19:36:59+00:00');
INSERT INTO "answer_key" VALUES('04','code_only',NULL,'Dropping legacy_format is safe within this app (never read here) but unsafe if other deployments read it. Correct code-only answer: needs deployment info.','2026-11-23T19:36:59+00:00');
INSERT INTO "answer_key" VALUES('04','with_snapshot',0,'Snapshot: elm workers-17 (2 replicas) polls ''SELECT id, legacy_format ...''. Online DROP COLUMN breaks workers-17 on elm. Unsafe until workers-17 retired (cedar is fine).','2026-11-23T19:36:59+00:00');
INSERT INTO "answer_key" VALUES('05','code_only',NULL,'Batch 25->50 is safe only if the archive receiver accepts >=50 rows per request. Needs deployment info.','2026-11-23T19:36:59+00:00');
INSERT INTO "answer_key" VALUES('05','with_snapshot',0,'Snapshot: cedar max_rows_per_request=40. With 70 ready rows the first 50-row request exceeds 40 and is rejected in full, breaking export on cedar (elm max 100 is fine).','2026-11-23T19:36:59+00:00');
INSERT INTO "answer_key" VALUES('06','code_only',NULL,'Changing DELIVERY_QUEUE to ''report-dispatch'' is safe only if consumers subscribe to it. Needs deployment info.','2026-11-23T19:36:59+00:00');
INSERT INTO "answer_key" VALUES('06','with_snapshot',0,'Snapshot: elm subscribes only to ''reports''. New jobs tagged ''report-dispatch'' have no consumer on elm (8 due in window stranded). cedar subscribes to both and is fine.','2026-11-23T19:36:59+00:00');
INSERT INTO "answer_key" VALUES('07','code_only',1,'Partial index (queue, scheduled_at, id) WHERE delivered_at IS NULL exactly matches the deliver_due query and ORDER BY, and is covering. Correct and appropriate; no defect.','2026-11-23T19:36:59+00:00');
INSERT INTO "answer_key" VALUES('08','code_only',1,'total = sent + waiting = count(delivered_at) + (count(*) - count(delivered_at)) = count(*). Arithmetically exact; no defect.','2026-11-23T19:37:00+00:00');
CREATE TABLE findings (
    finding_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id       TEXT NOT NULL REFERENCES runs(run_id),
    text         TEXT NOT NULL,
    locator      TEXT
);
CREATE TABLE providers (
    name        TEXT PRIMARY KEY,
    kind        TEXT NOT NULL,
    bot_login   TEXT,
    notes       TEXT,
    added_at    TEXT NOT NULL
);
CREATE TABLE reviews (
    run_id       TEXT PRIMARY KEY REFERENCES runs(run_id),
    raw_review   TEXT,
    review_url   TEXT,
    captured_at  TEXT
);
CREATE TABLE runs (
    run_id       TEXT PRIMARY KEY,
    provider     TEXT NOT NULL REFERENCES providers(name),
    case_id      TEXT NOT NULL,
    condition    TEXT NOT NULL,
    base_sha     TEXT,
    head_sha     TEXT,
    repo         TEXT,
    pr_number    INTEGER,
    trigger      TEXT,
    model        TEXT,
    settings_json TEXT,
    is_retry     INTEGER NOT NULL DEFAULT 0,
    outcome      TEXT NOT NULL DEFAULT 'pending',
    created_at   TEXT NOT NULL
);
CREATE TABLE scores (
    finding_id     INTEGER PRIMARY KEY REFERENCES findings(finding_id),
    bucket         TEXT NOT NULL,
    reason         TEXT NOT NULL,
    grader         TEXT,
    provider_hidden INTEGER NOT NULL DEFAULT 1,
    second_reader  TEXT,
    graded_at      TEXT
);
DELETE FROM "sqlite_sequence";
COMMIT;
