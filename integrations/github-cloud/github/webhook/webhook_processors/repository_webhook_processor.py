from typing import Any, Dict

from loguru import logger
from port_ocean.context.ocean import ocean
from port_ocean.core.handlers.webhook.abstract_webhook_processor import AbstractWebhookProcessor
from github.helpers.utils import ObjectKind


class RepositoryWebhookProcessor(AbstractWebhookProcessor):
    async def process(self, payload: Dict[str, Any]) -> None:
        """Process repository webhook events."""
        action = payload.get("action")
        if not action:
            return

        repository = payload.get("repository", {})
        if not repository:
            return

        logger.info(f"Processing repository {action} event for {repository.get('full_name')}")
        await ocean.resync(ObjectKind.REPOSITORY) 