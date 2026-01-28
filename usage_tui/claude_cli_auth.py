"""Extract and use authentication from Claude CLI installation."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ClaudeCLIAuth:
    """
    Extract authentication from existing Claude CLI installation.

    This is a workaround since Claude's OAuth is not publicly documented
    for third-party applications. Instead, we read the credentials that
    the official Claude CLI has already obtained.
    """

    DEFAULT_CREDS_PATH = Path.home() / ".claude" / ".credentials.json"

    def __init__(self, creds_path: Path | None = None) -> None:
        """
        Initialize with path to Claude CLI credentials.

        Args:
            creds_path: Path to Claude CLI credentials. Defaults to ~/.claude/.credentials.json
        """
        self.creds_path = creds_path or self.DEFAULT_CREDS_PATH

    def is_available(self) -> bool:
        """Check if Claude CLI credentials exist."""
        return self.creds_path.exists()

    def get_credentials(self) -> dict[str, Any] | None:
        """
        Load credentials from Claude CLI.

        Returns:
            Dict with OAuth credentials or None if not found
        """
        if not self.is_available():
            return None

        try:
            data = json.loads(self.creds_path.read_text())
            return data.get("claudeAiOauth")
        except Exception:
            return None

    def get_access_token(self) -> str | None:
        """Get the current access token."""
        creds = self.get_credentials()
        return creds.get("accessToken") if creds else None

    def is_token_expired(self) -> bool:
        """Check if the token is expired."""
        creds = self.get_credentials()
        if not creds or "expiresAt" not in creds:
            return True

        try:
            # expiresAt is a timestamp in milliseconds
            expires_at_ms = creds["expiresAt"]
            expires_at = datetime.fromtimestamp(expires_at_ms / 1000, tz=timezone.utc)
            return datetime.now(timezone.utc) >= expires_at
        except Exception:
            return True

    def get_token_info(self) -> dict[str, Any]:
        """Get information about the token."""
        creds = self.get_credentials()
        if not creds:
            return {
                "available": False,
                "error": "Claude CLI credentials not found",
            }

        token = creds.get("accessToken", "")
        expires_at = creds.get("expiresAt")
        expired = self.is_token_expired()

        info = {
            "available": True,
            "token_preview": f"{token[:15]}..." if token else None,
            "expires_at": expires_at,
            "expired": expired,
            "subscription_type": creds.get("subscriptionType"),
            "rate_limit_tier": creds.get("rateLimitTier"),
            "scopes": creds.get("scopes", []),
        }

        if expires_at:
            try:
                # expires_at is a timestamp in milliseconds
                exp_dt = datetime.fromtimestamp(expires_at / 1000, tz=timezone.utc)
                info["expires_at_formatted"] = exp_dt.isoformat()
                remaining = exp_dt - datetime.now(timezone.utc)
                if remaining.total_seconds() > 0:
                    hours = int(remaining.total_seconds() // 3600)
                    info["expires_in_hours"] = hours
            except Exception:
                pass

        return info


def extract_claude_cli_token() -> str | None:
    """
    Helper function to extract token from Claude CLI.

    Returns:
        Access token if available, None otherwise
    """
    auth = ClaudeCLIAuth()
    return auth.get_access_token()
