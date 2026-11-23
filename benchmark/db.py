from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone

DEFAULT_DB = os.environ.get("BENCH_DB", "bench.db")
SCHEMA = os.path.join(os.path.dirname(__file__), "schema.sql")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(path=DEFAULT_DB):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init(path=DEFAULT_DB):
    with open(SCHEMA) as f:
        ddl = f.read()
    conn = connect(path)
    with conn:
        conn.executescript(ddl)
    conn.close()


def add_provider(conn, name, kind, bot_login=None, notes=None):
    with conn:
        conn.execute(
            "INSERT OR REPLACE INTO providers(name,kind,bot_login,notes,added_at) VALUES(?,?,?,?,?)",
            (name, kind, bot_login, notes, now()),
        )


def providers(conn):
    return conn.execute("SELECT * FROM providers ORDER BY name").fetchall()


def next_seq(conn, provider, case_id, condition):
    row = conn.execute(
        "SELECT COUNT(*) c FROM runs WHERE provider=? AND case_id=? AND condition=?",
        (provider, case_id, condition),
    ).fetchone()
    return row["c"] + 1


def create_run(conn, provider, case_id, condition, **kw):
    seq = next_seq(conn, provider, case_id, condition)
    run_id = f"{provider}-{case_id}-{condition}-{seq}"
    with conn:
        conn.execute(
            """INSERT INTO runs(run_id,provider,case_id,condition,base_sha,head_sha,repo,
                   pr_number,trigger,model,settings_json,is_retry,outcome,created_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                run_id, provider, case_id, condition,
                kw.get("base_sha"), kw.get("head_sha"), kw.get("repo"),
                kw.get("pr_number"), kw.get("trigger"), kw.get("model"),
                kw.get("settings_json"), int(kw.get("is_retry", 0)),
                kw.get("outcome", "pending"), now(),
            ),
        )
    return run_id


def set_outcome(conn, run_id, outcome):
    from .rubric import validate_outcome
    validate_outcome(outcome)
    with conn:
        conn.execute("UPDATE runs SET outcome=? WHERE run_id=?", (outcome, run_id))


def runs(conn):
    return conn.execute("SELECT * FROM runs ORDER BY provider, case_id, condition").fetchall()


def get_run(conn, run_id):
    return conn.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()


def save_review(conn, run_id, raw_review, review_url=None):
    with conn:
        conn.execute(
            "INSERT OR REPLACE INTO reviews(run_id,raw_review,review_url,captured_at) VALUES(?,?,?,?)",
            (run_id, raw_review, review_url, now()),
        )
        conn.execute("UPDATE runs SET outcome='completed' WHERE run_id=? AND outcome='pending'", (run_id,))


def add_finding(conn, run_id, text, locator=None):
    with conn:
        cur = conn.execute(
            "INSERT INTO findings(run_id,text,locator) VALUES(?,?,?)", (run_id, text, locator)
        )
    return cur.lastrowid


def ungraded_findings(conn):
    return conn.execute(
        """SELECT f.finding_id, f.run_id, f.text, f.locator
           FROM findings f LEFT JOIN scores s ON s.finding_id=f.finding_id
           WHERE s.finding_id IS NULL ORDER BY f.finding_id"""
    ).fetchall()


def score_finding(conn, finding_id, bucket, reason, grader=None, provider_hidden=1, second_reader=None):
    from .rubric import validate_bucket
    validate_bucket(bucket)
    with conn:
        conn.execute(
            """INSERT OR REPLACE INTO scores(finding_id,bucket,reason,grader,provider_hidden,second_reader,graded_at)
               VALUES(?,?,?,?,?,?,?)""",
            (finding_id, bucket, reason, grader, int(provider_hidden), second_reader, now()),
        )


def freeze_key(conn, case_id, condition, change_is_safe, expected):
    with conn:
        conn.execute(
            """INSERT OR REPLACE INTO answer_key(case_id,condition,change_is_safe,expected,frozen_at)
               VALUES(?,?,?,?,?)""",
            (case_id, condition, change_is_safe, expected, now()),
        )


def answer_key(conn):
    return conn.execute("SELECT * FROM answer_key ORDER BY case_id, condition").fetchall()


def get_key(conn, case_id, condition):
    return conn.execute(
        "SELECT * FROM answer_key WHERE case_id=? AND condition=?", (case_id, condition)
    ).fetchone()
