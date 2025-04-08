from enum import StrEnum


class ObjectKind(StrEnum):
    REPOSITORY = "repository"
    TEAM = "team"
    ISSUE = "issue"
    PULL_REQUEST = "pull_request"
    WORKFLOW = "workflow" 