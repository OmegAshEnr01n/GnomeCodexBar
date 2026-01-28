"""Configuration management for usage-tui."""

import os
from typing import Any

from usage_tui.claude_cli_auth import extract_claude_cli_token
from usage_tui.providers.base import ProviderName


class Config:
    """
    Application configuration.

    Currently reads only from environment variables.
    Follows the principle of preferring env vars for security.
    """

    # Environment variable mappings
    ENV_VARS = {
        ProviderName.CLAUDE: "CLAUDE_CODE_OAUTH_TOKEN",
        ProviderName.OPENAI: "OPENAI_ADMIN_KEY",
        ProviderName.COPILOT: "GITHUB_TOKEN",
        ProviderName.CODEX: "CODEX_ACCESS_TOKEN",
    }

    # Provider descriptions
    PROVIDER_INFO = {
        ProviderName.CLAUDE: {
            "name": "Claude Code",
            "description": "Claude Code subscription quota via OAuth",
            "official": False,
            "note": "Uses unofficial OAuth endpoint with beta header",
        },
        ProviderName.OPENAI: {
            "name": "OpenAI",
            "description": "OpenAI API usage and costs",
            "official": True,
            "note": "Requires organization admin API key",
        },
        ProviderName.COPILOT: {
            "name": "GitHub Copilot",
            "description": "GitHub Copilot quota via internal API",
            "official": False,
            "note": "Uses VS Code client ID for device flow auth",
        },
        ProviderName.CODEX: {
            "name": "OpenAI Codex",
            "description": "OpenAI Codex usage via ChatGPT backend",
            "official": False,
            "note": "Reads credentials from ~/.codex/auth.json",
        },
    }

    def get_token(self, provider: ProviderName) -> str | None:
        """
        Get authentication token for a provider.

        For Claude: Falls back to extracting from Claude CLI credentials
        if env var is not set.
        """
        env_var = self.ENV_VARS.get(provider)
        if env_var and (token := os.environ.get(env_var)):
            return token

        # Special fallback for Claude: extract from CLI credentials
        if provider == ProviderName.CLAUDE:
            return extract_claude_cli_token()

        return None

    def is_provider_configured(self, provider: ProviderName) -> bool:
        """Check if a provider has required credentials."""
        token = self.get_token(provider)
        if not token:
            return False

        # Basic token validation by prefix
        validation_map = {
            ProviderName.CLAUDE: "sk-ant-",
            ProviderName.OPENAI: "sk-",
            ProviderName.COPILOT: ("ghp_", "github_pat_"),
        }

        if provider in validation_map:
            prefixes = validation_map[provider]
            if isinstance(prefixes, tuple):
                return any(token.startswith(p) for p in prefixes)
            return token.startswith(prefixes)

        return True

    def get_provider_status(self, provider: ProviderName) -> dict[str, Any]:
        """Get detailed status for a provider."""
        info = self.PROVIDER_INFO.get(provider, {})
        env_var = self.ENV_VARS.get(provider, "UNKNOWN")
        configured = self.is_provider_configured(provider)

        return {
            "provider": provider.value,
            "name": info.get("name", provider.value),
            "description": info.get("description", ""),
            "official": info.get("official", False),
            "note": info.get("note", ""),
            "env_var": env_var,
            "configured": configured,
            "token_preview": self._get_token_preview(provider) if configured else None,
        }

    def get_all_provider_status(self) -> list[dict[str, Any]]:
        """Get status for all providers."""
        return [self.get_provider_status(p) for p in ProviderName]

    def _get_token_preview(self, provider: ProviderName) -> str | None:
        """Get a safe preview of the token (first/last few chars)."""
        token = self.get_token(provider)
        if not token or len(token) < 12:
            return None
        return f"{token[:8]}...{token[-4:]}"

    def get_env_var_help(self) -> str:
        """Get help text for setting up environment variables."""
        lines = ["Required environment variables:\n"]

        for provider in ProviderName:
            env_var = self.ENV_VARS.get(provider)
            info = self.PROVIDER_INFO.get(provider, {})
            configured = self.is_provider_configured(provider)
            status = "[OK]" if configured else "[NOT SET]"

            lines.append(f"  {env_var}  {status}")
            lines.append(f"    {info.get('description', '')}")
            if note := info.get("note"):
                lines.append(f"    Note: {note}")
            lines.append("")

        return "\n".join(lines)


# Global config instance
config = Config()
