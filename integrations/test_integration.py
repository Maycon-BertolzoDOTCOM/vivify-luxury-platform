#!/usr/bin/env python3
"""Test the full integration stack: SOCAdapter → DeceptionAgent → AuditBridge."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from vivify.integrations.soc_adapter import SOCAdapter
from vivify.integrations.deception_agent import DeceptionAgent
from vivify.integrations.audit_bridge import AuditBridge


def test_soc_adapter():
    print("\n=== 1. SOCAdapter: Health Check ===")
    adapter = SOCAdapter()
    healthy = adapter.health_check()
    print(f"  SOC Gateway healthy: {healthy}")
    assert healthy, "SOC Gateway must be running on localhost:3333"

    print("\n=== 2. SOCAdapter: Basic Chat ===")
    result = adapter.chat(
        messages=[{"role": "user", "content": "Say 'OK' in one word."}],
        model="qwen2.5:3b",
        temperature=0.1,
        max_tokens=10,
    )
    print(f"  Success: {result['success']}")
    print(f"  Content: {result['content']}")
    assert result["success"], f"Chat failed: {result.get('error')}"
    assert len(result["content"]) > 0, "Empty response"

    print("\n=== 3. SOCAdapter: Async Chat ===")
    import asyncio

    async_result = asyncio.run(
        adapter.achat(
            messages=[{"role": "user", "content": "Say 'ASYNC OK' in two words."}],
            model="qwen2.5:3b",
            temperature=0.1,
            max_tokens=10,
        )
    )
    print(f"  Success: {async_result['success']}")
    print(f"  Content: {async_result['content']}")
    assert async_result["success"], f"Async chat failed: {async_result.get('error')}"


def test_deception_agent():
    print("\n=== 4. DeceptionAgent: Classify Attacker ===")
    agent = DeceptionAgent()

    # Test competitor classification
    result = agent.classify_attacker(
        user_agent="Mozilla/5.0 (compatible; PriceBot/1.0)",
        path="/api/jewels?limit=1000",
        method="GET",
        score=0.8,
        reasons=["Suspicious UA", "High request rate"],
    )
    print(f"  Classified as: {result}")
    assert result in ("competitor", "bot", "researcher", "unknown")

    print("\n=== 5. DeceptionAgent: Generate Poison ===")
    poison = agent.generate_poison(attacker_class="competitor", target_hint="precos")
    print(f"  Poison length: {len(poison)} chars")
    print(f"  Preview: {poison[:100]}...")
    assert len(poison) > 50, "Poison too short"

    print("\n=== 6. DeceptionAgent: Full Request Handler ===")
    response = agent.handle_request(
        user_agent="scrapy/1.2",
        path="/admin/config",
        method="POST",
        score=0.9,
        reasons=["UA contains 'scrapy'", "Suspicious path"],
    )
    print(f"  Attacker class: {response['attacker_class']}")
    print(f"  Action: {response['action']}")
    print(f"  Poison length: {response['poison_length']} chars")
    assert response["action"] == "poisoned"
    assert response["poison_length"] > 0


def test_audit_bridge():
    print("\n=== 7. AuditBridge: Log Action ===")
    bridge = AuditBridge()
    result = bridge.log_action(
        action="test_integration",
        target="vivify_integration_test",
        agent="test_script",
        metadata={"test": True, "phase": "validation"},
    )
    print(f"  Success: {result.get('success')}")
    print(f"  Hash: {result.get('hash', 'N/A')[:16]}...")
    # Audit is non-critical; don't assert if it fails
    if not result.get("success"):
        print(f"  (Audit non-critical, continuing)")

    print("\n=== 8. AuditBridge: Query Actions ===")
    entries = bridge.query_actions(session_id="vivify_integration_test", limit=5)
    print(f"  Entries found: {len(entries)}")
    for e in entries:
        print(f"    - {e.get('event_type')} @ {e.get('timestamp', '?')[:19]}")


def main():
    print("=" * 60)
    print("Vivify Integration Tests")
    print("=" * 60)

    tests = [
        ("SOCAdapter", test_soc_adapter),
        ("DeceptionAgent", test_deception_agent),
        ("AuditBridge", test_audit_bridge),
    ]

    passed = 0
    failed = 0

    for name, fn in tests:
        try:
            fn()
            print(f"  ✅ {name} PASSED")
            passed += 1
        except Exception as e:
            print(f"  ❌ {name} FAILED: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
