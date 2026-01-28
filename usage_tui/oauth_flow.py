"""OAuth flow for Claude authentication."""

import base64
import hashlib
import json
import secrets
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

import httpx


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""

    auth_code: str | None = None
    error: str | None = None

    def do_GET(self) -> None:
        """Handle GET request from OAuth redirect."""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if "code" in params:
            OAuthCallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = """
                <html>
                <head><title>Authentication Successful</title></head>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1>✓ Authentication Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
                """
            self.wfile.write(html.encode("utf-8"))
        elif "error" in params:
            OAuthCallbackHandler.error = params["error"][0]
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = f"""
                <html>
                <head><title>Authentication Failed</title></head>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1>✗ Authentication Failed</h1>
                    <p>Error: {params["error"][0]}</p>
                    <p>You can close this window and try again.</p>
                </body>
                </html>
                """
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress HTTP server logs."""
        pass


class ClaudeOAuthFlow:
    """
    OAuth flow for Claude authentication.

    This implements the OAuth 2.0 authorization code flow:
    1. Opens browser to Claude's authorization page
    2. User logs in and grants permission
    3. Claude redirects back to local server with auth code
    4. Exchange auth code for access token
    5. Save token for future use
    """

    # OAuth endpoints (discovered from Claude CLI behavior)
    # Note: These are unofficial endpoints used by Claude CLI
    AUTHORIZE_URL = "https://console.anthropic.com/oauth/authorize"
    TOKEN_URL = "https://console.anthropic.com/oauth/token"
    CLIENT_ID = "usage-tui"  # Custom client ID

    # Scopes based on actual Claude CLI credentials
    SCOPES = ["user:inference", "user:profile"]

    REDIRECT_URI = "http://localhost:8734/callback"
    REDIRECT_PORT = 8734

    def __init__(self, credentials_path: Path | None = None) -> None:
        """
        Initialize OAuth flow.

        Args:
            credentials_path: Path to save credentials. Defaults to ~/.usage-tui/credentials.json
        """
        if credentials_path is None:
            credentials_path = Path.home() / ".usage-tui" / "credentials.json"
        self.credentials_path = credentials_path
        self.credentials_path.parent.mkdir(parents=True, exist_ok=True)

    def _generate_pkce_pair(self) -> tuple[str, str]:
        """
        Generate PKCE code verifier and challenge.

        Returns:
            Tuple of (code_verifier, code_challenge)
        """
        # Generate random code verifier (43-128 chars)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8")
        code_verifier = code_verifier.rstrip("=")  # Remove padding

        # Generate code challenge (SHA256 hash of verifier)
        challenge_bytes = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode("utf-8")
        code_challenge = code_challenge.rstrip("=")  # Remove padding

        return code_verifier, code_challenge

    async def authenticate(self) -> dict[str, Any]:
        """
        Run the OAuth flow to get an access token.

        Returns:
            Dict with token data including 'access_token', 'refresh_token', etc.

        Raises:
            Exception: If authentication fails
        """
        print("\n🔐 Starting Claude OAuth authentication...")
        print("=" * 60)

        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)

        # Generate PKCE pair
        code_verifier, code_challenge = self._generate_pkce_pair()
        self._code_verifier = code_verifier  # Save for token exchange

        # Build authorization URL with PKCE
        auth_params = {
            "client_id": self.CLIENT_ID,
            "redirect_uri": self.REDIRECT_URI,
            "response_type": "code",
            "state": state,
            "scope": " ".join(self.SCOPES),  # Use Claude-specific scopes
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        auth_url = f"{self.AUTHORIZE_URL}?{urlencode(auth_params)}"

        print("\n📱 Opening browser for authentication...")
        print(f"   URL: {auth_url[:60]}...")
        print("\n   If the browser doesn't open, copy and paste this URL:")
        print(f"   {auth_url}")
        print()

        # Start local server to receive callback
        server = HTTPServer(("localhost", self.REDIRECT_PORT), OAuthCallbackHandler)
        server_thread = Thread(target=server.handle_request, daemon=True)
        server_thread.start()

        # Open browser
        try:
            webbrowser.open(auth_url)
        except Exception as e:
            print(f"⚠️  Could not open browser: {e}")
            print("   Please open the URL manually.")

        print("⏳ Waiting for authentication (timeout: 120s)...")
        print("   Complete the login in your browser...")

        # Wait for callback
        server_thread.join(timeout=120)

        if OAuthCallbackHandler.error:
            raise Exception(f"OAuth error: {OAuthCallbackHandler.error}")

        if not OAuthCallbackHandler.auth_code:
            raise Exception("Authentication timeout or cancelled")

        auth_code = OAuthCallbackHandler.auth_code
        print("\n✓ Authorization code received")

        # Exchange code for token
        print("🔄 Exchanging code for access token...")
        token_data = await self._exchange_code_for_token(auth_code)

        # Save credentials
        self._save_credentials(token_data)
        print(f"✓ Credentials saved to: {self.credentials_path}")

        print("\n✅ Authentication successful!")
        print("=" * 60)

        return token_data

    async def _exchange_code_for_token(self, code: str) -> dict[str, Any]:
        """Exchange authorization code for access token with PKCE."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.REDIRECT_URI,
                    "client_id": self.CLIENT_ID,
                    "code_verifier": self._code_verifier,  # PKCE verifier
                },
            )

            if response.status_code != 200:
                raise Exception(f"Token exchange failed: {response.status_code} - {response.text}")

            return response.json()

    def _save_credentials(self, token_data: dict[str, Any]) -> None:
        """Save credentials to disk."""
        self.credentials_path.write_text(json.dumps(token_data, indent=2))
        self.credentials_path.chmod(0o600)  # Secure permissions

    def load_credentials(self) -> dict[str, Any] | None:
        """Load saved credentials if they exist."""
        if not self.credentials_path.exists():
            return None

        try:
            return json.loads(self.credentials_path.read_text())
        except Exception:
            return None

    def get_access_token(self) -> str | None:
        """Get the current access token."""
        creds = self.load_credentials()
        if creds:
            return creds.get("access_token")
        return None

    async def refresh_token_if_needed(self) -> str | None:
        """
        Refresh the access token if it's expired.

        Returns:
            New access token if refreshed, None if not needed or failed
        """
        creds = self.load_credentials()
        if not creds:
            return None

        # Check if token is expired (simplified - would need actual expiry check)
        refresh_token = creds.get("refresh_token")
        if not refresh_token:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.TOKEN_URL,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "client_id": self.CLIENT_ID,
                    },
                )

                if response.status_code == 200:
                    token_data = response.json()
                    self._save_credentials(token_data)
                    return token_data.get("access_token")

        except Exception:
            pass

        return None


async def run_oauth_flow() -> str | None:
    """
    Helper function to run the OAuth flow and return access token.

    Returns:
        Access token if successful, None otherwise
    """
    flow = ClaudeOAuthFlow()

    # Check if we already have credentials
    existing_token = flow.get_access_token()
    if existing_token:
        print("✓ Found existing credentials")
        print(f"  Token: {existing_token[:15]}...")

        response = input("\nUse existing credentials? (Y/n): ").strip().lower()
        if response not in ("n", "no"):
            return existing_token

    # Run OAuth flow
    try:
        token_data = await flow.authenticate()
        return token_data.get("access_token")
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        return None


if __name__ == "__main__":
    import asyncio

    async def main():
        token = await run_oauth_flow()
        if token:
            print(f"\n✅ Got token: {token[:15]}...")
            print("\nSet environment variable:")
            print(f'export CLAUDE_CODE_OAUTH_TOKEN="{token}"')
        else:
            print("\n❌ Failed to get token")

    asyncio.run(main())
