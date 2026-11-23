from __future__ import annotations

from .base import Provider, CaptureResult


class ManualProvider(Provider):
    kind = "manual"

    def capture(self, run_row) -> CaptureResult:
        return CaptureResult(
            None, None, "pending",
            note="Manual provider: paste the review with "
                 "`python -m benchmark capture <run_id> --from-file <path> [--url <permalink>]`.",
        )
