#!/usr/bin/env python3
"""
OpenCode Zen API Diagnostic Probe
Minimal connectivity test to isolate endpoint/auth/payload issues
Based on docs/guides/opencode_zen_troubleshooting.md
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


def test_connectivity_variant(variant_name: str, url: str, headers: dict, body: dict):
    """
    Test a specific combination of endpoint/headers/payload

    Args:
        variant_name: Description of this test variant
        url: API endpoint URL
        headers: HTTP headers dict
        body: Request payload dict

    Returns:
        tuple: (success: bool, status_code: int, response_text: str, error: str)
    """
    try:
        import requests

        print(f"\n{'='*80}")
        print(f"Testing: {variant_name}")
        print(f"{'='*80}")
        print(f"URL: {url}")
        print(f"Headers: {json.dumps({k: v[:20]+'...' if k in ['Authorization', 'X-API-Key'] and len(v) > 20 else v for k, v in headers.items()}, indent=2)}")
        print(f"Body preview: {json.dumps(body, indent=2)[:300]}...")

        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(body),
            timeout=30
        )

        status = response.status_code
        text = response.text
        request_id = response.headers.get('x-request-id', 'N/A')

        print(f"\n✅ Response received:")
        print(f"   Status: {status}")
        print(f"   Request ID: {request_id}")
        print(f"   Response length: {len(text)} chars")
        print(f"   Response preview: {text[:500]}")

        if status == 200:
            try:
                response_json = json.loads(text)
                print(f"   ✅ Valid JSON response")
                return (True, status, text, None)
            except json.JSONDecodeError as e:
                print(f"   ⚠️ Response is not valid JSON: {e}")
                return (False, status, text, f"Invalid JSON: {e}")
        else:
            print(f"   ⚠️ Non-200 status code")
            return (False, status, text, f"HTTP {status}")

    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        return (False, 0, "", str(e))


def main():
    """
    Execute systematic OpenCode Zen connectivity probes
    """
    print(f"\n{'='*80}")
    print(f"OpenCode Zen API Diagnostic Probe")
    print(f"{'='*80}")
    print(f"Started: {datetime.now().isoformat()}")

    # Load configuration from environment
    api_key = os.getenv("OPENCODEZEN_API_KEY")
    base_url = os.getenv("OPENCODEZEN_BASE_URL", "https://api.opencode-zen.example/v1")
    model = os.getenv("OPENCODEZEN_MODEL", "grok-code")

    print(f"\nConfiguration:")
    print(f"  API Key: {'***' + api_key[-4:] if api_key else 'NOT SET'}")
    print(f"  Base URL: {base_url}")
    print(f"  Model: {model}")

    if not api_key:
        print(f"\n❌ OPENCODEZEN_API_KEY not set. Exiting.")
        return 1

    # Minimal test message
    test_messages = [
        {
            "role": "system",
            "content": "You extract legal events as structured JSON."
        },
        {
            "role": "user",
            "content": "Test connectivity only. Reply with: OK"
        }
    ]

    # Test variants to try
    variants = []

    # Variant 1: Bearer auth + /chat/completions
    variants.append({
        "name": "Bearer Auth + /chat/completions (OpenAI-standard)",
        "url": f"{base_url.rstrip('/')}/chat/completions",
        "headers": {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        "body": {
            "model": model,
            "messages": test_messages,
            "temperature": 0.0,
            "stream": False
        }
    })

    # Variant 2: X-API-Key auth + /chat/completions
    variants.append({
        "name": "X-API-Key Auth + /chat/completions",
        "url": f"{base_url.rstrip('/')}/chat/completions",
        "headers": {
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        },
        "body": {
            "model": model,
            "messages": test_messages,
            "temperature": 0.0,
            "stream": False
        }
    })

    # Variant 3: Bearer auth + /completions
    variants.append({
        "name": "Bearer Auth + /completions (legacy)",
        "url": f"{base_url.rstrip('/')}/completions",
        "headers": {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        "body": {
            "model": model,
            "prompt": "Test connectivity. Reply: OK",
            "temperature": 0.0,
            "max_tokens": 10
        }
    })

    # Variant 4: Bearer auth + /extract (original custom endpoint)
    variants.append({
        "name": "Bearer Auth + /extract (original custom)",
        "url": f"{base_url.rstrip('/')}/extract",
        "headers": {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        "body": {
            "model": model,
            "text": "Test connectivity",
            "task": "extraction",
            "format": "json"
        }
    })

    # Execute all variants
    results = []
    for variant in variants:
        success, status, text, error = test_connectivity_variant(
            variant["name"],
            variant["url"],
            variant["headers"],
            variant["body"]
        )
        results.append({
            "name": variant["name"],
            "success": success,
            "status": status,
            "error": error
        })

    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")

    success_count = sum(1 for r in results if r["success"])
    print(f"\nSuccessful variants: {success_count}/{len(results)}")

    for i, result in enumerate(results, 1):
        status_icon = "✅" if result["success"] else "❌"
        print(f"\n{i}. {status_icon} {result['name']}")
        print(f"   Status: {result['status']}")
        if result["error"]:
            print(f"   Error: {result['error']}")

    # Recommendations
    print(f"\n{'='*80}")
    print(f"RECOMMENDATIONS")
    print(f"{'='*80}")

    if success_count == 0:
        print(f"\n❌ No variants succeeded. Possible issues:")
        print(f"   1. Invalid API key")
        print(f"   2. Incorrect base URL")
        print(f"   3. Invalid model slug")
        print(f"   4. Provider requires different endpoint/format")
        print(f"   5. Network connectivity issue")
        print(f"\nNext steps:")
        print(f"   - Verify API key with provider dashboard")
        print(f"   - Check provider API documentation for correct endpoint")
        print(f"   - Confirm model slug is valid")
    elif success_count < len(results):
        successful = [r for r in results if r["success"]]
        print(f"\n✅ Found working configuration:")
        for r in successful:
            print(f"   - {r['name']}")
        print(f"\nUpdate src/core/opencode_zen_adapter.py to use the working variant.")
    else:
        print(f"\n✅ All variants succeeded!")
        print(f"   The API is very flexible. Current adapter should work.")

    print(f"\n{'='*80}")
    print(f"Completed: {datetime.now().isoformat()}")
    print(f"{'='*80}\n")

    return 0 if success_count > 0 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
