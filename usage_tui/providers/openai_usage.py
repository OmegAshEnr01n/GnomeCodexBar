"""OpenAI usage and cost provider."""

import os
from datetime import datetime, timedelta, timezone

import httpx

from usage_tui.providers.base import (
    AuthenticationError,
    BaseProvider,
    ProviderError,
    ProviderName,
    ProviderResult,
    UsageMetrics,
    WindowPeriod,
)


class OpenAIUsageProvider(BaseProvider):
    """
    Provider for OpenAI API usage and cost metrics.

    Uses the official OpenAI Admin API to fetch organization usage data.
    Requires an admin/org API key with appropriate permissions.

    Environment Variables:
        OPENAI_ADMIN_KEY: Organization admin API key (sk-...)

    Official API endpoints:
        - GET /v1/organization/usage/completions
        - GET /v1/organization/costs
    """

    name = ProviderName.OPENAI
    BASE_URL = "https://api.openai.com/v1/organization"
    TOKEN_ENV_VAR = "OPENAI_ADMIN_KEY"

    def __init__(self, api_key: str | None = None) -> None:
        """
        Initialize the OpenAI usage provider.

        Args:
            api_key: Admin API key. If not provided, reads from environment.
        """
        self._api_key = api_key or os.environ.get(self.TOKEN_ENV_VAR)

    def is_configured(self) -> bool:
        """Check if API key is available."""
        return self._api_key is not None and self._api_key.startswith("sk-")

    def get_config_help(self) -> str:
        """Get configuration instructions."""
        return f"""OpenAI Usage Provider Configuration:

1. Get an admin API key from your OpenAI organization settings
2. Set environment variable:
   export {self.TOKEN_ENV_VAR}=sk-...

Note: Must be an organization/admin key with usage permissions."""

    def _get_time_range(self, window: WindowPeriod) -> tuple[int, int]:
        """Get Unix timestamps for the time window."""
        now = datetime.now(timezone.utc)
        days = {"5h": 1, "7d": 7, "30d": 30}[window.value]  # 5h maps to 1 day for OpenAI
        start = now - timedelta(days=days)
        return int(start.timestamp()), int(now.timestamp())

    async def fetch(self, window: WindowPeriod = WindowPeriod.DAY_7) -> ProviderResult:
        """Fetch OpenAI usage and cost data."""
        if not self.is_configured():
            return self._make_error_result(
                window=window,
                error=f"Not configured. Set {self.TOKEN_ENV_VAR} environment variable.",
            )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self._api_key}"}
                start_time, end_time = self._get_time_range(window)

                # Fetch usage and costs in parallel
                usage_task = self._fetch_usage(client, headers, start_time, end_time)
                costs_task = self._fetch_costs(client, headers, start_time, end_time)

                usage_data, costs_data = await usage_task, await costs_task

                return self._build_result(window, usage_data, costs_data)

        except AuthenticationError:
            raise
        except httpx.TimeoutException:
            return self._make_error_result(window=window, error="Request timed out")
        except httpx.RequestError as e:
            return self._make_error_result(window=window, error=f"Network error: {e}")
        except Exception as e:
            raise ProviderError(f"Unexpected error: {e}") from e

    async def _fetch_usage(
        self,
        client: httpx.AsyncClient,
        headers: dict,
        start_time: int,
        end_time: int,
    ) -> dict:
        """Fetch completions usage data."""
        response = await client.get(
            f"{self.BASE_URL}/usage/completions",
            headers=headers,
            params={
                "start_time": start_time,
                "end_time": end_time,
                "bucket_width": "1d",
            },
        )
        self._check_response(response)
        return response.json()

    async def _fetch_costs(
        self,
        client: httpx.AsyncClient,
        headers: dict,
        start_time: int,
        end_time: int,
    ) -> dict:
        """Fetch cost data."""
        response = await client.get(
            f"{self.BASE_URL}/costs",
            headers=headers,
            params={
                "start_time": start_time,
                "end_time": end_time,
                "bucket_width": "1d",
            },
        )
        self._check_response(response)
        return response.json()

    def _check_response(self, response: httpx.Response) -> None:
        """Check response status and raise appropriate errors."""
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")

        if response.status_code == 403:
            raise AuthenticationError("API key lacks required permissions")

        if response.status_code != 200:
            raise ProviderError(f"API error: HTTP {response.status_code}")

    def _build_result(
        self, window: WindowPeriod, usage_data: dict, costs_data: dict
    ) -> ProviderResult:
        """Build normalized result from usage and cost data."""
        # Aggregate usage from buckets
        total_input_tokens = 0
        total_output_tokens = 0
        total_requests = 0

        for bucket in usage_data.get("data", []):
            for result in bucket.get("results", []):
                total_input_tokens += result.get("input_tokens", 0)
                total_output_tokens += result.get("output_tokens", 0)
                total_requests += result.get("num_model_requests", 0)

        # Aggregate costs from buckets
        total_cost = 0.0
        for bucket in costs_data.get("data", []):
            for result in bucket.get("results", []):
                # Cost is in cents, convert to dollars
                amount_cents = result.get("amount", {}).get("value", 0)
                total_cost += amount_cents / 100.0

        metrics = UsageMetrics(
            cost=round(total_cost, 4),
            requests=total_requests,
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            # OpenAI doesn't have quota limits in the same way
            remaining=None,
            limit=None,
            reset_at=None,
        )

        return ProviderResult(
            provider=self.name,
            window=window,
            metrics=metrics,
            raw={"usage": usage_data, "costs": costs_data},
        )
