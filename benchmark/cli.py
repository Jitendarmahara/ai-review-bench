"""`python -m benchmark <command>`. See SETUP.md for the full pipeline."""
from __future__ import annotations

import argparse
import sys

from . import db, coverage, report, grade
from .config import SEED_PROVIDERS, CASES, conditions_for
from .providers import for_kind


def cmd_init(a):
    db.init(a.db)
    print(f"initialized {a.db}")


def cmd_seed(a):
    conn = db.connect(a.db)
    for name, kind, bot, notes in SEED_PROVIDERS:
        db.add_provider(conn, name, kind, bot, notes)
    print(f"seeded {len(SEED_PROVIDERS)} providers (verify bot logins — see SETUP.md)")


def cmd_add_provider(a):
    conn = db.connect(a.db)
    db.add_provider(conn, a.name, a.kind, a.bot_login, a.notes)
    print(f"provider {a.name} ({a.kind}) added")


def cmd_freeze_key(a):
    conn = db.connect(a.db)
    safe = {"safe": 1, "defect": 0, "depends": None}[a.verdict]
    db.freeze_key(conn, a.case, a.condition, safe, a.expected)
    print(f"froze key for {a.case}/{a.condition}: verdict={a.verdict}")


def cmd_open_pr(a):
    conn = db.connect(a.db)
    run_id = db.create_run(
        conn, a.provider, a.case, a.condition,
        repo=a.repo, pr_number=a.pr, base_sha=a.base_sha, head_sha=a.head_sha,
        trigger=a.trigger, model=a.model, is_retry=a.retry,
    )
    print(f"run {run_id} recorded (repo={a.repo} pr=#{a.pr})")


def cmd_capture(a):
    conn = db.connect(a.db)
    run = db.get_run(conn, a.run_id)
    if not run:
        sys.exit(f"no such run {a.run_id}")
    if a.from_file:
        raw = open(a.from_file).read()
        db.save_review(conn, a.run_id, raw, a.url)
        print(f"captured manual review for {a.run_id} ({len(raw)} chars)")
        return
    prov_row = conn.execute("SELECT * FROM providers WHERE name=?", (run["provider"],)).fetchone()
    provider = for_kind(prov_row["kind"])(prov_row["name"], prov_row["bot_login"])
    res = provider.capture(run)
    print(f"[{run['provider']}] outcome={res.outcome} :: {res.note}")
    if res.raw_review:
        db.save_review(conn, a.run_id, res.raw_review, res.review_url)
        print(f"captured review ({len(res.raw_review)} chars) -> saved")
    elif res.outcome in ("quota_stop", "error", "unattempted"):
        db.set_outcome(conn, a.run_id, res.outcome)


def cmd_set_outcome(a):
    conn = db.connect(a.db)
    db.set_outcome(conn, a.run_id, a.outcome)
    print(f"{a.run_id} -> {a.outcome}")


def cmd_add_finding(a):
    conn = db.connect(a.db)
    fid = db.add_finding(conn, a.run_id, a.text, a.locator)
    print(f"finding #{fid} added to {a.run_id}")


def cmd_grade_export(a):
    conn = db.connect(a.db)
    n = grade.export(conn, a.file)
    print(f"exported {n} ungraded findings (provider hidden) -> {a.file}")


def cmd_grade_import(a):
    conn = db.connect(a.db)
    n = grade.import_(conn, a.file, grader=a.grader, second_reader=a.second_reader)
    print(f"imported {n} grades")


def cmd_coverage(a):
    conn = db.connect(a.db)
    print(coverage.render(conn))


def cmd_report(a):
    conn = db.connect(a.db)
    text = report.render(conn)
    if a.out:
        open(a.out, "w").write(text)
        print(f"wrote {a.out}")
    else:
        print(text)


def cmd_status(a):
    conn = db.connect(a.db)
    provs = db.providers(conn)
    runs = db.runs(conn)
    keys = db.answer_key(conn)
    print(f"providers: {len(provs)} | runs: {len(runs)} | frozen keys: {len(keys)}")
    cells = sum(len(conditions_for(c)) for c in CASES)
    done = sum(1 for r in runs if r["outcome"] == "completed" and not r["is_retry"])
    print(f"target cells (case x condition): {cells} | completed runs: {done}")
    for r in runs:
        print(f"  {r['run_id']:38} {r['outcome']}")


def build_parser():
    p = argparse.ArgumentParser(prog="benchmark", description="AI review benchmark harness")
    p.add_argument("--db", default=db.DEFAULT_DB, help="sqlite path (default bench.db or $BENCH_DB)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init").set_defaults(func=cmd_init)
    sub.add_parser("seed-providers").set_defaults(func=cmd_seed)
    sub.add_parser("status").set_defaults(func=cmd_status)

    ap = sub.add_parser("add-provider"); ap.set_defaults(func=cmd_add_provider)
    ap.add_argument("name"); ap.add_argument("kind", choices=["github_bot", "manual", "api"])
    ap.add_argument("--bot-login"); ap.add_argument("--notes")

    fk = sub.add_parser("freeze-key"); fk.set_defaults(func=cmd_freeze_key)
    fk.add_argument("case", choices=list(CASES))
    fk.add_argument("condition", choices=["code_only", "with_snapshot"])
    fk.add_argument("verdict", choices=["safe", "defect", "depends"])
    fk.add_argument("--expected", required=True, help="the correct verdict / defect description")

    op = sub.add_parser("open-pr"); op.set_defaults(func=cmd_open_pr)
    op.add_argument("provider"); op.add_argument("case", choices=list(CASES))
    op.add_argument("condition", choices=["code_only", "with_snapshot"])
    op.add_argument("--repo", required=True); op.add_argument("--pr", type=int, required=True)
    op.add_argument("--base-sha"); op.add_argument("--head-sha")
    op.add_argument("--trigger", default="pr_opened"); op.add_argument("--model")
    op.add_argument("--retry", type=int, default=0)

    cap = sub.add_parser("capture"); cap.set_defaults(func=cmd_capture)
    cap.add_argument("run_id"); cap.add_argument("--from-file"); cap.add_argument("--url")

    so = sub.add_parser("set-outcome"); so.set_defaults(func=cmd_set_outcome)
    so.add_argument("run_id"); so.add_argument("outcome",
                    choices=["completed", "quota_stop", "error", "unattempted", "pending"])

    af = sub.add_parser("add-finding"); af.set_defaults(func=cmd_add_finding)
    af.add_argument("run_id"); af.add_argument("text"); af.add_argument("--locator")

    ge = sub.add_parser("grade-export"); ge.set_defaults(func=cmd_grade_export); ge.add_argument("file")
    gi = sub.add_parser("grade-import"); gi.set_defaults(func=cmd_grade_import)
    gi.add_argument("file"); gi.add_argument("--grader", default="jitendar")
    gi.add_argument("--second-reader")

    sub.add_parser("coverage").set_defaults(func=cmd_coverage)
    rp = sub.add_parser("report"); rp.set_defaults(func=cmd_report); rp.add_argument("--out")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
