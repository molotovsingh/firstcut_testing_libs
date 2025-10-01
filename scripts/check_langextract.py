#!/usr/bin/env python3
"""
LangExtract Connectivity Test
Tests LangExtract/Gemini API connectivity and credentials
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from src.core.langextract_adapter import LangExtractEventExtractor
from src.core.config import LangExtractConfig


def log_result(message: str, log_file: Path):
    """Write timestamped message to log file and stdout"""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    with open(log_file, "a") as f:
        f.write(log_entry + "\n")


def main():
    """Execute LangExtract connectivity test"""

    log_file = project_root / "docs" / "reports" / "langextract_connection.log"

    # Clear previous log
    if log_file.exists():
        log_file.unlink()

    log_result("=" * 80, log_file)
    log_result("LangExtract Connectivity Test", log_file)
    log_result("=" * 80, log_file)

    # Check environment variables
    log_result("\n1. Checking environment variables...", log_file)
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if gemini_key:
        log_result(f"✅ GEMINI_API_KEY found (length: {len(gemini_key)} chars)", log_file)
    else:
        log_result("❌ GEMINI_API_KEY not found in environment", log_file)
        log_result("\nSTATUS: FAILED - Missing API key", log_file)
        return 1

    # Initialize configuration
    log_result("\n2. Loading LangExtract configuration...", log_file)
    try:
        config = LangExtractConfig()
        log_result(f"✅ Configuration loaded", log_file)
        log_result(f"   Model: {config.model_id}", log_file)
        log_result(f"   Temperature: {config.temperature}", log_file)
        log_result(f"   Max Workers: {config.max_workers}", log_file)
    except Exception as e:
        log_result(f"❌ Configuration failed: {e}", log_file)
        log_result("\nSTATUS: FAILED - Configuration error", log_file)
        return 1

    # Initialize adapter
    log_result("\n3. Initializing LangExtract adapter...", log_file)
    try:
        extractor = LangExtractEventExtractor(config)
        log_result("✅ Adapter initialized", log_file)
    except ImportError as e:
        log_result(f"❌ Import error: {e}", log_file)
        log_result("   Possible cause: langextract library not installed", log_file)
        log_result("\nSTATUS: SKIPPED - Library not available", log_file)
        return 2
    except Exception as e:
        log_result(f"❌ Initialization failed: {e}", log_file)
        log_result("\nSTATUS: FAILED - Initialization error", log_file)
        return 1

    # Check availability
    log_result("\n4. Checking adapter availability...", log_file)
    is_available = extractor.is_available()

    if is_available:
        log_result("✅ LangExtract adapter is available", log_file)
    else:
        log_result("❌ LangExtract adapter reports unavailable", log_file)
        log_result("\nSTATUS: FAILED - Adapter not available", log_file)
        return 1

    # Perform minimal extraction test
    log_result("\n5. Performing minimal extraction test...", log_file)

    test_text = """
    This Lease Agreement is entered into on September 21, 2025, between Landlord Corp
    and Tenant LLC. The lease term begins on October 1, 2025 and ends on September 30, 2026.
    Monthly rent of $2,500 is due on the 5th of each month.
    """.strip()

    test_metadata = {
        "file_path": "test_connectivity_check.txt",
        "document_name": "test_connectivity_check.txt"
    }

    try:
        log_result(f"   Test text length: {len(test_text)} chars", log_file)
        log_result("   Calling extract_events()...", log_file)

        events = extractor.extract_events(test_text, test_metadata)

        log_result(f"✅ Extraction completed successfully", log_file)
        log_result(f"   Events extracted: {len(events)}", log_file)

        # Log first event details if available
        if events:
            first_event = events[0]
            log_result(f"\n   First event details:", log_file)
            log_result(f"   - Number: {first_event.number}", log_file)
            log_result(f"   - Date: {first_event.date}", log_file)
            log_result(f"   - Particulars: {first_event.event_particulars[:100]}...", log_file)
            log_result(f"   - Citation: {first_event.citation}", log_file)

            # Check if it's a fallback record
            if first_event.attributes.get("fallback"):
                log_result(f"   ⚠️ WARNING: Fallback record detected", log_file)
                log_result(f"   Reason: {first_event.attributes.get('reason')}", log_file)
                log_result("\nSTATUS: PARTIAL - API call may have failed", log_file)
                return 3

        log_result("\n" + "=" * 80, log_file)
        log_result("STATUS: PASSED ✅", log_file)
        log_result("LangExtract/Gemini API is reachable and functional", log_file)
        log_result("=" * 80, log_file)
        return 0

    except Exception as e:
        log_result(f"❌ Extraction test failed: {e}", log_file)
        log_result(f"   Error type: {type(e).__name__}", log_file)

        import traceback
        log_result(f"\n   Traceback:", log_file)
        for line in traceback.format_exc().split('\n'):
            log_result(f"   {line}", log_file)

        log_result("\nSTATUS: FAILED - Extraction error", log_file)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
