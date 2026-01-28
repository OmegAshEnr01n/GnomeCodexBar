#!/bin/bash
# Helper script to extract Claude OAuth token and set up environment

CREDENTIALS_FILE="$HOME/.claude/.credentials.json"

echo "🔑 Setting up Usage TUI credentials"
echo "===================================="
echo

# Check if Claude credentials exist
if [ ! -f "$CREDENTIALS_FILE" ]; then
    echo "❌ Claude credentials not found at: $CREDENTIALS_FILE"
    echo
    echo "Run this to set up:"
    echo "  claude setup-token"
    exit 1
fi

# Extract OAuth token
TOKEN=$(python3 -c "
import json
import sys
try:
    data = json.load(open('$CREDENTIALS_FILE'))
    token = data.get('claudeAiOauth', {}).get('accessToken', '')
    if token:
        print(token)
    else:
        sys.exit(1)
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
")

if [ $? -ne 0 ] || [ -z "$TOKEN" ]; then
    echo "❌ Could not extract OAuth token"
    echo
    echo "Your credentials file exists but the token couldn't be read."
    echo "Try running: claude setup-token"
    exit 1
fi

# Verify token format
if [[ ! "$TOKEN" =~ ^sk-ant- ]]; then
    echo "⚠️  Warning: Token doesn't start with 'sk-ant-'"
    echo "   This might not be the correct token format"
fi

echo "✅ Claude OAuth token found"
echo

# Export for current session
export CLAUDE_CODE_OAUTH_TOKEN="$TOKEN"

echo "Token exported for this session as: CLAUDE_CODE_OAUTH_TOKEN"
echo

# Provide instructions for permanent setup
echo "📝 To make this permanent, add to your shell config:"
echo
echo "   # For bash (~/.bashrc):"
echo "   echo 'export CLAUDE_CODE_OAUTH_TOKEN=\"$TOKEN\"' >> ~/.bashrc"
echo
echo "   # For zsh (~/.zshrc):"
echo "   echo 'export CLAUDE_CODE_OAUTH_TOKEN=\"$TOKEN\"' >> ~/.zshrc"
echo
echo "   # Or create a secure .env file:"
echo "   echo 'export CLAUDE_CODE_OAUTH_TOKEN=\"$TOKEN\"' > ~/.usage-tui.env"
echo "   chmod 600 ~/.usage-tui.env"
echo "   # Then: source ~/.usage-tui.env before running usage-tui"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "🚀 Ready to test! Run:"
echo "   usage-tui doctor    # Check connection"
echo "   usage-tui show      # Show metrics"
echo "   usage-tui tui       # Launch TUI"
echo
