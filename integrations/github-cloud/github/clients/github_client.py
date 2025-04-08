import asyncio
from functools import partial
from typing import Any, AsyncIterator, Callable, Optional

from loguru import logger
from port_ocean.context.ocean import ocean
from port_ocean.utils.async_iterators import (
    semaphore_async_iterator,
    stream_async_iterators_tasks,
)

from github.clients.rest_client import RestClient


class GitHubClient:
    DEFAULT_PARAMS = {
        "per_page": 100,  # Maximum allowed by GitHub API
    }

    def __init__(self, base_url: str, token: str) -> None:
        self.rest = RestClient(base_url, token)
        # The organization is set by the client factory
        self.org = ""
        # The owner type (user or organization)
        self.owner_type = None
        
        # Log the client initialization
        logger.info(f"GitHubClient initialized with base URL: {base_url}")

    async def determine_owner_type(self, owner: str) -> str:
        """Determine if the owner is a user or an organization."""
        if self.owner_type:
            logger.info(f"Using cached owner type: {self.owner_type}")
            return self.owner_type
            
        logger.info(f"Determining type for owner: {owner}")
        try:
            # Make a direct API call to get the owner type
            response = await self.rest.send_api_request(
                "GET", 
                f"users/{owner}",
                params=self.DEFAULT_PARAMS
            )
            
            # Extract the type from the response
            self.owner_type = response.get("type", "User")
            logger.info(f"Owner '{owner}' is of type: {self.owner_type}")
            
            # Log additional information for debugging
            logger.info(f"Full owner response: {response}")
            logger.info(f"Owner login: {response.get('login')}")
            logger.info(f"Owner type: {self.owner_type}")
            
            return self.owner_type
        except Exception as e:
            logger.error(f"Error determining owner type: {e}")
            if hasattr(e, 'response'):
                logger.error(f"Response status code: {e.response.status_code}")
                logger.error(f"Response headers: {e.response.headers}")
                try:
                    error_json = e.response.json()
                    logger.error(f"Error details: {error_json}")
                except:
                    logger.error(f"Response text: {e.response.text}")
            # Default to User if we can't determine the type
            self.owner_type = "User"
            return self.owner_type

    async def get_repository(self, owner: str, repo: str) -> dict[str, Any]:
        """Get a specific repository."""
        logger.info(f"Fetching repository {owner}/{repo}")
        return await self.rest.send_api_request(
            "GET", f"repos/{owner}/{repo}", params=self.DEFAULT_PARAMS
        )

    async def get_team(self, org: str, team_slug: str) -> dict[str, Any]:
        """Get a specific team."""
        logger.info(f"Fetching team {org}/{team_slug}")
        return await self.rest.send_api_request(
            "GET", f"orgs/{org}/teams/{team_slug}", params=self.DEFAULT_PARAMS
        )

    async def get_pull_request(
        self, owner: str, repo: str, pull_number: int
    ) -> dict[str, Any]:
        """Get a specific pull request."""
        logger.info(f"Fetching pull request {owner}/{repo}#{pull_number}")
        return await self.rest.send_api_request(
            "GET", f"repos/{owner}/{repo}/pulls/{pull_number}"
        )

    async def get_issue(self, owner: str, repo: str, issue_number: int) -> dict[str, Any]:
        """Get a specific issue."""
        logger.info(f"Fetching issue {owner}/{repo}#{issue_number}")
        return await self.rest.send_api_request(
            "GET", f"repos/{owner}/{repo}/issues/{issue_number}"
        )

    async def get_workflow(
        self, owner: str, repo: str, workflow_id: str
    ) -> dict[str, Any]:
        """Get a specific workflow."""
        logger.info(f"Fetching workflow {owner}/{repo}/{workflow_id}")
        return await self.rest.send_api_request(
            "GET", f"repos/{owner}/{repo}/actions/workflows/{workflow_id}"
        )

    async def get_repositories(
        self,
        params: Optional[dict[str, Any]] = None,
        max_concurrent: int = 10,
        include_languages: bool = False,
    ) -> AsyncIterator[list[dict[str, Any]]]:
        """Fetch repositories from the GitHub API."""
        if not self.org:
            logger.warning("No GitHub organization specified in the client")
            return
            
        # Determine the owner type
        owner_type = await self.determine_owner_type(self.org)
        
        # Log the API request details
        logger.info(f"Fetching repositories for {owner_type.lower()}: {self.org}")
        
        # Use the appropriate endpoint based on the owner type
        if owner_type == "Organization":
            path = f"orgs/{self.org}/repos"
            logger.info(f"Using organization endpoint: {path}")
        else:
            path = f"users/{self.org}/repos"
            logger.info(f"Using user endpoint: {path}")
            
        params = params or {}
        params.update(self.DEFAULT_PARAMS)
        
        try:
            async for batch in self.rest.get_paginated_resource(path, params=params):
                logger.info(f"Received batch of {len(batch)} repositories")
                if include_languages:
                    batch = await self._enrich_batch(
                        batch,
                        self.enrich_repository_with_languages,
                        max_concurrent,
                    )
                yield batch
        except Exception as e:
            logger.error(f"Error fetching repositories: {e}")
            if hasattr(e, 'response'):
                logger.error(f"Response status code: {e.response.status_code}")
                logger.error(f"Response headers: {e.response.headers}")
                try:
                    error_json = e.response.json()
                    logger.error(f"Error details: {error_json}")
                except:
                    logger.error(f"Response text: {e.response.text}")
            raise

    async def _enrich_batch(
        self,
        batch: list[dict[str, Any]],
        enrich_func: Callable[[dict[str, Any]], AsyncIterator[list[dict[str, Any]]]],
        max_concurrent: int,
    ) -> list[dict[str, Any]]:
        """Enrich a batch of items with additional data."""
        if not batch:
            return batch

        async def process_item(item: dict[str, Any]) -> dict[str, Any]:
            async for enriched_batch in enrich_func(item):
                return enriched_batch[0] if enriched_batch else item
            return item

        tasks = [process_item(item) for item in batch]
        enriched_items = await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

        return [
            item if not isinstance(item, Exception) else batch[i]
            for i, item in enumerate(enriched_items)
        ]

    async def enrich_repository_with_languages(
        self, repo: dict[str, Any]
    ) -> AsyncIterator[list[dict[str, Any]]]:
        """Enrich a repository with its languages."""
        try:
            languages = await self.rest.get_repository_languages(repo["full_name"])
            repo["languages"] = list(languages.keys())
            yield [repo]
        except Exception as e:
            logger.error(f"Error enriching repository with languages: {e}")
            yield [repo]

    async def get_teams(
        self, org: Optional[str] = None
    ) -> AsyncIterator[list[dict[str, Any]]]:
        """Fetch teams from the GitHub API."""
        # Use the organization from the client instance if not provided
        org = org or self.org
        if not org:
            logger.warning("No GitHub organization specified in the client")
            return
            
        # Determine the owner type
        owner_type = await self.determine_owner_type(org)
        
        # Teams are only available for organizations
        if owner_type != "Organization":
            logger.warning(f"Cannot fetch teams for {owner_type.lower()}: {org}")
            return
            
        # Log the API request details
        logger.info(f"Fetching teams for organization: {org}")
        
        path = f"orgs/{org}/teams"
        params = self.DEFAULT_PARAMS.copy()
        
        try:
            async for batch in self.rest.get_paginated_resource(path, params=params):
                # Process each team in the batch to ensure required fields are present
                for team in batch:
                    # Ensure name field is present
                    if 'name' not in team:
                        logger.warning(f"Team missing name field: {team}")
                        team['name'] = team.get('slug', 'Unknown Team')
                    
                    # Ensure html_url field is present
                    if 'html_url' not in team:
                        logger.warning(f"Team missing html_url field: {team}")
                        team['html_url'] = f"https://github.com/orgs/{org}/teams/{team.get('slug', '')}"
                    
                    # Log the updated team data
                    logger.info(f"Team data: {team}")
                    logger.info(f"Team name: {team.get('name')}")
                    logger.info(f"Team html_url: {team.get('html_url')}")
                
                logger.info(f"Received batch of {len(batch)} teams")
                yield batch
        except Exception as e:
            logger.error(f"Error fetching teams: {e}")
            if hasattr(e, 'response'):
                logger.error(f"Response status code: {e.response.status_code}")
                logger.error(f"Response headers: {e.response.headers}")
                try:
                    error_json = e.response.json()
                    logger.error(f"Error details: {error_json}")
                except:
                    logger.error(f"Response text: {e.response.text}")
            raise

    async def get_repository_resource(
        self,
        repos_batch: list[dict[str, Any]],
        resource_type: str,
        max_concurrent: int = 10,
    ) -> AsyncIterator[list[dict[str, Any]]]:
        """Fetch a resource for a batch of repositories."""
        if resource_type not in self.rest.VALID_REPOSITORY_RESOURCES:
            logger.error(f"Invalid repository resource type: {resource_type}")
            return

        async def process_repo(repo: dict[str, Any]) -> list[dict[str, Any]]:
            async for batch in self._process_single_repository(repo, resource_type):
                return batch
            return []

        tasks = [process_repo(repo) for repo in repos_batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error processing repository: {result}")
                continue
            if result:
                yield result

    async def _process_single_repository(
        self,
        repo: dict[str, Any],
        resource_type: str,
    ) -> AsyncIterator[list[dict[str, Any]]]:
        """Process a single repository to fetch a resource."""
        try:
            logger.info(f"Fetching {resource_type} for repository {repo['full_name']}")
            async for batch in self.rest.get_paginated_repository_resource(
                repo["full_name"], resource_type
            ):
                if batch:
                    logger.info(f"Received {len(batch)} {resource_type} for repository {repo['full_name']}")
                    # Log the first item in the batch for debugging
                    if len(batch) > 0:
                        logger.info(f"Sample {resource_type} data: {batch[0]}")
                yield batch
        except Exception as e:
            logger.error(f"Error processing repository {repo['full_name']}: {e}")
            yield []

    async def get_issues(self, repo: Optional[str] = None) -> AsyncIterator[list[dict[str, Any]]]:
        """Fetch issues for a repository or the entire organization."""
        if repo:
            # If a specific repository is provided, fetch issues for that repo
            path = f"repos/{self.org}/{repo}/issues"
            logger.info(f"Fetching issues for repository: {repo}")
        else:
            # For organization-wide issues, we need to fetch issues from each repository
            logger.info(f"Fetching issues for all repositories in {self.org}")
            async for repos_batch in self.get_repositories():
                for repo in repos_batch:
                    path = f"repos/{self.org}/{repo['name']}/issues"
                    logger.info(f"Fetching issues for repository: {repo['name']}")
                    params = {
                        "state": "all",  # Get both open and closed issues
                        "filter": "all",  # Get all issues (not just assigned to the authenticated user)
                        "per_page": 100,  # Maximum allowed by GitHub API
                    }
                    try:
                        async for batch in self.rest.get_paginated_resource(path, params=params):
                            if not batch:
                                logger.warning(f"No issues found for repository: {repo['name']}")
                                continue
                            
                            logger.info(f"Received {len(batch)} issues from repository {repo['name']}")
                            # Log a sample of the issue data for debugging
                            if batch:
                                sample_issue = batch[0]
                                logger.info(f"Sample issue data: {sample_issue}")
                                logger.info(f"Issue number: {sample_issue.get('number')}")
                                logger.info(f"Issue title: {sample_issue.get('title')}")
                                logger.info(f"Issue state: {sample_issue.get('state')}")
                            
                            yield batch
                    except Exception as e:
                        logger.error(f"Error fetching issues for repository {repo['name']}: {e}")
                        if hasattr(e, 'response'):
                            logger.error(f"Response status code: {e.response.status_code}")
                            logger.error(f"Response headers: {e.response.headers}")
                            try:
                                error_json = e.response.json()
                                logger.error(f"Error details: {error_json}")
                            except:
                                logger.error(f"Response text: {e.response.text}")
                        continue
            return
        
        # For a single repository
        params = {
            "state": "all",  # Get both open and closed issues
            "filter": "all",  # Get all issues (not just assigned to the authenticated user)
            "per_page": 100,  # Maximum allowed by GitHub API
        }
        
        try:
            async for batch in self.rest.get_paginated_resource(path, params=params):
                if not batch:
                    logger.warning(f"No issues found for path: {path}")
                    continue
                
                logger.info(f"Received {len(batch)} issues")
                # Log a sample of the issue data for debugging
                if batch:
                    sample_issue = batch[0]
                    logger.info(f"Sample issue data: {sample_issue}")
                    logger.info(f"Issue number: {sample_issue.get('number')}")
                    logger.info(f"Issue title: {sample_issue.get('title')}")
                    logger.info(f"Issue state: {sample_issue.get('state')}")
                
                yield batch
        except Exception as e:
            logger.error(f"Error fetching issues: {e}")
            if hasattr(e, 'response'):
                logger.error(f"Response status code: {e.response.status_code}")
                logger.error(f"Response headers: {e.response.headers}")
                try:
                    error_json = e.response.json()
                    logger.error(f"Error details: {error_json}")
                except:
                    logger.error(f"Response text: {e.response.text}")
            raise 