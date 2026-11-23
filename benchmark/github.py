"""GitHub operations via the `gh` CLI."""
from __future__ import annotations

import json
import subprocess
from typing import Optional


class GhError(RuntimeError):
    pass


def _gh(*args, check=True):
    try:
        out = subprocess.run(["gh", *args], capture_output=True, text=True, check=check)
    except FileNotFoundError:
        raise GhError("`gh` CLI not found. Install GitHub CLI and run `gh auth login`.")
    if check and out.returncode != 0:
        raise GhError(f"gh {' '.join(args)} failed:\n{out.stderr.strip()}")
    return out.stdout.strip()


def api(path, *extra):
    raw = _gh("api", path, *extra)
    return json.loads(raw) if raw else {}


def create_private_repo(full_name, description=""):
    try:
        _gh("repo", "create", full_name, "--private", "--description",
            description or "AI review benchmark run repo")
    except GhError as e:
        if "already exists" not in str(e).lower():
            raise


def open_pr(repo, base, head, title, body=""):
    out = _gh("pr", "create", "--repo", repo, "--base", base, "--head", head,
              "--title", title, "--body", body or title)
    return int(out.rstrip("/").split("/")[-1])


def head_sha(repo, branch):
    data = api(f"repos/{repo}/commits/{branch}")
    return data.get("sha", "") if isinstance(data, dict) else ""


def first_review_from(repo, pr_number, bot_login) -> Optional[dict]:
    candidates = []

    reviews = api(f"repos/{repo}/pulls/{pr_number}/reviews")
    for r in reviews if isinstance(reviews, list) else []:
        if (r.get("user") or {}).get("login") == bot_login and r.get("body"):
            candidates.append(_norm(r, r.get("submitted_at")))

    issue_comments = api(f"repos/{repo}/issues/{pr_number}/comments")
    for c in issue_comments if isinstance(issue_comments, list) else []:
        if (c.get("user") or {}).get("login") == bot_login:
            candidates.append(_norm(c, c.get("created_at")))

    review_comments = api(f"repos/{repo}/pulls/{pr_number}/comments")
    for c in review_comments if isinstance(review_comments, list) else []:
        if (c.get("user") or {}).get("login") == bot_login:
            candidates.append(_norm(c, c.get("created_at")))

    if not candidates:
        return None
    candidates.sort(key=lambda x: x["created_at"] or "")
    return candidates[0]


def _norm(obj, ts):
    return {
        "body": obj.get("body") or "",
        "url": obj.get("html_url") or "",
        "created_at": ts or "",
        "author": (obj.get("user") or {}).get("login", ""),
    }


def whoami():
    return _gh("api", "user", "--jq", ".login")
