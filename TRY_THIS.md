# Try This Now!

I fixed the OAuth flow to include PKCE (the missing `code_challenge` parameter).

## Run This Command:

```bash
usage-tui login
```

## What Changed:

The OAuth flow now includes:
- ✅ `code_challenge` - SHA256 hash for security
- ✅ `code_challenge_method: S256` - Standard PKCE method
- ✅ `code_verifier` - Sent during token exchange

This is the same security mechanism that Claude CLI uses.

## Expected Result:

Browser should open and NOT show "Invalid OAuth Request" anymore. Instead:
1. You'll see Claude's actual login page
2. Log in with your credentials
3. Claude will ask for permission
4. Browser redirects to success page
5. Terminal shows your token

## If It Still Fails:

Let me know:
- What error message do you see?
- Screenshot the browser page?
- Copy any URL it goes to?

This will help us figure out the next step!
