"""Provider x case coverage tables, one per condition, with raw denominators."""
from __future__ import annotations

from . import db
from .config import CASES, conditions_for

SYM = {"completed": "OK", "quota_stop": "Q", "error": "E",
       "unattempted": "-", "pending": "."}


def _primary_runs(conn):
    rows = conn.execute(
        "SELECT provider, case_id, condition, outcome, run_id FROM runs WHERE is_retry=0 ORDER BY created_at"
    ).fetchall()
    latest = {}
    for r in rows:
        latest[(r["provider"], r["case_id"], r["condition"])] = r["outcome"]
    return latest


def table(conn, condition):
    provs = [p["name"] for p in db.providers(conn)]
    cases = [c for c in CASES if condition in conditions_for(c)]
    latest = _primary_runs(conn)

    header = "| Provider | " + " | ".join(cases) + " | completed |"
    sep = "|" + "---|" * (len(cases) + 2)
    lines = [f"### Condition: {condition}", "", header, sep]
    for p in provs:
        cells, done = [], 0
        for c in cases:
            o = latest.get((p, c, condition))
            cells.append(SYM.get(o, "-") if o else "-")
            if o == "completed":
                done += 1
        lines.append(f"| {p} | " + " | ".join(cells) + f" | {done}/{len(cases)} |")
    return "\n".join(lines)


def denominators(conn):
    provs = db.providers(conn)
    runs = db.runs(conn)
    distinct_cases = {r["case_id"] for r in runs}
    completed_pairs = sum(1 for r in runs if r["outcome"] == "completed" and not r["is_retry"])
    repeats = sum(1 for r in runs if r["is_retry"])
    return (
        "### Denominators\n\n"
        f"- Distinct reviewers: {len(provs)}\n"
        f"- Distinct cases touched: {len(distinct_cases)}\n"
        f"- Completed provider-case pairs (non-retry): {completed_pairs}\n"
        f"- Repeats (variability runs): {repeats}\n"
    )


def render(conn):
    parts = ["## Coverage\n", denominators(conn), ""]
    for cond in ("code_only", "with_snapshot"):
        parts.append(table(conn, cond))
        parts.append("")
    parts.append("Legend: OK completed · Q quota_stop · E error · - unattempted · . pending")
    return "\n".join(parts)
