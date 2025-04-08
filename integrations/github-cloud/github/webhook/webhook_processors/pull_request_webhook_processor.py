from typing import Any, Dict

from loguru import logger
from port_ocean.context.ocean import ocean


class PullRequestWebhookProcessor:
    async def process(self, payload: Dict[str, Any]) -> None:
        """Process pull request webhook events."""
        action = payload.get("action")
        if not action:
            return

        pull_request = payload.get("pull_request", {})
        if not pull_request:
            return

        logger.info(f"Processing pull request {action} event for #{pull_request.get('number')}")
        await ocean.resync(ObjectKind.PULL_REQUEST) 