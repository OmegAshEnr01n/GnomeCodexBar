# How You Can Help Test Usage-TUI

## ✅ What's Been Implemented

The entire Usage-TUI system is complete:
- Base provider architecture with normalized output
- Caching system (memory + disk)
- Configuration management
- CLI with multiple commands
- Interactive Textual TUI
- OpenAI provider (ready to test)
- Claude OAuth provider (needs endpoint verification)
- **NEW:** Interactive OAuth login flow

## 🧪 What Needs Testing

### Test 1: Interactive OAuth Login (5 minutes)

```bash
cd ~/Desktop/Projects/GnomeCodexBar
usage-tui login
```

**What should happen:**
1. Opens browser to Claude login page
2. You log in with your Claude credentials
3. Browser redirects to `http://localhost:8734/callback`
4. Terminal shows success message
5. Token is saved

**Please report:**
- Does the browser open? Y/N
- What URL does it go to?
- What do you see in the browser?
- Any error messages?
- Does it complete successfully?

**Why this matters:** If this works, users can authenticate without copying/pasting tokens!

---

### Test 2: OpenAI Provider (if you have access)

If you have an OpenAI admin API key:

```bash
export OPENAI_ADMIN_KEY="sk-..."
usage-tui show --provider openai
usage-tui tui
```

**This proves:** The entire system works end-to-end with a stable API.

---

### Test 3: Claude Admin Key (if you have org access)

According to [Claude's docs](https://platform.claude.com/docs/en/build-with-claude/usage-cost-api), you need an admin key (`sk-ant-admin-...`) for usage data.

**If you have org access:**
1. Go to: https://console.anthropic.com/settings/admin-keys
2. Create an admin key
3. Test:
```bash
export CLAUDE_ADMIN_KEY="sk-ant-admin-..."
usage-tui show --provider claude
```

---

### Test 4: The Interactive TUI

Once you have working credentials:

```bash
usage-tui tui
```

**Test these features:**
- Does the UI render correctly?
- Do provider cards show data?
- Press `r` - does refresh work?
- Press `1`, `7`, `3` - do time windows switch?
- Press `j` - does JSON view toggle?
- Press `q` - does it quit cleanly?

---

## 🔍 What I Need to Know

### About Your Setup:
1. **Do you have an organization account** or individual?
2. **Do you have access to OpenAI** with an admin key?
3. **Can you create an admin API key** at Claude Console?

### About the OAuth Flow:
When you run `usage-tui login`:
- Screenshot what the browser shows?
- Copy any error messages?
- Does it find the OAuth endpoints?

### About the TUI:
- Does it look good?
- Any visual glitches?
- Performance issues?
- Feature requests?

---

## 📋 Quick Testing Checklist

```bash
# 1. Try OAuth login
usage-tui login
# → Report what happens

# 2. Check configuration
usage-tui env
# → Shows which providers are configured

# 3. Run doctor
usage-tui doctor
# → Tests connectivity

# 4. Try to show data
usage-tui show
# → Shows metrics (if configured)

# 5. Launch TUI
usage-tui tui
# → Interactive interface
```

---

## 🎯 Priority Order

**Most valuable tests:**
1. **OAuth login** (`usage-tui login`) - This is new, needs testing
2. **OpenAI provider** - Proves the system works
3. **TUI interface** - User experience validation

**Lower priority:**
- Claude admin key (only if you have org access)
- Edge cases and error handling
- Performance testing

---

## 💡 Alternative Approaches (If OAuth Fails)

If `usage-tui login` doesn't work, we can:

### A. Use Claude CLI's stored credentials
Read directly from `~/.claude/.credentials.json`

### B. Parse Claude CLI output
Run `claude` commands and parse results

### C. Admin API only
Focus on organization admin keys (official, stable)

### D. OpenAI focus
Make OpenAI the primary provider, Claude secondary

---

## 📝 Reporting Results

Please share:
```
## OAuth Login Test
- Browser opened: Y/N
- URL shown: <paste URL>
- Error messages: <paste errors>
- Success: Y/N

## OpenAI Test (if available)
- API key works: Y/N
- Data displays: Y/N
- Screenshot: <attach>

## TUI Test
- Renders correctly: Y/N
- Features work: Y/N
- Issues: <describe>
```

---

## 🚀 Once Working

After successful testing, you can:
1. Use daily to track usage
2. Set up alerts for quota limits
3. Export data for analysis
4. Integrate with monitoring tools

**Future features** (based on your feedback):
- Waybar/Polybar output
- GNOME extension
- Cost alerts
- CSV export
- Historical tracking

---

## Questions?

Ask me anything about:
- How the OAuth flow works
- What the code is doing
- How to customize it
- What to test next

**Ready to test!** Start with `usage-tui login` and let me know what happens.
