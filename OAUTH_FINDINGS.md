# OAuth Endpoint Investigation

## Current Status: API Changed ⚠️

The OAuth usage endpoint that was expected to work has changed.

### What We Found

1. **Token exists and is valid format**: `sk-ant-oat01-...` (108 chars)
2. **Token is stored in**: `~/.claude/.credentials.json` 
3. **Additional OAuth fields available**:
   - `accessToken` - The OAuth token itself
   - `refreshToken` - For token renewal
   - `expiresAt` - Token expiration
   - `scopes` - OAuth scopes
   - `subscriptionType` - Subscription info
   - `rateLimitTier` - Rate limit tier

### API Response

```bash
curl -H "Authorization: Bearer <token>" https://api.anthropic.com/api/oauth/usage
```

**Returns:**
```json
{
  "type": "error",
  "error": {
    "type": "authentication_error",
    "message": "OAuth authentication is currently not supported.",
    "details": {"error_visibility": "user_facing"}
  }
}
```

**HTTP Status:** 401

## Why This Happened

As noted in the original plan:

> ⚠️ **Stability note**: this endpoint may change. Code must parse defensively.

The endpoint was unofficial and Anthropic has changed their OAuth implementation.

## Next Steps - How You Can Help

### Option 1: Find the New Endpoint
Check what the Claude CLI actually calls when checking usage:

```bash
# Run Claude CLI with network tracing
strace -e trace=network -f claude 2>&1 | grep api.anthropic
# or
tcpdump -i any -A host api.anthropic.com
```

### Option 2: Check Claude CLI Source
If the Claude CLI is open source or has accessible code:
- Look for usage/quota checking logic
- Find what API endpoints it calls
- See if there's a public API we can use

### Option 3: Use Alternative Approach
Instead of direct API calls, we could:
- Parse Claude CLI's config files for usage data (if stored)
- Run `claude` commands and parse output
- Use browser automation to fetch from claude.ai dashboard

### Option 4: Focus on OpenAI First
Since OpenAI's API is official and stable:
1. Set up OpenAI admin key
2. Test that provider fully
3. Decide on Claude later

## What Still Works

Everything else in the project is functional:
- ✅ Provider architecture
- ✅ Caching system
- ✅ Configuration management
- ✅ CLI commands
- ✅ TUI interface
- ✅ OpenAI provider (needs testing with real key)

## Recommended Next Step

**Test with OpenAI** to validate the full system works:

```bash
# Get an admin API key from OpenAI
export OPENAI_ADMIN_KEY=sk-...

# Test
usage-tui show --provider openai
usage-tui tui
```

If OpenAI works, we can confirm the architecture is solid and then focus on fixing Claude.
