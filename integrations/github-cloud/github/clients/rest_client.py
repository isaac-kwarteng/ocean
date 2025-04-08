from typing import Any, AsyncIterator, Optional
from urllib.parse import quote

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from github.clients.base_client import HTTPBaseClient


class RestClient(HTTPBaseClient):
    DEFAULT_PAGE_SIZE = 100
    VALID_REPOSITORY_RESOURCES = ["issues", "pulls", "actions/workflows"]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    async def get_paginated_resource(
        self, resource_type: str, params: Optional[dict[str, Any]] = None
    ) -> AsyncIterator[list[dict[str, Any]]]:
        """Fetch a paginated resource (e.g., repos, teams)."""
        # Log the API request details
        logger.info(f"Making paginated request to {resource_type} with params: {params}")
        
        try:
            async for batch in self._make_paginated_request(resource_type, params=params):
                # For teams, ensure we have the required fields
                if resource_type.endswith("/teams"):
                    for team in batch:
                        # Ensure name field is present
                        if "name" not in team:
                            logger.warning(f"Team missing name field: {team}")
                            team["name"] = team.get("slug", "Unknown Team")
                        
                        # Ensure html_url field is present
                        if "html_url" not in team:
                            logger.warning(f"Team missing html_url field: {team}")
                            org_login = team.get("organization", {}).get("login", "unknown")
                            team["html_url"] = f"https://github.com/orgs/{org_login}/teams/{team.get('slug', '')}"
                        
                        # Log the updated team data
                        logger.info(f"Team data: {team}")
                        logger.info(f"Team name: {team.get('name')}")
                        logger.info(f"Team html_url: {team.get('html_url')}")
                
                logger.info(f"Received batch from {resource_type}")
                yield batch
        except Exception as e:
            # Log detailed error information
            logger.error(f"Error making paginated request to {resource_type}: {e}")
            if hasattr(e, 'response'):
                logger.error(f"Response status code: {e.response.status_code}")
                logger.error(f"Response headers: {e.response.headers}")
                try:
                    error_json = e.response.json()
                    logger.error(f"Error details: {error_json}")
                except:
                    logger.error(f"Response text: {e.response.text}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    async def get_paginated_repository_resource(
        self,
        repo_full_name: str,
        resource_type: str,
        params: Optional[dict[str, Any]] = None,
    ) -> AsyncIterator[list[dict[str, Any]]]:
        """Fetch a paginated repository resource (e.g., issues, pulls)."""
        encoded_repo_name = quote(repo_full_name, safe="")
        path = f"repos/{encoded_repo_name}/{resource_type}"
        
        # Log the API request details
        logger.info(f"Making paginated request to {path} with params: {params}")
        
        try:
            async for batch in self._make_paginated_request(path, params=params):
                if batch:
                    logger.info(f"Received batch of {len(batch)} {resource_type} from {path}")
                    # Log the first item in the batch for debugging
                    if len(batch) > 0:
                        logger.info(f"Sample {resource_type} data: {batch[0]}")
                else:
                    logger.warning(f"Received empty batch for {path}")
                yield batch
        except Exception as e:
            logger.error(f"Error making paginated request to {path}: {e}")
            if hasattr(e, 'response'):
                logger.error(f"Response status code: {e.response.status_code}")
                logger.error(f"Response headers: {e.response.headers}")
                try:
                    error_json = e.response.json()
                    logger.error(f"Error details: {error_json}")
                except:
                    logger.error(f"Response text: {e.response.text}")
            raise

    async def get_repository_languages(
        self, repo_full_name: str, params: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Get languages for a repository."""
        encoded_repo_name = quote(repo_full_name, safe="")
        path = f"repos/{encoded_repo_name}/languages"
        
        # Log the API request details
        logger.info(f"Fetching languages for repository {repo_full_name}")
        
        try:
            return await self.send_api_request("GET", path, params=params or {})
        except Exception as e:
            logger.error(f"Error fetching languages for repository {repo_full_name}: {e}")
            raise

    async def _make_paginated_request(
        self,
        path: str,
        params: Optional[dict[str, Any]] = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> AsyncIterator[list[dict[str, Any]]]:
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