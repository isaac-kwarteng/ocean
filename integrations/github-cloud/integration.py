from typing import Literal

from port_ocean.core.handlers import APIPortAppConfig
from port_ocean.core.handlers.port_app_config.models import (
    PortAppConfig,
    ResourceConfig,
    Selector,
)
from port_ocean.core.integrations.base import BaseIntegration
from pydantic import Field


class RepositorySelector(Selector):
    include_languages: bool = Field(
        alias="includeLanguages",
        default=False,
        description="Whether to include the languages of the repository, defaults to false",
    )


class RepositoryResourceConfig(ResourceConfig):
    kind: Literal["repository"]
    selector: RepositorySelector


class PullRequestResourceConfig(ResourceConfig):
    kind: Literal["pull_request"]
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
        | ResourceConfig
    ] = Field(
        default_factory=list
    )


class GitHubIntegration(BaseIntegration):
    class AppConfigHandlerClass(APIPortAppConfig):
        CONFIG_CLASS = GitHubPortAppConfig 