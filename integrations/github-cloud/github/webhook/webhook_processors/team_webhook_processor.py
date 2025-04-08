from typing import Any, Dict

from loguru import logger
from port_ocean.context.ocean import ocean


class TeamWebhookProcessor:
    async def process(self, payload: Dict[str, Any]) -> None:
        """Process team webhook events."""
        action = payload.get("action")
        if not action:
            return

        team = payload.get("team", {})
        if not team:
            return

        logger.info(f"Processing team {action} event for {team.get('name')}")
        await ocean.resync(ObjectKind.TEAM) 