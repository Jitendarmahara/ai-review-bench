"""Scoring buckets, fixed before any reviewer output is read."""

BUCKETS = {
    "correct_bug": "Correctly identifies a real defect in the change.",
    "false_warning": "Warns about a problem the code already handles, or that is not a real issue.",
    "needs_deploy_info": "Correctly states it needs deployment/runtime information to decide.",
    "valid_unanticipated": "A correct, useful finding that was not in the frozen answer key.",
    "noise": "Unactionable, off-topic, or stylistic comment with no bearing on correctness.",
}

OUTCOMES = {
    "pending": "Attempt created but review not yet captured.",
    "completed": "Reviewer returned a review we captured.",
    "quota_stop": "Reviewer refused/stopped due to quota, trial, or rate limit.",
    "error": "Reviewer errored or never finished.",
    "unattempted": "We did not run this provider-case.",
}

VALID_BUCKETS = set(BUCKETS)
VALID_OUTCOMES = set(OUTCOMES)


def validate_bucket(b):
    if b not in VALID_BUCKETS:
        raise ValueError(f"Unknown bucket {b!r}. Valid: {sorted(VALID_BUCKETS)}")


def validate_outcome(o):
    if o not in VALID_OUTCOMES:
        raise ValueError(f"Unknown outcome {o!r}. Valid: {sorted(VALID_OUTCOMES)}")
