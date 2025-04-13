from typing import cast

from loguru import logger
from port_ocean.context.event import event
from port_ocean.context.ocean import ocean
from port_ocean.core.ocean_types import ASYNC_GENERATOR_RESYNC_TYPE
from port_ocean.clients.port.types import UserAgentType

from integration import RepositoryResourceConfig
from github.client import create_github_client
from github.helpers.utils import ObjectKind

# Initialize the GitHub client globally
github_client = None


@ocean.on_start()
async def on_start() -> None:
    """
    Initialize the GitHub client once during the application startup.
    """
    global github_client
    if github_client is None:
        github_client = await create_github_client()  # Initialize the client
        logger.info("GitHub client initialized successfully.")
    else:
        logger.info("GitHub client already initialized.")
    if ocean.event_listener_type == "ONCE":
        logger.info("Skipping webhook creation because the event listener is ONCE")
        return
    logger.info("Initial sync will be handled by the resync decorators")


@ocean.on_resync(ObjectKind.REPOSITORY)
async def on_resync_repositories(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    if github_client is None:
        raise RuntimeError("GitHub client is not initialized. Ensure `on_start` has been executed.")
    
    async for repositories_batch in github_client.get_repositories(include_languages=True):
        logger.info(f"Received repository batch with {len(repositories_batch)} repositories")
        yield repositories_batch


@ocean.on_resync(ObjectKind.TEAM)
async def on_resync_teams(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    if github_client is None:
        raise RuntimeError("GitHub client is not initialized. Ensure `on_start` has been executed.")
    
    async for teams_batch in github_client.get_teams():
        logger.info(f"Received team batch with {len(teams_batch)} teams")
        yield teams_batch


@ocean.on_resync(ObjectKind.ISSUE)
async def on_resync_issues(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    if github_client is None:
        raise RuntimeError("GitHub client is not initialized. Ensure `on_start` has been executed.")
    
    async for repositories_batch in github_client.get_repositories():
        for repo in repositories_batch:
            repo_name = repo["name"]
            async for issues_batch in github_client.get_issues(repo=repo_name):
                logger.info(f"Processing issues for repository: {repo_name}")
                yield issues_batch


@ocean.on_resync(ObjectKind.PULL_REQUEST)
async def on_resync_pull_requests(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    if github_client is None:
        raise RuntimeError("GitHub client is not initialized. Ensure `on_start` has been executed.")
    
    async for repositories_batch in github_client.get_repositories():
        for repo in repositories_batch:
            repo_name = repo["name"]
            async for pull_requests_batch in github_client.get_pull_requests(repo=repo_name):
                logger.info(f"Processing pull requests for repository: {repo_name}")
                yield pull_requests_batch


@ocean.on_resync(ObjectKind.WORKFLOW)
async def on_resync_workflows(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    if github_client is None:
        raise RuntimeError("GitHub client is not initialized. Ensure `on_start` has been executed.")
    
    async for repositories_batch in github_client.get_repositories():
        for repo in repositories_batch:
            repo_name = repo["name"]
            async for workflows_batch in github_client.get_workflows(repo=repo_name):
                logger.info(f"Processing workflows for repository: {repo_name}")
                yield workflows_batch