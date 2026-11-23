from .base import Provider
from .github_bot import GithubBotProvider
from .manual import ManualProvider

__all__ = ["Provider", "GithubBotProvider", "ManualProvider", "for_kind"]


def for_kind(kind):
    return {
        "github_bot": GithubBotProvider,
        "manual": ManualProvider,
    }[kind]
