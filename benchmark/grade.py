"""Blind grading: export ungraded findings with the provider hidden, grade, re-import."""
from __future__ import annotations

import json

from . import db
from .rubric import BUCKETS


def export(conn, path):
    rows = db.ungraded_findings(conn)
    items = []
    for r in rows:
        run = db.get_run(conn, r["run_id"])
        key = db.get_key(conn, run["case_id"], run["condition"])
        items.append({
            "finding_id": r["finding_id"],
            "case_id": run["case_id"],
            "condition": run["condition"],
            "expected": (key["expected"] if key else "NO KEY FROZEN — run freeze-key first"),
            "change_is_safe": (key["change_is_safe"] if key else None),
            "finding_text": r["text"],
            "locator": r["locator"],
            "bucket": "",
            "reason": "",
        })
    payload = {"_buckets": BUCKETS, "items": items}
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    return len(items)


def import_(conn, path, grader="jitendar", second_reader=None):
    with open(path) as f:
        payload = json.load(f)
    n = 0
    for it in payload.get("items", []):
        b = (it.get("bucket") or "").strip()
        if not b:
            continue
        db.score_finding(conn, it["finding_id"], b, it.get("reason", "").strip(),
                         grader=grader, provider_hidden=1, second_reader=second_reader)
        n += 1
    return n
