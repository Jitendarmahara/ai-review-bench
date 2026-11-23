from __future__ import annotations

from .base import Provider, CaptureResult
from .. import github


class GithubBotProvider(Provider):
    kind = "github_bot"

    def capture(self, run_row) -> CaptureResult:
        repo = run_row["repo"]
        pr = run_row["pr_number"]
        if not repo or not pr:
            return CaptureResult(None, None, "unattempted", note="No repo/PR recorded; open the PR first.")
        if not self.bot_login:
            return CaptureResult(None, None, "error",
                                 note=f"No bot_login set for provider {self.name}.")
        try:
            review = github.first_review_from(repo, int(pr), self.bot_login)
        except github.GhError as e:
            return CaptureResult(None, None, "error", note=str(e))

        if review is None:
            return CaptureResult(None, None, "pending",
                                 note="No review from this bot yet. Re-run capture later, "
                                      "or set quota_stop/error/unattempted by hand.")
        return CaptureResult(
            raw_review=review["body"],
            review_url=review["url"],
            outcome="completed",
            note=f"authored by {review['author']} at {review['created_at']}",
        )
