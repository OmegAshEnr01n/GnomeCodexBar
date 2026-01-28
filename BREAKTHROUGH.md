# Breakthrough: Claude OAuth Usage API

## The Problem
Claude's official Usage API requires:
- Admin API key (`sk-ant-admin-...`)
- Organization account (not available for individual accounts)

Individual users only have:
- OAuth tokens from Claude CLI (`sk-ant-oat01-...`)
- Regular API keys (`sk-ant-api03-...`)

Neither worked with the official `/v1/organizations/usage_report/messages` endpoint.

## The Solution
By analyzing the **CodexBar** project source code, we discovered:

### Secret Beta Header
The **unofficial** OAuth usage endpoint requires a special beta header:

```bash
GET https://api.anthropic.com/api/oauth/usage

Headers:
  Authorization: Bearer sk-ant-oat01-...
  anthropic-beta: oauth-2025-04-20
  Accept: application/json
```

### Required OAuth Scope
The token must include the `user:profile` scope. Tokens with only `user:inference` will get 403.

Check your scopes:
```bash
cat ~/.claude/.credentials.json | jq '.claudeAiOauth.scopes'
```

### Response Format
```json
{
  "five_hour": {
    "utilization": 61.0,
    "resets_at": "2026-01-28T07:59:59.571404+00:00"
  },
  "seven_day": {
    "utilization": 22.0,
    "resets_at": "2026-02-03T09:59:59.571468+00:00"
  },
  "extra_usage": {
    "is_enabled": false,
    "monthly_limit": null,
    "used_credits": null,
    "utilization": null
  }
}
```

- `utilization` is a **percentage** (0-100) of quota used
- `resets_at` is when the quota resets

## What We Implemented

### 1. Updated Claude Provider
**File:** `usage_tui/providers/claude_oauth.py`

Changes:
- Added `anthropic-beta: oauth-2025-04-20` header
- Updated response parser to handle utilization percentages
- Added support for different time windows (5-hour vs 7-day)

### 2. Auto-Load from CLI Credentials
**Files:** 
- `usage_tui/claude_cli_auth.py` - Token extraction
- `usage_tui/config.py` - Auto-fallback logic
- `usage_tui/providers/claude_oauth.py` - Integration

Now the tool automatically:
1. Checks `CLAUDE_CODE_OAUTH_TOKEN` env var
2. Falls back to `~/.claude/.credentials.json`
3. Validates token has `user:profile` scope

### 3. Fixed Token Expiration
The `expiresAt` field is a **millisecond timestamp**, not ISO string:
```python
expires_at = datetime.fromtimestamp(expires_at_ms / 1000, tz=timezone.utc)
```

## Usage

### Quick Test
```bash
# No env var needed if Claude CLI is set up
usage-tui show --provider claude

# With explicit token
export CLAUDE_CODE_OAUTH_TOKEN="sk-ant-oat01-..."
usage-tui show --provider claude --json
```

### Check Configuration
```bash
usage-tui doctor
usage-tui env
```

### Interactive TUI
```bash
usage-tui tui
```

## Credits
This breakthrough came from analyzing the **CodexBar** project:
- Repository: `~/Desktop/Projects/CodexBar`
- Key file: `Sources/CodexBarCore/Providers/Claude/ClaudeOAuth/ClaudeOAuthUsageFetcher.swift:50`
- Documentation: `docs/claude.md:36`

The beta header (`anthropic-beta: oauth-2025-04-20`) was the missing piece.

## Important Notes

1. **Unofficial API**: This endpoint is not documented and may change
2. **Scope Required**: Token must have `user:profile` scope
3. **Individual Accounts Only**: This is for personal Claude accounts, not orgs
4. **Rate Limits**: The API may have undocumented rate limits

## Test Results

✅ **Working**:
- Token extraction from `~/.claude/.credentials.json`
- OAuth usage endpoint with beta header
- Utilization percentage parsing
- Reset time display
- CLI show command
- JSON output
- Doctor command

🔄 **Next Steps**:
- Test TUI interface with real data
- Add better error messages for scope issues
- Consider implementing Web API fallback (cookie-based)
