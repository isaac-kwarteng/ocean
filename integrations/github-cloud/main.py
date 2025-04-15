from typing import cast, AsyncIterator, Any
from loguru import logger
from asyncio import Semaphore
from port_ocean.context.event import event
from port_ocean.context.ocean import ocean
from port_ocean.core.ocean_types import ASYNC_GENERATOR_RESYNC_TYPE

from integration import RepositoryResourceConfig
from client import create_github_client
from helpers.utils import ObjectKind

# Global client instance and concurrency control
_CLIENT = None
CONCURRENCY_LIMIT = 5  
semaphore = Semaphore(CONCURRENCY_LIMIT)


def get_github_client():
    """Singleton pattern for GitHub client"""
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = create_github_client()
    return _CLIENT


@ocean.on_start()
async def on_start() -> None:
    logger.info("Starting GitHub integration")
    if ocean.event_listener_type == "ONCE":
        logger.info("Skipping webhook setup for ONCE listener")

    # Initialize client at startup to validate credentials early
    try:
        client = get_github_client()
        owner_type = await client.determine_owner_type(client.org)
        logger.info(f"Connected to GitHub as {owner_type}: {client.org}")
    except Exception as e:
        logger.error(f"Failed to initialize GitHub client: {e}")
        raise


async def process_with_concurrency(func, *args) -> AsyncIterator[Any]:
    """Helper to manage concurrency limits and properly handle async generators"""
    async with semaphore:
        result = await func(*args)
        if hasattr(result, '__aiter__'):
            async for item in result:
                yield item
        else:
            yield result


@ocean.on_resync(ObjectKind.REPOSITORY)
async def on_resync_repositories(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    client = get_github_client()
    selector = cast(RepositoryResourceConfig, event.resource_config).selector

    try:
        total_repos = 0

        async for batch in client.get_repositories(include_languages=selector.include_languages):
            processed_count = len(batch)
            total_repos += processed_count
            logger.info(f"Processing {processed_count} repositories (Total: {total_repos})")
            yield batch

        logger.success(
            f"Completed repository sync for {total_repos} repositories"
        )
    except Exception as e:
        logger.error(f"Repository sync failed: {e}")
        yield []


@ocean.on_resync(ObjectKind.TEAM)
async def on_resync_teams(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    client = get_github_client()
    try:
        total_teams = 0

        async for batch in client.get_teams():
            processed_count = len(batch)
            total_teams += processed_count
            logger.info(f"Processing {processed_count} teams (Total: {total_teams})")
            yield batch

        if total_teams > 0:
            logger.success(
                f"Completed team sync for {total_teams} teams"
            )
        else:
            logger.warning("No teams found or organization not accessible")
    except Exception as e:
        logger.error(f"Team sync failed: {e}")
        yield []


async def _process_repository_resources(client, repo, resource_type) -> AsyncIterator[Any]:
    """Helper to process resources for a single repository"""
    try:
        if resource_type == "issues":
            async for issue in client.get_issues(repo["name"]):
                yield issue
        elif resource_type == "pulls":
            async for pr in client.get_pull_requests(repo["name"]):
                yield pr
        elif resource_type == "workflows":
            async for workflow in client.get_workflows(repo["name"]):
                yield workflow
    except Exception as e:
        logger.warning(f"Skipping {resource_type} for {repo['name']}: {e}")
        yield []


@ocean.on_resync(ObjectKind.ISSUE)
async def on_resync_issues(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    client = get_github_client()
    try:
        total_issues = 0
        repo_count = 0

        async for repos_batch in client.get_repositories():
            for repo in repos_batch:
                repo_count += 1
                async for issues_batch in process_with_concurrency(
                    _process_repository_resources, client, repo, "issues"
                ):
                    if issues_batch:
                        total_issues += 1
                        yield [issues_batch]

        logger.success(
            f"Synced {total_issues} issues from {repo_count} repositories"
        )
    except Exception as e:
        logger.error(f"Issue sync failed: {e}")
        yield []


@ocean.on_resync(ObjectKind.PULL_REQUEST)
async def on_resync_pull_requests(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    client = get_github_client()
    try:
        total_prs = 0
        repo_count = 0

        async for repos_batch in client.get_repositories():
            for repo in repos_batch:
                repo_count += 1
                async for prs_batch in process_with_concurrency(
                    _process_repository_resources, client, repo, "pulls"
                ):
                    if prs_batch:
                        total_prs += 1
                        yield [prs_batch]

        logger.success(
            f"Synced {total_prs} PRs from {repo_count} repositories"
        )
    except Exception as e:
        logger.error(f"PR sync failed: {e}")
        yield []


@ocean.on_resync(ObjectKind.WORKFLOW)
async def on_resync_workflows(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    client = get_github_client()
    try:
        total_workflows = 0
        repo_count = 0

        async for repos_batch in client.get_repositories():
            for repo in repos_batch:
                repo_count += 1
                async for workflows_batch in process_with_concurrency(
                    _process_repository_resources, client, repo, "workflows"
                ):
                    if workflows_batch:
                        total_workflows += 1
                        yield [workflows_batch]

        logger.success(
            f"Synced {total_workflows} workflows from {repo_count} repositories"
        )
    except Exception as e:
        logger.error(f"Workflow sync failed: {e}")
        yield []