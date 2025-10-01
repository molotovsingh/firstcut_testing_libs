#!/usr/bin/env python3
"""
OpenRouter Connectivity Test
Tests OpenRouter API connectivity and credentials
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from src.core.openrouter_adapter import OpenRouterEventExtractor
from src.core.config import OpenRouterConfig
from src.core.extractor_factory import ExtractorConfigurationError


def log_result(message: str, log_file: Path):
    """Write timestamped message to log file and stdout"""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    with open(log_file, "a") as f:
        f.write(log_entry + "\n")


def main():
    """Execute OpenRouter connectivity test"""

    log_file = project_root / "docs" / "reports" / "openrouter_connection.log"

    # Clear previous log
    if log_file.exists():
        log_file.unlink()

    log_result("=" * 80, log_file)
    log_result("OpenRouter Connectivity Test", log_file)
    log_result("=" * 80, log_file)

    # Check environment variables
    log_result("\n1. Checking environment variables...", log_file)
    api_key = os.getenv("OPENROUTER_API_KEY")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3-haiku")

    if api_key:
        log_result(f"✅ OPENROUTER_API_KEY found (length: {len(api_key)} chars)", log_file)
        log_result(f"   Base URL: {base_url}", log_file)
        log_result(f"   Model: {model}", log_file)
    else:
        log_result("⚠️ OPENROUTER_API_KEY not found in environment", log_file)
        log_result("   To test OpenRouter, set OPENROUTER_API_KEY in .env", log_file)
        log_result("\nSTATUS: SKIPPED - API key not configured", log_file)
        return 2

    # Check if requests library is available
    log_result("\n2. Checking HTTP client availability...", log_file)
    try:
        import requests
        log_result("✅ requests library is available", log_file)
    except ImportError:
        log_result("❌ requests library not installed", log_file)
        log_result("   Install with: pip install requests", log_file)
        log_result("\nSTATUS: SKIPPED - HTTP client unavailable", log_file)
        return 2

    # Initialize configuration
    log_result("\n3. Loading OpenRouter configuration...", log_file)
    try:
        config = OpenRouterConfig()
        log_result(f"✅ Configuration loaded", log_file)
        log_result(f"   API Key: {'*' * (len(config.api_key) - 4) + config.api_key[-4:]}", log_file)
        log_result(f"   Base URL: {config.base_url}", log_file)
        log_result(f"   Model: {config.model}", log_file)
        log_result(f"   Timeout: {config.timeout}s", log_file)
    except Exception as e:
        log_result(f"❌ Configuration failed: {e}", log_file)
        log_result("\nSTATUS: FAILED - Configuration error", log_file)
        return 1

    # Initialize adapter
    log_result("\n4. Initializing OpenRouter adapter...", log_file)
    try:
        extractor = OpenRouterEventExtractor(config)
        log_result("✅ Adapter initialized", log_file)
    except ExtractorConfigurationError as e:
        log_result(f"❌ Configuration error: {e}", log_file)
        log_result("\nSTATUS: FAILED - Invalid configuration", log_file)
        return 1
    except Exception as e:
        log_result(f"❌ Initialization failed: {e}", log_file)
        log_result("\nSTATUS: FAILED - Initialization error", log_file)
        return 1

    # Check availability
    log_result("\n5. Checking adapter availability...", log_file)
    is_available = extractor.is_available()

    if is_available:
        log_result("✅ OpenRouter adapter is available", log_file)
    else:
        log_result("❌ OpenRouter adapter reports unavailable", log_file)
        log_result("\nSTATUS: FAILED - Adapter not available", log_file)
        return 1

    # Perform minimal extraction test
    log_result("\n6. Performing minimal API connectivity test...", log_file)

    test_text = """
    This Service Agreement was executed on March 15, 2024, between Client Inc. and
    Service Provider LLC. The agreement becomes effective April 1, 2024 and continues
    for a period of 12 months. Payment of $5,000 is due within 30 days of invoice.
    """.strip()

    test_metadata = {
        "file_path": "test_openrouter_connectivity.txt",
        "document_name": "test_openrouter_connectivity.txt"
    }

    try:
        log_result(f"   Test text length: {len(test_text)} chars", log_file)
        log_result("   Calling OpenRouter API via extract_events()...", log_file)
        log_result("   NOTE: This makes a real API call and may incur costs", log_file)

        events = extractor.extract_events(test_text, test_metadata)

        log_result(f"✅ API call completed successfully", log_file)
        log_result(f"   Events extracted: {len(events)}", log_file)

        # Log first event details if available
        if events:
            first_event = events[0]
            log_result(f"\n   First event details:", log_file)
            log_result(f"   - Number: {first_event.number}", log_file)
            log_result(f"   - Date: {first_event.date}", log_file)
            log_result(f"   - Particulars: {first_event.event_particulars[:100]}...", log_file)
            log_result(f"   - Citation: {first_event.citation}", log_file)
            log_result(f"   - Provider: {first_event.attributes.get('provider', 'unknown')}", log_file)

            # Check if it's a fallback record
            if first_event.attributes.get("fallback"):
                log_result(f"   ⚠️ WARNING: Fallback record detected", log_file)
                log_result(f"   Reason: {first_event.attributes.get('reason')}", log_file)
                log_result("\nSTATUS: PARTIAL - API call may have failed", log_file)
                return 3

        log_result("\n" + "=" * 80, log_file)
        log_result("STATUS: PASSED ✅", log_file)
        log_result("OpenRouter API is reachable and functional", log_file)
        log_result("=" * 80, log_file)
        return 0

    except Exception as e:
        log_result(f"❌ API connectivity test failed: {e}", log_file)
        log_result(f"   Error type: {type(e).__name__}", log_file)

        import traceback
        log_result(f"\n   Traceback:", log_file)
        for line in traceback.format_exc().split('\n'):
            log_result(f"   {line}", log_file)

        log_result("\nSTATUS: FAILED - API connectivity error", log_file)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
