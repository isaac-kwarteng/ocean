from typing import Any, Dict

from loguru import logger
from port_ocean.context.ocean import ocean


class WorkflowWebhookProcessor:
    async def process(self, payload: Dict[str, Any]) -> None:
        """Process workflow webhook events."""
        action = payload.get("action")
        if not action:
            return

        workflow = payload.get("workflow", {})
        if not workflow:
            return

        logger.info(f"Processing workflow {action} event for {workflow.get('name')}")
        await ocean.resync(ObjectKind.WORKFLOW) 