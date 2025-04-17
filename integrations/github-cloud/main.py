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
        result = func(*args)
        if hasattr(result, "__aiter__"):
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

        logger.success(f"Completed repository sync for {total_repos} repositories")
    except Exception as e:
        logger.error(f"Repository sync failed: {e}")
        yield []


@ocean.on_resync(ObjectKind.TEAM)
async def on_resync_teams(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    client = get_github_client()
    try:
        total_teams = 0

        async for batch in client.get_teams_with_repos():
            logger.debug(f"Team with repos data sample: {batch[0]}")

            processed_count = len(batch)
            total_teams += processed_count
            logger.info(
                f"Processing {processed_count} teams with repositories (Total: {total_teams})"
            )

            yield batch

        logger.success(f"Completed team sync for {total_teams} teams with repository relationships")
    except Exception as e:
        logger.error(f"Team sync failed: {e}")
        yield []


@ocean.on_resync(ObjectKind.ISSUE)
async def on_resync_issues(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    client = get_github_client()
    try:
        total_issues = 0
        repo_count = 0

        async for repos_batch in client.get_repositories():
            repo_count += len(repos_batch)
            logger.info(
                f"Checking {len(repos_batch)} repositories for issues (Total repos: {repo_count})"
            )

            for repo in repos_batch:
                repo_name = repo["name"]
                async for issues_batch in client.get_issues(repo_name):
                    # Enrich issues with repository context
                    enriched_issues = []
                    for issue in issues_batch:
                        issue.update(
                            {
                                "repository": repo_name,
                                "repository_full_name": repo["full_name"],
                                "is_issue": True,  # Explicit marker
                            }
                        )
                        enriched_issues.append(issue)

                    if enriched_issues:
                        total_issues += len(enriched_issues)
                        logger.debug(f"Found {len(enriched_issues)} issues in {repo_name}")
                        yield enriched_issues

        logger.success(f"Synced {total_issues} issues from {repo_count} repositories")
    except Exception as e:
        logger.error(f"Issue sync failed: {str(e)}")
        yield []


@ocean.on_resync(ObjectKind.PULL_REQUEST)
async def on_resync_pull_requests(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    client = get_github_client()
    try:
        total_prs = 0
        repo_count = 0

        async for repos_batch in client.get_repositories():
            repo_count += len(repos_batch)
            logger.info(f"Processing {len(repos_batch)} repositories (Total: {repo_count})")

            for repo in repos_batch:
                repo_name = repo["name"]
                logger.debug(f"Checking PRs for repository: {repo_name}")

                async for prs_batch in process_with_concurrency(
                    client.get_pull_requests, repo_name
                ):
                    if prs_batch:
                        total_prs += len(prs_batch)
                        logger.debug(f"Found {len(prs_batch)} PRs in {repo_name}")
                        yield prs_batch

        logger.info(f"Total PRs found: {total_prs} from {repo_count} repositories")
    except Exception as e:
        logger.error(f"PR sync failed: {e}")
        yield []


@ocean.on_resync(ObjectKind.WORKFLOW)
async def on_resync_workflows(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    client = get_github_client()
    try:
        async for repos_batch in client.get_repositories():
            for repo in repos_batch:
                repo_name = repo["name"]
                async for workflows_batch in client.get_workflows(repo_name):
                    # Enrich with repository context
                    for workflow in workflows_batch:
                        workflow["repository"] = repo_name
                    yield workflows_batch
    except Exception as e:
        logger.error(f"Workflow sync failed: {e}")
        yield []
