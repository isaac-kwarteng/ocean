from typing import cast

from loguru import logger
from port_ocean.context.event import event
from port_ocean.context.ocean import ocean
from port_ocean.core.ocean_types import ASYNC_GENERATOR_RESYNC_TYPE
from port_ocean.clients.port.types import UserAgentType

from integration import RepositoryResourceConfig
from github.clients.client_factory import create_github_client
from github.helpers.utils import ObjectKind

# Commenting out webhook imports and processors to focus on data synchronization
# from github.webhook.webhook_processors.repository_webhook_processor import (
#     RepositoryWebhookProcessor,
# )
# from github.webhook.webhook_processors.pull_request_webhook_processor import (
#     PullRequestWebhookProcessor,
# )
# from github.webhook.webhook_processors.issue_webhook_processor import (
#     IssueWebhookProcessor,
# )
# from github.webhook.webhook_processors.team_webhook_processor import (
#     TeamWebhookProcessor,
# )
# from github.webhook.webhook_processors.workflow_webhook_processor import (
#     WorkflowWebhookProcessor,
# )
# from github.webhook.webhook_factory.organization_webhook_factory import OrganizationWebHook


@ocean.on_start()
async def on_start() -> None:
    logger.info("Starting Port Ocean GitHub Cloud Integration")
    # Disabling webhook creation to focus on data synchronization
    if ocean.event_listener_type == "ONCE":
        logger.info("Skipping webhook creation because the event listener is ONCE")
        return

    # if base_url := ocean.app.base_url:
    #     logger.info(f"Creating webhooks for organization at {base_url}")
    #     client = create_github_client()
    #     webhook_factory = OrganizationWebHook(client, base_url)
    #     await webhook_factory.create_webhooks_for_organization()
    
    # The resync functionality is handled by the @ocean.on_resync decorators below
    logger.info("Initial sync will be handled by the resync decorators")


@ocean.on_resync(ObjectKind.REPOSITORY)
async def on_resync_repositories(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    client = create_github_client()

    selector = cast(RepositoryResourceConfig, event.resource_config).selector

    include_languages = bool(selector.include_languages)

    async for repositories_batch in client.get_repositories(
        include_languages=include_languages
    ):
        logger.info(f"Received repository batch with {len(repositories_batch)} repositories")
        yield repositories_batch


@ocean.on_resync(ObjectKind.TEAM)
async def on_resync_teams(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    client = create_github_client()

    async for teams_batch in client.get_teams():
        logger.info(f"Received team batch with {len(teams_batch)} teams")
        yield teams_batch


@ocean.on_resync(ObjectKind.ISSUE)
async def on_resync_issues(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    client = create_github_client()

    async for repositories_batch in client.get_repositories():
        logger.info(f"Processing batch of {len(repositories_batch)} repositories for issues")
        async for issues_batch in client.get_repository_resource(repositories_batch, "issues"):
            yield issues_batch


@ocean.on_resync(ObjectKind.PULL_REQUEST)
async def on_resync_pull_requests(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    client = create_github_client()

    async for repositories_batch in client.get_repositories():
        logger.info(
            f"Processing batch of {len(repositories_batch)} repositories for pull requests"
        )
        async for pull_requests_batch in client.get_repository_resource(
            repositories_batch, "pulls"
        ):
            yield pull_requests_batch


@ocean.on_resync(ObjectKind.WORKFLOW)
async def on_resync_workflows(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    client = create_github_client()

    async for repositories_batch in client.get_repositories():
        logger.info(
            f"Processing batch of {len(repositories_batch)} repositories for workflows"
        )
        async for workflows_batch in client.get_repository_resource(
            repositories_batch, "actions/workflows"
        ):
            yield workflows_batch

# Commenting out webhook processor registrations to fix the error
# ocean.add_webhook_processor("/hook/{organization_id}", RepositoryWebhookProcessor)
# ocean.add_webhook_processor("/hook/{organization_id}", PullRequestWebhookProcessor)
# ocean.add_webhook_processor("/hook/{organization_id}", IssueWebhookProcessor)
# ocean.add_webhook_processor("/hook/{organization_id}", TeamWebhookProcessor)
# ocean.add_webhook_processor("/hook/{organization_id}", WorkflowWebhookProcessor) 