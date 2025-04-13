from typing import Any, Optional, AsyncIterator, Callable
import asyncio
from functools import partial
from loguru import logger
from port_ocean.context.ocean import ocean
from port_ocean.utils.async_iterators import semaphore_async_iterator, stream_async_iterators_tasks
from urllib.parse import quote
from tenacity import retry, stop_after_attempt, wait_exponential
import aiohttp
import json


class GitHubClient:
    DEFAULT_PAGE_SIZE = 100
    DEFAULT_PARAMS = {"per_page": 100}

    def __init__(
        self, base_url: str, token: str, organization: str = "", api_version: str = "v3"
    ) -> None:
        """
        Initializes the GitHubClient with the base URL, token, organization, and API version.
        """
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.organization = organization
        self.api_version = api_version
        self.owner_type = None  # Initialize owner_type
        self._headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": f"application/vnd.github.{self.api_version}+json",
            "Content-Type": "application/json",
        }
        self._session: Optional[aiohttp.ClientSession] = None

    async def initialize(self) -> None:
        """
        Initializes the aiohttp session. Must be called in an async context.
        """
        self._session = aiohttp.ClientSession()

    async def close(self) -> None:
        """
        Closes the aiohttp session.
        """
        if self._session:
            await self._session.close()

    async def send_api_request(
        self,
        method: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Sends an HTTP request to the GitHub API and logs the request and response.
        """
        if not self._session:
            raise RuntimeError("Client session is not initialized. Call `initialize()` first.")
        
        url = f"{self.base_url}/{path}"
        logger.info(f"Sending {method} request to {url} with params: {params} and data: {data}")
        
        async with self._session.request(method, url, headers=self._headers, params=params, json=data) as response:
            response_text = await response.text()
            logger.info(f"Response from {url}: {response.status} - {response_text}")
            
            response.raise_for_status()  # Raise an exception for HTTP errors
            return json.loads(response_text)

    async def determine_owner_type(self) -> str:
        """
        Determines whether the organization is a user or an organization.
        """
        if self.owner_type:
            return self.owner_type

        if not self.organization:
            raise ValueError("Organization is missing or empty when determining owner type.")

        logger.info(f"Determining owner type for: {self.organization}")
        response = await self.send_api_request("GET", f"users/{self.organization}")
        self.owner_type = response.get("type", "User")  # Default to "User" if type is not found
        return self.owner_type

    async def get_repositories(self, include_languages: bool = False) -> AsyncIterator[list[dict[str, Any]]]:
        """
        Retrieves repositories for the user or organization based on the owner type.
        """
        user_type = await self.determine_owner_type()

        if user_type == "Organization":
            path = f"orgs/{self.organization}/repos"
        else:
            path = f"users/{self.organization}/repos"

        params = self.DEFAULT_PARAMS.copy()
        if include_languages:
            params["include_languages"] = "true"

        # Use the paginated request method
        async for batch in self._make_paginated_request(path, params=params):
            yield batch

    async def get_teams(self) -> AsyncIterator[list[dict[str, Any]]]:
        """
        Retrieves teams for the organization. Only valid for organizations.
        """
        user_type = await self.determine_owner_type()

        if user_type != "Organization":
            logger.info("Skipping team retrieval as the owner is not an organization.")
            return

        path = f"orgs/{self.organization}/teams"
        async for batch in self._make_paginated_request(path):
            yield batch

    async def get_pull_requests(self, repo: str) -> AsyncIterator[list[dict[str, Any]]]:
        """
        Retrieves pull requests for a repository.
        """
        path = f"repos/{self.organization}/{repo}/pulls"

        # Use the paginated request method
        async for batch in self._make_paginated_request(path, params=self.DEFAULT_PARAMS):
            yield batch

    async def get_issues(self, repo: str) -> AsyncIterator[list[dict[str, Any]]]:
        """
        Retrieves issues for a repository.
        """
        path = f"repos/{self.organization}/{repo}/issues"

        # Use the paginated request method
        async for batch in self._make_paginated_request(path, params=self.DEFAULT_PARAMS):
            yield batch

    async def get_workflows(self, repo: str) -> AsyncIterator[list[dict[str, Any]]]:
        """
        Retrieves workflows for a repository.
        """
        path = f"repos/{self.organization}/{repo}/actions/workflows"

        # Use the paginated request method
        async for batch in self._make_paginated_request(path, params=self.DEFAULT_PARAMS):
            yield batch

    async def _make_paginated_request(
        self,
        path: str,
        params: Optional[dict[str, Any]] = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> AsyncIterator[list[dict[str, Any]]]:
        """
        Handles paginated requests to the GitHub API and yields results in batches.
        """
        page = 1
        params_dict: dict[str, Any] = params or {}

        while True:
            request_params = {**params_dict, "per_page": page_size, "page": page}
            logger.debug(f"Fetching page {page} from {path}")

            response = await self.send_api_request("GET", path, params=request_params)

            # GitHub API returns a list directly, or empty dict for 404
            batch: list[dict[str, Any]] = response if isinstance(response, list) else []

            if not batch:
                break

            yield batch

            if len(batch) < page_size:
                logger.debug(f"Last page reached for {path}, no more data.")
                break

            page += 1


# Factory function to create and initialize the GitHubClient
_github_client: Optional[GitHubClient] = None


async def create_github_client() -> GitHubClient:
    """
    Factory function to create and return a singleton instance of GitHubClient.
    """
    global _github_client
    if _github_client is not None:
        return _github_client

    integration_config = ocean.integration_config
    base_url = integration_config.get("baseUrl", "https://api.github.com").rstrip("/")
    token = integration_config.get("token", "")
    organization = integration_config.get("organization", "").strip()  # Fetch and clean organization

    if not organization:
        raise ValueError("The 'organization' configuration is missing or empty. Please set it in the .env file.")

    _github_client = GitHubClient(base_url, token, organization)
    await _github_client.initialize()
    return _github_client