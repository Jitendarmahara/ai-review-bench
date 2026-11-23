"""Optional Greptile API route. The github_bot route covers Greptile once installed;
this is a stub for an API-driven comparison condition. Fill in capture() with your key."""
from __future__ import annotations

import json
import os
import urllib.request

from .base import Provider, CaptureResult

GREPTILE_API = os.environ.get("GREPTILE_API", "https://api.greptile.com/v2")


class GreptileApiProvider(Provider):
    kind = "api"

    def capture(self, run_row) -> CaptureResult:
        key = os.environ.get("GREPTILE_API_KEY")
        gh_token = os.environ.get("GITHUB_TOKEN")
        if not key or not gh_token:
            return CaptureResult(None, None, "unattempted",
                                 note="Set GREPTILE_API_KEY and GITHUB_TOKEN, or use the github_bot route.")
        return CaptureResult(None, None, "pending",
                             note="Greptile API capture not implemented; use github_bot route.")


def _post(url, payload, headers):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())
