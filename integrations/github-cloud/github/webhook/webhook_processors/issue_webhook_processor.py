from typing import Any, Dict

from loguru import logger
from port_ocean.context.ocean import ocean


class IssueWebhookProcessor:
    async def process(self, payload: Dict[str, Any]) -> None:
        """Process issue webhook events."""
        action = payload.get("action")
        if not action:
            return

        issue = payload.get("issue", {})
        if not issue:
            return

        logger.info(f"Processing issue {action} event for #{issue.get('number')}")
        await ocean.resync(ObjectKind.ISSUE) 