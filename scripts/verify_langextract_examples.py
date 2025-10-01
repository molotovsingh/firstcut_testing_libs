#!/usr/bin/env python3
"""
LangExtract Examples Verification Script
Smoke test to verify that LangExtract examples are constructed correctly

SANDBOX IMPORT LIMITATIONS:
==========================
This script may encounter SIGFPE (floating point exception) during langextract import
in certain sandbox environments. This is typically caused by native dependencies like
torch or numpy conflicting with sandbox security restrictions.

MANUAL REPRODUCTION STEPS:
==========================
If the automated verification fails, developers can test manually using these commands:

1. Basic Import Test:
   .venv/bin/python -c "import langextract; print('✅ langextract import successful')"

2. Component Test:
   .venv/bin/python -c "import langextract as lx; print('✅ ExampleData:', lx.data.ExampleData)"

3. Construction Test:
   .venv/bin/python - <<'PY'
   import langextract as lx
   extraction = lx.data.Extraction(
       extraction_class="test",
       extraction_text="test",
       attributes={}
   )
   example = lx.data.ExampleData(text="test", extractions=[extraction])
   print("✅ ExampleData construction successful")
   PY

4. Dependencies Test:
   .venv/bin/python -c "import torch, numpy; print('✅ Native dependencies OK')"

TROUBLESHOOTING:
================
- If SIGFPE occurs during import: Check torch/numpy versions and compatibility
- If import succeeds but construction fails: Check langextract API changes
- If all manual tests pass: Issue may be environment-specific, proceed with deployment

Note: The script will emit warnings instead of hard failures when import issues occur,
allowing CI/CD pipelines to continue while alerting developers to potential issues.
"""

import sys
import os
import signal

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def handle_sigfpe(signum, frame):
    """Handle SIGFPE (floating point exception) during import"""
    print("❌ SIGFPE detected during langextract import")
    print("💡 This is likely caused by native dependencies (torch, numpy) in sandbox environment")
    print("📋 To test manually, run:")
    print("   .venv/bin/python -c 'import langextract; print(\"Import successful\")'")
    print("🔍 For detailed diagnosis, use the inline script approach")
    sys.exit(2)  # Different exit code for SIGFPE

def main():
    """Verify LangExtract examples with graceful error handling"""

    # Set up signal handler for SIGFPE
    try:
        signal.signal(signal.SIGFPE, handle_sigfpe)
    except (AttributeError, ValueError):
        # Some systems may not support SIGFPE handling
        pass

    try:
        # Test if langextract module is available with broad exception handling
        try:
            print("🔍 Testing langextract import...")
            import langextract as lx
            print("✅ langextract module available")

            # Verify core components are accessible
            print("🔍 Verifying langextract.data components...")
            ExampleData = lx.data.ExampleData
            Extraction = lx.data.Extraction
            print("✅ ExampleData and Extraction classes accessible")

        except ImportError as e:
            print(f"❌ langextract module not available: {e}")
            return 1
        except Exception as e:
            # Catch any other exceptions including potential system-level errors
            print(f"❌ langextract import failed with {type(e).__name__}: {e}")
            print("💡 This may be due to sandbox environment limitations or native library conflicts")
            print("📋 Manual test commands:")
            print("   .venv/bin/python -c 'import langextract as lx; print(lx.data.ExampleData)'")
            print("   .venv/bin/python -c 'import torch; import numpy; print(\"Dependencies OK\")'")
            return 2

        # Test ExampleData construction without requiring API key
        print("🔍 Testing LangExtractClient examples construction...")

        try:
            from src.core.langextract_client import LangExtractClient
        except ImportError as e:
            print(f"❌ Failed to import LangExtractClient: {e}")
            return 1

        # Temporarily mock the API key check to test example construction
        original_load_key = LangExtractClient._load_api_key
        def mock_load_key(self):
            self.api_key = "mock_key_for_testing"

        LangExtractClient._load_api_key = mock_load_key

        try:
            client = LangExtractClient()
            example_count = len(client.shared_examples)

            print(f"📊 Shared examples count: {example_count}")

            if example_count == 0:
                print("❌ No examples created - LangExtract setup failed")
                print("💡 This indicates an issue with _create_shared_examples method")
                return 1

            # Verify example structure
            if client.shared_examples:
                example = client.shared_examples[0]
                if hasattr(example, 'text') and hasattr(example, 'extractions'):
                    print("✅ Examples use correct API format (text + extractions)")
                    if example.extractions and len(example.extractions) > 0:
                        extraction = example.extractions[0]
                        if (hasattr(extraction, 'extraction_class') and
                            hasattr(extraction, 'extraction_text') and
                            hasattr(extraction, 'attributes')):
                            print("✅ Extractions have required fields")
                            print(f"✅ SUCCESS: {example_count} examples ready for LangExtract")
                            return 0
                        else:
                            print("❌ Extraction missing required fields")
                            print("💡 Check extraction object construction in _create_shared_examples")
                            return 1
                    else:
                        print("❌ Example has no extractions")
                        print("💡 ExampleData objects need non-empty extractions list")
                        return 1
                else:
                    print("❌ Example uses wrong API format")
                    print("💡 Expected ExampleData(text=..., extractions=[...]) format")
                    return 1

        except Exception as client_error:
            print(f"❌ Error during LangExtractClient verification: {type(client_error).__name__}: {client_error}")
            print("💡 This may indicate issues with example construction or API key mocking")
            return 1
        finally:
            # Restore original method
            try:
                LangExtractClient._load_api_key = original_load_key
            except:
                pass  # Best effort restore

    except Exception as e:
        print(f"❌ Unexpected error during verification: {type(e).__name__}: {e}")
        print("💡 This may be due to system-level issues or environment conflicts")
        print("📋 For debugging, try manual import test:")
        print("   .venv/bin/python - <<'EOF'")
        print("   import langextract as lx")
        print("   example = lx.data.ExampleData(text='test', extractions=[])")
        print("   print('ExampleData test successful')")
        print("   EOF")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)