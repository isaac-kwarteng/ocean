from typing import Any, Optional

from loguru import logger
from port_ocean.context.ocean import ocean

from github.client import GitHubClient
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
            "url": f"{self.base_url}/integration/webhook",
            "content_type": "json",
            "secret": ocean.integration_config.get("webhook_secret", ""),
            "events": self.events.to_dict(),
        }
        
        try:
            await self.client.send_api_request(
                "POST", 
                f"orgs/{self.client.organization}/hooks", 
                data=webhook_config
            )
            logger.info("Successfully created webhook for organization")
        except Exception as e:
            logger.error(f"Failed to create webhook: {str(e)}")
            raise 