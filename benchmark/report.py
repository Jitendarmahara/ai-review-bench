"""Summary stats from graded findings, plus the report scaffold."""
from __future__ import annotations

from collections import defaultdict

from . import db
from .rubric import BUCKETS


def bucket_counts(conn):
    rows = conn.execute(
        """SELECT r.provider AS provider, s.bucket AS bucket, COUNT(*) AS n
           FROM scores s JOIN findings f ON f.finding_id=s.finding_id
           JOIN runs r ON r.run_id=f.run_id
           GROUP BY r.provider, s.bucket"""
    ).fetchall()
    out = defaultdict(lambda: defaultdict(int))
    for row in rows:
        out[row["provider"]][row["bucket"]] = row["n"]
    return out


def missed_defects(conn):
    out = defaultdict(list)
    keys = {(k["case_id"], k["condition"]): k for k in db.answer_key(conn)
            if k["change_is_safe"] == 0}
    runs = conn.execute("SELECT * FROM runs WHERE outcome='completed' AND is_retry=0").fetchall()
    for r in runs:
        key = keys.get((r["case_id"], r["condition"]))
        if not key:
            continue
        hit = conn.execute(
            """SELECT COUNT(*) c FROM scores s JOIN findings f ON f.finding_id=s.finding_id
               WHERE f.run_id=? AND s.bucket='correct_bug'""",
            (r["run_id"],),
        ).fetchone()["c"]
        if hit == 0:
            out[r["provider"]].append(f"{r['case_id']}/{r['condition']}")
    return out


def summary_table(conn):
    counts = bucket_counts(conn)
    missed = missed_defects(conn)
    cols = list(BUCKETS.keys())
    head = "| Provider | " + " | ".join(cols) + " | missed |"
    sep = "|" + "---|" * (len(cols) + 2)
    lines = [head, sep]
    for p in [pr["name"] for pr in db.providers(conn)]:
        row = counts.get(p, {})
        cells = [str(row.get(b, 0)) for b in cols]
        lines.append(f"| {p} | " + " | ".join(cells) + f" | {len(missed.get(p, []))} |")
    return "\n".join(lines)


def render(conn):
    from . import coverage
    parts = [
        "# AI Review Benchmark — results\n",
        coverage.render(conn),
        "\n## Scored findings (counts)\n",
        summary_table(conn),
        "\n_Columns are rubric buckets; see EXPERIMENT_PROTOCOL.md. "
        "`missed` = cases with a known defect where the reviewer produced no correct_bug finding._\n",
        "\n## Missed defects (detail)\n",
    ]
    for p, cases in missed_defects(conn).items():
        parts.append(f"- {p}: {', '.join(cases) if cases else 'none'}")
    parts.append("\n## Spotlight result (fill in)\n")
    parts.append("Pick ONE result. Walk from the commit + the reviewer's original comment "
                 "to the behavior you verified and the score you assigned. State one limitation.\n")
    parts.append("\n## Caveat\n")
    parts.append("Eight related changes in one application give limited evidence about "
                 "performance elsewhere, even across many providers.")
    return "\n".join(parts)
