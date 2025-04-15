from typing import Literal
from pydantic import Field
from port_ocean.core.handlers.port_app_config import APIPortAppConfig
from port_ocean.core.handlers.port_app_config.models import (
    ResourceConfig,
    Selector,
    PortAppConfig,
)
from port_ocean.core.integrations.base import BaseIntegration


class RepositorySelector(Selector):
    include_languages: bool = Field(
        alias="includeLanguages",
        default=False,
        description="Include programming language data for repositories",
    )


class RepositoryResourceConfig(ResourceConfig):
    kind: Literal["repository"]
    selector: RepositorySelector


class PullRequestResourceConfig(ResourceConfig):
    kind: Literal["pull-request"]
    selector: Selector


class IssueResourceConfig(ResourceConfig):
    kind: Literal["issue"]
    selector: Selector


class TeamResourceConfig(ResourceConfig):
    kind: Literal["team"]
    selector: Selector


class WorkflowResourceConfig(ResourceConfig):
    kind: Literal["workflow"]
    selector: Selector


class GitHubPortAppConfig(PortAppConfig):
    resources: list[
        RepositoryResourceConfig
        | PullRequestResourceConfig
        | IssueResourceConfig
        | TeamResourceConfig
        | WorkflowResourceConfig
    ] = Field(default_factory=list)


class GitHubIntegration(BaseIntegration):
    class AppConfigHandlerClass(APIPortAppConfig):
        CONFIG_CLASS = GitHubPortAppConfig

        def __init__(self, ocean_integration: "BaseIntegration"):
            super().__init__(ocean_integration)
