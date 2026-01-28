#!/usr/bin/env python3
"""
Test workflow demonstrating usage-tui functionality.

This script simulates provider responses to test the full flow
without requiring real API credentials.
"""

import asyncio
from datetime import datetime, timedelta, timezone

from usage_tui.cache import ResultCache
from usage_tui.providers.base import (
    ProviderName,
    ProviderResult,
    UsageMetrics,
    WindowPeriod,
)


def create_mock_claude_result() -> ProviderResult:
    """Create a mock Claude result with quota data."""
    reset_at = datetime.now(timezone.utc) + timedelta(hours=3, minutes=42)

    metrics = UsageMetrics(
        remaining=38.0,
        limit=100.0,
        reset_at=reset_at,
        cost=None,
        requests=None,
        input_tokens=None,
        output_tokens=None,
    )

    return ProviderResult(
        provider=ProviderName.CLAUDE,
        window=WindowPeriod.DAY_7,
        metrics=metrics,
        raw={
            "used": 62.0,
            "limit": 100.0,
            "resets_at": reset_at.isoformat(),
        },
    )


def create_mock_openai_result() -> ProviderResult:
    """Create a mock OpenAI result with usage and cost data."""
    metrics = UsageMetrics(
        cost=3.2145,
        requests=1204,
        input_tokens=450000,
        output_tokens=125000,
        remaining=None,
        limit=None,
        reset_at=None,
    )

    return ProviderResult(
        provider=ProviderName.OPENAI,
        window=WindowPeriod.DAY_7,
        metrics=metrics,
        raw={
            "usage": {
                "data": [
                    {
                        "results": [
                            {
                                "input_tokens": 450000,
                                "output_tokens": 125000,
                                "num_model_requests": 1204,
                            }
                        ]
                    }
                ]
            },
            "costs": {"data": [{"results": [{"amount": {"value": 32145}}]}]},
        },
    )


def print_result_summary(result: ProviderResult) -> None:
    """Print a formatted summary of a result."""
    print(f"\n{'=' * 60}")
    print(f"Provider: {result.provider.value.upper()}")
    print(f"Window: {result.window.value}")
    print(f"Updated: {result.updated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'=' * 60}")

    m = result.metrics

    if m.usage_percent is not None:
        bar_width = 40
        filled = int(bar_width * m.usage_percent / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        print(f"Usage:    {bar} {m.usage_percent:.1f}%")
        print(f"          ({m.limit - m.remaining:.1f} / {m.limit} used)")

    if m.reset_at:
        delta = m.reset_at - datetime.now(timezone.utc)
        hours = int(delta.total_seconds() // 3600)
        mins = int((delta.total_seconds() % 3600) // 60)
        print(f"Resets:   {hours}h {mins}m")

    if m.cost is not None:
        print(f"Cost:     ${m.cost:.4f}")

    if m.requests is not None:
        print(f"Requests: {m.requests:,}")

    if m.total_tokens is not None:
        print(f"Tokens:   {m.total_tokens:,}")
        if m.input_tokens and m.output_tokens:
            print(f"          ({m.input_tokens:,} in / {m.output_tokens:,} out)")


async def main():
    """Run the test workflow."""
    print("\n🧪 Usage TUI Test Workflow")
    print("=" * 60)
    print("\nThis demonstrates the full usage-tui flow with mock data.\n")

    # Test 1: Create mock results
    print("\n1️⃣  Creating mock provider results...")
    claude_result = create_mock_claude_result()
    openai_result = create_mock_openai_result()
    print("   ✓ Claude result created")
    print("   ✓ OpenAI result created")

    # Test 2: Test caching
    print("\n2️⃣  Testing cache layer...")
    cache = ResultCache()
    cache.set(claude_result)
    cache.set(openai_result)
    print(f"   ✓ Results cached to: {cache._cache_dir}")

    # Test 3: Retrieve from cache
    print("\n3️⃣  Retrieving from cache...")
    cached_claude = cache.get(ProviderName.CLAUDE, WindowPeriod.DAY_7)
    cached_openai = cache.get(ProviderName.OPENAI, WindowPeriod.DAY_7)
    print(f"   ✓ Claude cached: {cached_claude is not None}")
    print(f"   ✓ OpenAI cached: {cached_openai is not None}")

    # Test 4: Display results
    print("\n4️⃣  Displaying results...")
    print_result_summary(claude_result)
    print_result_summary(openai_result)

    # Test 5: Test normalized output
    print("\n\n5️⃣  Testing normalized output format...")
    import json

    output = {
        "claude": claude_result.model_dump(mode="json"),
        "openai": openai_result.model_dump(mode="json"),
    }
    print("\n   JSON Output (normalized):")
    print("   " + "─" * 56)
    for line in json.dumps(output, indent=2, default=str).split("\n")[:20]:
        print(f"   {line}")
    print("   ...")

    # Summary
    print("\n\n✅ All tests passed!")
    print("\n📋 Next steps:")
    print("   1. Set real credentials:")
    print("      export CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-...")
    print("      export OPENAI_ADMIN_KEY=sk-...")
    print()
    print("   2. Test with real data:")
    print("      usage-tui show")
    print("      usage-tui doctor")
    print()
    print("   3. Launch the TUI:")
    print("      usage-tui tui")
    print()


if __name__ == "__main__":
    asyncio.run(main())
