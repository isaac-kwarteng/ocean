from typing import Dict, List, Optional
from port_ocean.core.integrations.base import BaseIntegration
from port_ocean.core.models import Entity
from port_ocean.core.types import RawEntity
from port_ocean.core.handlers.port_app_config.models import ResourceConfig

from .client.github_client import GitHubClient
from .webhook_processor.webhook_processor import GitHubWebhookProcessor

class GitHubCloudIntegration(BaseIntegration):
    def __init__(self):
        super().__init__()
        self.github_client = GitHubClient()
        self.webhook_processor = GitHubWebhookProcessor()

    async def initialize(self, context: Dict) -> None:
        """Initialize the integration with GitHub Cloud."""
        await self.github_client.initialize(context)

    async def get_resources(self, resource_config: ResourceConfig) -> List[RawEntity]:
        """Fetch resources from GitHub based on the resource type."""
        resource_type = resource_config.resource_type
        
        if resource_type == "repository":
            return await self.github_client.get_repositories()
        elif resource_type == "branch":
            return await self.github_client.get_branches()
        elif resource_type == "pull_request":
            return await self.github_client.get_pull_requests()
        elif resource_type == "issue":
            return await self.github_client.get_issues()
        else:
            raise ValueError(f"Unsupported resource type: {resource_type}")

    async def get_resource_mappings(self, resource_config: ResourceConfig) -> Dict[str, Entity]:
        """Get resource mappings for the specified resource type."""
        resources = await self.get_resources(resource_config)
        return {
            resource["id"]: Entity(
                identifier=resource["id"],
                title=resource.get("name", ""),
                blueprint=resource_config.resource_type,
                properties=resource.get("properties", {}),
                relations=resource.get("relations", {}),
            )
            for resource in resources
        }

    async def process_webhook(self, payload: Dict) -> None:
        """Process incoming webhooks from GitHub."""
        await self.webhook_processor.process(payload) 