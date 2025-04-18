from typing import Any, AsyncIterator, Callable, Optional, Dict, List
import asyncio
from urllib.parse import quote
import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from port_ocean.utils import http_async_client
from port_ocean.context.ocean import ocean


class GitHubClient:
    DEFAULT_PARAMS = {"per_page": 100}
    DEFAULT_PAGE_SIZE = 100
    VALID_REPOSITORY_RESOURCES = ["issues", "pulls", "actions/workflows"]

    def __init__(self, base_url: str, token: str) -> None:
        self.token = token
        self._client = http_async_client
        self._headers = self._get_headers()
        self.base_url = base_url
        self.org = ""
        self.username = ""  # For user accounts
        self.owner_type = None
        logger.info(f"Initialized GitHubClient for {base_url}")

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }

    async def get_owner_endpoint(self, resource_path: str) -> str:
        """Returns the proper endpoint based on owner type"""
        if not self.org:
            raise ValueError("No owner/organization configured")

        if self.owner_type == "Organization":
            return f"orgs/{self.org}/{resource_path}"
        else:
            return f"users/{self.username}/{resource_path}"

    async def get_repo_endpoint(self, repo: str, resource_path: str) -> str:
        """Returns the proper repository endpoint based on owner type"""
        if not self.org:
            raise ValueError("No owner/organization configured")

        owner = self.org if self.owner_type == "Organization" else self.username
        return f"repos/{owner}/{repo}/{resource_path}"

    async def send_api_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/{path}"
        logger.debug(f"Request: {method} {url}")

        try:
            response = await self._client.request(
                method=method,
                url=url,
                headers=self._headers,
                params=params,
                json=data,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"API request failed: {e.response.status_code} {method} {url}")
            if e.response.status_code == 404:
                return {}
            raise
        except httpx.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            raise

    async def determine_owner_type(self, owner: str) -> str:
        if self.owner_type:
            return self.owner_type

        try:
            response = await self.send_api_request("GET", f"users/{owner}")
            self.owner_type = response.get("type", "User")
            if self.owner_type == "User":
                self.username = owner  # Store username for user accounts
            return self.owner_type
        except Exception as e:
            logger.error(f"Error determining owner type: {e}")
            self.owner_type = "User"
            self.username = owner
            return self.owner_type

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _make_paginated_request(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        page = 1
        params_dict = params or {}

        while True:
            request_params = {**params_dict, "per_page": page_size, "page": page}
            response = await self.send_api_request("GET", path, request_params)

            batch = response if isinstance(response, list) else []
            if not batch:
                break

            yield batch
            if len(batch) < page_size:
                break
            page += 1

    async def get_paginated_resource(
        self, resource_type: str, params: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        async for batch in self._make_paginated_request(resource_type, params):
            yield batch

    async def get_repositories(
        self, include_languages: bool = False, params: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        if not self.org:
            raise ValueError("No owner/organization configured")

        owner_type = await self.determine_owner_type(self.org)
        path = (
            f"orgs/{self.org}/repos"
            if owner_type == "Organization"
            else f"users/{self.username}/repos"
        )

        async for batch in self.get_paginated_resource(path, params):
            if include_languages:
                batch = await self._enrich_batch(batch, self._enrich_repo_languages)
            yield batch

    async def _enrich_repo_languages(self, repo: Dict[str, Any]) -> Dict[str, Any]:
        try:
            languages = await self.send_api_request("GET", f"repos/{repo['full_name']}/languages")
            repo["languages"] = list(languages.keys())
        except Exception as e:
            logger.warning(f"Failed to get languages for {repo['full_name']}: {e}")
        return repo

    async def _enrich_batch(
        self,
        batch: List[Dict[str, Any]],
        enrich_func: Callable[[Dict[str, Any]], Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        return await asyncio.gather(*[enrich_func(item) for item in batch])

    async def get_teams(self) -> AsyncIterator[List[Dict[str, Any]]]:
        """Fetch all teams with full details including counts"""
        if not self.org:
            raise ValueError("Organization not configured")

        path = f"orgs/{self.org}/teams"
        async for team_batch in self._make_paginated_request(path):
            # Enrich each team with detailed counts
            enriched_teams = []
            for team in team_batch:
                detailed_team = await self._get_team_details(team["slug"])
                enriched_teams.append(detailed_team)
            yield enriched_teams

    async def _get_team_details(self, team_slug: str) -> Dict[str, Any]:
        """Get detailed team information including counts"""
        path = f"orgs/{self.org}/teams/{team_slug}"
        return await self.send_api_request("GET", path)

    async def get_teams_with_repos(self) -> AsyncIterator[List[Dict[str, Any]]]:
        """Fetch all teams with their associated repositories"""
        if not self.org:
            raise ValueError("Organization not configured")

        path = f"orgs/{self.org}/teams"

        async for team_batch in self._make_paginated_request(path):
            enriched_teams = []
            for team in team_batch:
                # Get team details
                detailed_team = await self._get_team_details(team["slug"])

                # Get team repositories
                repos_path = f"orgs/{self.org}/teams/{team['slug']}/repos"
                detailed_team["repositories"] = []
                async for repo_batch in self._make_paginated_request(repos_path):
                    detailed_team["repositories"].extend([repo["name"] for repo in repo_batch])

                enriched_teams.append(detailed_team)
            yield enriched_teams

    async def get_pull_requests(
        self, repo: str, params: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        path = await self.get_repo_endpoint(repo, "pulls")
        params = params or {}
        params.update({"state": "all"})  # Get all PRs (open, closed, merged)
        logger.info(f"Fetching PRs for {repo} with params: {params}")

        async for batch in self._make_paginated_request(path, params):
            yield batch

    async def get_issues(
        self, repo_name: str, params: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """Fetch all issues for a specific repository"""
        path = f"repos/{self.org}/{repo_name}/issues"
        params = params or {}
        params.update(
            {
                "state": "all",  # Get open, closed, and merged issues
                "filter": "all",  # Include all issue types
                "per_page": 100,  # Max items per page
            }
        )

        async for batch in self._make_paginated_request(path, params):
            # Filter out pull requests (GitHub API returns both)
            actual_issues = [issue for issue in batch if "pull_request" not in issue]
            if actual_issues:
                yield actual_issues

    async def get_workflows(self, repo: str) -> AsyncIterator[List[Dict[str, Any]]]:
        path = f"repos/{self.org}/{repo}/actions/workflows" if self.org else f"repos/{self.username}/{repo}/actions/workflows"
        logger.info(f"Fetching workflows from: {path}")
        
        try:
            response = await self.send_api_request("GET", path)
            logger.debug(f"API response: {response}")
            
            if not response.get("workflows"):
                logger.warning(f"No workflows found in {repo}")
                yield []
                return
                
            # Add repository context
            workflows = response["workflows"]
            for w in workflows:
                w["repository"] = {
                    "full_name": f"{self.org or self.username}/{repo}",
                    "name": repo
                }
                
            logger.info(f"Found {len(workflows)} workflows in {repo}")
            yield workflows
            
        except Exception as e:
            logger.error(f"Failed to get workflows: {str(e)}")
            yield []

    async def get_workflow(
        self, repo: str, workflow_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get details for a specific workflow"""
        path = await self.get_repo_endpoint(repo, f"actions/workflows/{workflow_id}")
        try:
            return await self.send_api_request("GET", path)
        except Exception as e:
            logger.error(f"Failed to get workflow {workflow_id} for {repo}: {e}")
            return None
    async def get_repository_resource(
        self,
        repos_batch: List[Dict[str, Any]],
        resource_type: str,
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        if resource_type not in self.VALID_REPOSITORY_RESOURCES:
            raise ValueError(f"Invalid resource type: {resource_type}")

        for repo in repos_batch:
            try:
                path = f"repos/{repo['full_name']}/{resource_type}"
                async for batch in self._make_paginated_request(path):
                    yield batch
            except Exception as e:
                logger.error(f"Failed to get {resource_type} for {repo['full_name']}: {e}")
                continue


def create_github_client() -> GitHubClient:
    """Factory function to create and configure a GitHubClient instance."""
    try:
        integration_config: Dict[str, Any] = ocean.integration_config

        # Validate required configurations
        if not integration_config.get("token"):
            raise ValueError("GitHub token is required in integration config")

        base_url = integration_config.get("github_host", "https://api.github.com").rstrip("/")
        github_token = integration_config["token"]
        org = integration_config.get("organization")

        logger.info("Creating GitHub client with configuration:")
        logger.info(f"Base URL: {base_url}")
        logger.info(f"Organization: {org or 'Not specified (some features may be limited)'}")

        client = GitHubClient(base_url, github_token)
        if org:
            client.org = org

        return client

    except KeyError as e:
        logger.error(f"Missing required configuration: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to create GitHub client: {e}")
        raise
