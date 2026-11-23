"""Cases, conditions, and the seed provider list. Ground truth lives in the DB, not here."""

CASES = {
    "01": {"title": "Page report history by scheduled time", "has_snapshot": False},
    "02": {"title": "Stream the report export",              "has_snapshot": False},
    "03": {"title": "Batch queued deliveries",               "has_snapshot": False},
    "04": {"title": "Retire the legacy delivery column",     "has_snapshot": True},
    "05": {"title": "Increase export batch size",            "has_snapshot": True},
    "06": {"title": "Use the new delivery queue",            "has_snapshot": True},
    "07": {"title": "Index pending deliveries",              "has_snapshot": False},
    "08": {"title": "Include a total in the activity summary","has_snapshot": False},
}

CONDITIONS = ("code_only", "with_snapshot")


def conditions_for(case_id):
    c = CASES[case_id]
    return ("code_only", "with_snapshot") if c["has_snapshot"] else ("code_only",)


def all_cells():
    for cid in CASES:
        for cond in conditions_for(cid):
            yield cid, cond


# bot_login is the GitHub account that authors the review; verify it against a real review.
SEED_PROVIDERS = [
    ("proofline",  "github_bot", "proofline[bot]",     "Host app. Free month of hosted review."),
    ("coderabbit", "github_bot", "coderabbitai[bot]",  "Free trial. Confirm private-PR coverage."),
    ("greptile",   "github_bot", "greptile-apps[bot]", "Free Starter credits. Confirm private-PR coverage."),
]

BASE_BRANCH = "pilot/base"


def pilot_branch(case_id):
    return f"pilot/{case_id}"
