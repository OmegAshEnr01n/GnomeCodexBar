Below is a **clean, copy-pasteable SWE plan** suitable for dropping directly into **Codex**.
It is structured, implementation-oriented, includes **code snippets**, and clearly separates **official vs unofficial surfaces** with **sources**.

---

# Multi-Provider Usage Metrics TUI (Claude · OpenAI/Codex · GitHub Copilot)

## Goal

Build a **local TUI tool** that shows **usage / quota / cost metrics** across:

* **Claude (Claude Code / OAuth quota)**
* **OpenAI / Codex (API usage + cost)**
* **GitHub Copilot (org / enterprise usage reports)**

Design must be:

* Provider-agnostic
* OAuth-aware
* Safe (no scraping)
* Extensible to GNOME / Waybar / daemons later

---

## High-Level Architecture

```
┌────────────────────────┐
│        TUI (rich)      │
│  - overview screen     │
│  - provider detail     │
│  - raw JSON toggle     │
└──────────┬─────────────┘
           │
┌──────────▼─────────────┐
│   Provider Interface   │
│  fetch(window) → dict  │
└──────────┬─────────────┘
     ┌─────┼────────┬─────────┐
     ▼     ▼        ▼         ▼
 Claude   OpenAI   Copilot   (future)
 OAuth    Admin    Reports
```

---

## Normalized Output Contract (Critical)

All providers **must return this shape**:

```json
{
  "provider": "claude | openai | copilot",
  "window": "1d | 7d | 30d",
  "metrics": {
    "cost": 1.42,
    "requests": 37,
    "input_tokens": 120000,
    "output_tokens": 54000,
    "remaining": null,
    "limit": null,
    "reset_at": "ISO8601 | null"
  },
  "updated_at": "ISO8601",
  "raw": {}
}
```

The TUI **never** depends on provider-specific fields.

---

## Provider 1 — Claude (Claude Code OAuth)

### What is supported

* **Claude Code subscription quota**
* Same surface used by **CodexBar**
* Uses **OAuth token** (`sk-ant-oat…`)

### What is NOT supported

* Claude web UI scraping
* Org-level billing (needs Admin API key)

### Auth

* Token generated via:

  ```bash
  claude setup-token
  ```
* Stored as:

  ```bash
  export CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-...
  ```

### Endpoint (unofficial but observed)

```
GET https://api.anthropic.com/api/oauth/usage
Authorization: Bearer <token>
```

### Implementation (Python)

```python
# providers/claude_oauth.py
def fetch(window: str) -> dict:
    r = httpx.get(
        "https://api.anthropic.com/api/oauth/usage",
        headers={"Authorization": f"Bearer {token}"}
    )
    data = r.json()

    return normalize(
        provider="claude",
        used=data.get("used"),
        limit=data.get("limit"),
        reset_at=data.get("resets_at"),
        raw=data
    )
```

### Source

* CodexBar Claude docs (OAuth usage)
* Claude Code tooling docs (`claude setup-token`)
* Anthropic internal OAuth usage behavior (non-public)

⚠️ **Stability note**: this endpoint may change. Code must parse defensively.

---

## Provider 2 — OpenAI / Codex (Official, Stable)

### What this represents

* **OpenAI API usage** (includes Codex CLI if using OpenAI)
* **Token counts + $ cost**
* Org / project scoped

### Auth

```bash
export OPENAI_ADMIN_KEY=sk-...
```

> Must be an org/admin key

---

### Usage Endpoint

```
GET /v1/organization/usage/completions
Authorization: Bearer <ADMIN_KEY>
```

Query params:

* `start_time`
* `end_time`
* `bucket_width=1d`
* `group_by=model`

### Cost Endpoint

```
GET /v1/organization/costs
Authorization: Bearer <ADMIN_KEY>
```

---

### Implementation

```python
# providers/openai_usage.py
def fetch(window: str) -> dict:
    usage = get_usage_buckets(...)
    costs = get_costs(...)

    return {
        "provider": "openai",
        "metrics": {
            "input_tokens": sum(...),
            "output_tokens": sum(...),
            "requests": sum(...),
            "cost": sum(costs),
        },
        "raw": {"usage": usage, "costs": costs}
    }
```

### Sources

* OpenAI Usage API docs
* OpenAI Costs API docs

✅ **Official & stable**

---

## Provider 3 — GitHub Copilot (Org / Enterprise)

### Reality check

* GitHub **does not expose personal Copilot usage**
* APIs are **org / enterprise reporting only**

### Auth

```bash
export GITHUB_TOKEN=ghp_...
```

Required scopes:

* `read:org`
* `read:enterprise`
* `manage_billing:copilot` (depending on endpoint)

---

### API Pattern

1. Request usage report
2. Receive **signed download links**
3. Download JSON / CSV
4. Aggregate locally

Example:

```
GET /orgs/{org}/copilot/usage
→ { download_links: [...] }
```

---

### Implementation

```python
# providers/github_copilot.py
def fetch(window: str) -> dict:
    links = request_report_links()
    report = download(links[0])

    return normalize_from_report(report)
```

### Sources

* GitHub Copilot Usage Metrics API
* GitHub Enterprise Copilot Reporting docs

⚠️ Requires org access

---

## TUI Implementation (Rich)

### Screens

1. **Overview**

   ```
   Claude     62% used   resets 02:41
   OpenAI     $3.21      7d
   Copilot    1,204 req  28d
   ```

2. **Provider Detail**

   * tokens in / out
   * requests
   * cost
   * reset timer

3. **Raw JSON toggle**

---

### CLI Surface

```bash
usage-tui show --provider all --window 7d
usage-tui show --provider claude
usage-tui doctor
```

---

## Project Structure

```
usage_tui/
  cli.py
  tui.py
  providers/
    base.py
    claude_oauth.py
    openai_usage.py
    github_copilot.py
  cache.py
  config.py
```

---

## Caching & Safety

* Cache results 60–180s
* Persist last good payload to disk
* Never log tokens
* Prefer env vars → keyring later

---

## Known Limitations (Explicit)

| Provider | Limitation                         |
| -------- | ---------------------------------- |
| Claude   | OAuth usage endpoint is unofficial |
| Copilot  | No personal usage API              |
| OpenAI   | Admin key required                 |

---

## Future Extensions

* GNOME extension (poll localhost daemon)
* Waybar / i3blocks output mode
* Prometheus exporter
* Unified daily usage ledger

---

## Final Recommendation

**Implement in this order**:

1. Claude OAuth (fast feedback, personal value)
2. OpenAI usage + cost (stable, official)
3. Copilot org reports (slowest, permissions-heavy)

This keeps velocity high while preserving correctness.

---

If you want, next step I can:

* Produce a **v0.2 code diff**
* Add **Waybar single-line output**
* Or design the **GNOME extension on top of this TUI backend**
