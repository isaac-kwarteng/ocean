from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod


class EventConfig(ABC):
    @abstractmethod
    def to_dict(self) -> dict[str, bool]:
        """Convert event configuration to a dictionary."""
        pass


@dataclass(frozen=True)
class OrganizationEvents(EventConfig):
    repository_events: bool = True
    pull_request_events: bool = True
    issue_events: bool = True
    team_events: bool = True
    workflow_events: bool = True

    def to_dict(self) -> dict[str, bool]:
        return asdict(self) 