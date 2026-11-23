PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS providers (
    name        TEXT PRIMARY KEY,
    kind        TEXT NOT NULL,
    bot_login   TEXT,
    notes       TEXT,
    added_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
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

CREATE TABLE IF NOT EXISTS reviews (
    run_id       TEXT PRIMARY KEY REFERENCES runs(run_id),
    raw_review   TEXT,
    review_url   TEXT,
    captured_at  TEXT
);

CREATE TABLE IF NOT EXISTS findings (
    finding_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id       TEXT NOT NULL REFERENCES runs(run_id),
    text         TEXT NOT NULL,
    locator      TEXT
);

CREATE TABLE IF NOT EXISTS scores (
    finding_id     INTEGER PRIMARY KEY REFERENCES findings(finding_id),
    bucket         TEXT NOT NULL,
    reason         TEXT NOT NULL,
    grader         TEXT,
    provider_hidden INTEGER NOT NULL DEFAULT 1,
    second_reader  TEXT,
    graded_at      TEXT
);

CREATE TABLE IF NOT EXISTS answer_key (
    case_id      TEXT NOT NULL,
    condition    TEXT NOT NULL,
    change_is_safe INTEGER,
    expected     TEXT,
    frozen_at    TEXT,
    PRIMARY KEY (case_id, condition)
);
