from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class CaptureResult:
    raw_review: Optional[str]
    review_url: Optional[str]
    outcome: str
    model: Optional[str] = None
    note: str = ""


class Provider:
    kind = "base"

    def __init__(self, name, bot_login=None, **settings):
        self.name = name
        self.bot_login = bot_login
        self.settings = settings

    def capture(self, run_row) -> CaptureResult:
        raise NotImplementedError
