from typing import Any, Optional
import os

from loguru import logger
from port_ocean.context.ocean import ocean

from github.clients.github_client import GitHubClient

_github_client: Optional[GitHubClient] = None


def create_github_client() -> GitHubClient:
    global _github_client
    if _github_client is not None:
        return _github_client

    # Get configuration from ocean.integration_config
    integration_config: dict[str, Any] = ocean.integration_config
    
    # Log all variables in the integration config
    logger.info("All variables in integration config:")
    for key, value in integration_config.items():
        # Mask sensitive values
        masked_value = "***" if key in ["github_token", "token"] else value
        logger.info(f"  {key}: {masked_value}")
    
    # Get specific configuration values
    base_url = integration_config.get("github_host", "https://api.github.com").rstrip("/")
    github_token = integration_config.get("github_token", "")
    
    # Hard-coded the organization for now
    org = "isaac-kwarteng"
    logger.info(f"Using hard-coded organization: {org}")
    
    # Log the configuration for debugging
    logger.info(f"Creating GitHub client with configuration:")
    logger.info(f"Base URL: {base_url}")
    logger.info(f"Organization: {org}")
    
    # Check if required variables are missing
    if not github_token:
        logger.warning("GitHub token is missing from the integration config")
    else:
        # Check if this is a classic token (which might be restricted by the organization)
        # We can't directly check, but we can warn about potential issues
        logger.warning(
            "If you encounter a 403 error about token lifetime, consider using a fine-grained token "
            "instead of a classic token. Fine-grained tokens are more secure and can bypass "
            "organization restrictions on token lifetime."
        )
    
    _github_client = GitHubClient(base_url, github_token)
    # Set the organization explicitly
    _github_client.org = org
    return _github_client