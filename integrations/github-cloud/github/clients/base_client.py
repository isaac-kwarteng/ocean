from typing import Any, Optional

import httpx
from loguru import logger
from port_ocean.utils import http_async_client

from github.clients.auth_client import AuthClient


class HTTPBaseClient:
    def __init__(self, base_url: str, token: str, endpoint: str = ""):
        self.token = token
        self._client = http_async_client
        auth_client = AuthClient(token)
        self._headers = auth_client.get_headers()
        self.base_url = f"{base_url}/{endpoint.strip('/')}" if endpoint else base_url

    async def send_api_request(
        self,
        method: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}/{path}"
        logger.info(f"Sending {method} request to {url}")
        logger.info(f"Request params: {params}")
        logger.info(f"Request data: {data}")
        logger.info(f"Request headers: {self._headers}")

        try:
            response = await self._client.request(
                method=method,
                url=url,
                headers=self._headers,
                params=params,
                json=data,
            )
            response.raise_for_status()
            logger.info(f"Response status code: {response.status_code}")
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(
                    f"Resource not found at {url} for the following params {params}"
                )
                return {}
            logger.error(f"HTTP status error for {method} request to {path}: {e}")
            logger.error(f"Response status code: {e.response.status_code}")
            logger.error(f"Response headers: {e.response.headers}")
            try:
                error_json = e.response.json()
                logger.error(f"Error details: {error_json}")
            except:
                logger.error(f"Response text: {e.response.text}")
            raise

        except httpx.HTTPError as e:
            logger.error(f"HTTP error for {method} request to {path}: {e}")
            raise 