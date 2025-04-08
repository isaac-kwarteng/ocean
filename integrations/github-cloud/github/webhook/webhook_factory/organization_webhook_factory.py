from typing import Any, Optional

from loguru import logger

from github.clients.github_client import GitHubClient
from github.webhook.events import OrganizationEvents


class OrganizationWebHook:
    def __init__(self, client: GitHubClient, base_url: str) -> None:
        self.client = client
        self.base_url = base_url
        self.events = OrganizationEvents()

    async def create_webhooks_for_organization(self) -> None:
        """Create webhooks for the organization."""
        logger.info("Creating webhooks for organization")
        webhook_config = {
            "url": f"{self.base_url}/hook/{{organization_id}}",
            "content_type": "json",
            "secret": "{{webhook_secret}}",
            "events": self.events.to_dict(),
        }
        await self.client.rest.send_api_request(
            "POST", "orgs/{{organization}}/hooks", data=webhook_config
        ) 