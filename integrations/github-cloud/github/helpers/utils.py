from enum import StrEnum
from typing import List


class ObjectKind(StrEnum):
    REPOSITORY = "repository"
    TEAM = "team"
    ISSUE = "issue"
    PULL_REQUEST = "pull_request"
    WORKFLOW = "workflow"

    @classmethod
    def available_kinds(cls) -> List[str]:
        """Return a list of all available object kinds."""
        return [kind.value for kind in cls] 