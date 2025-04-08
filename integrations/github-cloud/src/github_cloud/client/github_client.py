from typing import Dict, List, Optional
import aiohttp
from port_ocean.core.integrations.base import BaseIntegration

class GitHubClient:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.session: Optional[aiohttp.ClientSession] = None
        self.token: Optional[str] = None

    async def initialize(self, context: Dict) -> None:
        """Initialize the GitHub client with authentication."""
        self.token = context.get("token")
        if not self.token:
            raise ValueError("GitHub token is required")
        
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
            }
        )

    async def close(self) -> None:
        """Close the HTTP session."""
        if self.session:
            await self.session.close()

    async def get_repositories(self) -> List[Dict]:
        """Fetch all repositories the token has access to."""
        async with self.session.get(f"{self.base_url}/user/repos") as response:
            response.raise_for_status()
            return await response.json()

    async def get_branches(self, repo: str) -> List[Dict]:
        """Fetch all branches for a repository."""
        async with self.session.get(f"{self.base_url}/repos/{repo}/branches") as response:
            response.raise_for_status()
            return await response.json()

    async def get_pull_requests(self, repo: str) -> List[Dict]:
        """Fetch all pull requests for a repository."""
        async with self.session.get(f"{self.base_url}/repos/{repo}/pulls") as response:
            response.raise_for_status()
            return await response.json()

    async def get_issues(self, repo: str) -> List[Dict]:
        """Fetch all issues for a repository."""
        async with self.session.get(f"{self.base_url}/repos/{repo}/issues") as response:
            response.raise_for_status()
            return await response.json() 