#!/usr/bin/env python3
"""
DeepSeek Direct API Configuration Diagnostic Script
Validates API key, configuration, and connectivity with detailed error reporting
Tests direct DeepSeek API (not via OpenRouter)
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from dotenv import load_dotenv
from src.core.config import DeepSeekConfig, env_str
from src.core.constants import LEGAL_EVENTS_PROMPT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class DeepSeekDiagnostic:
    """Comprehensive DeepSeek Direct API configuration validation"""

    def __init__(self, test_model: Optional[str] = None, verbose: bool = False):
        self.test_model = test_model
        self.verbose = verbose
        self.checks_passed = 0
        self.total_checks = 10
        self.config = None
        self.api_key_safe = None
        self.log_file = Path(__file__).parent / "deepseek_diagnostic.log"

        # Setup file logging
        file_handler = logging.FileHandler(self.log_file, mode='w')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

    def log(self, message: str, level: str = "INFO"):
        """Log message to console and file"""
        if level == "INFO":
            logger.info(message)
        elif level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        elif level == "DEBUG" and self.verbose:
            logger.debug(message)

    def mask_api_key(self, api_key: str) -> str:
        """Safely mask API key for display"""
        if not api_key or len(api_key) < 16:
            return "***INVALID***"
        return f"{api_key[:8]}...{api_key[-8:]}"

    def print_header(self):
        """Print diagnostic header"""
        self.log("=" * 70)
        self.log("🔍 DeepSeek Direct API Configuration Diagnostic")
        self.log("=" * 70)
        self.log(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"Log file: {self.log_file}")
        self.log("=" * 70)
        self.log("")

    def print_step(self, step: int, name: str):
        """Print step header"""
        self.log(f"\n[Step {step}/{self.total_checks}] {name}")
        self.log("-" * 50)

    def print_result(self, passed: bool, message: str):
        """Print check result"""
        icon = "✅" if passed else "❌"
        self.log(f"{icon} {message}")
        if passed:
            self.checks_passed += 1

    def check_environment_file(self) -> bool:
        """Step 1: Check if .env file exists"""
        self.print_step(1, "Environment File Check")

        project_root = Path(__file__).parent.parent
        env_file = project_root / ".env"

        if not env_file.exists():
            self.print_result(False, f".env file not found at {env_file}")
            self.log("💡 Create .env from .env.example: cp .env.example .env")
            return False

        self.print_result(True, f".env file found at {env_file}")

        # Load environment variables
        load_dotenv(env_file)
        self.log(f"   Loaded environment variables from {env_file}")
        return True

    def check_api_key_format(self) -> bool:
        """Step 2: Validate API key format"""
        self.print_step(2, "API Key Format Validation")

        api_key = os.getenv("DEEPSEEK_API_KEY", "")

        if not api_key:
            self.print_result(False, "DEEPSEEK_API_KEY not set in .env")
            self.log("💡 Get API key from: https://platform.deepseek.com")
            self.log("💡 Add to .env: DEEPSEEK_API_KEY=sk-...")
            return False

        # Check for whitespace
        if api_key != api_key.strip():
            self.print_result(False, "API key contains leading/trailing whitespace")
            return False

        self.api_key_safe = self.mask_api_key(api_key)
        self.print_result(True, f"API key found: {self.api_key_safe}")

        # Check expected format (DeepSeek keys typically start with sk-)
        if api_key.startswith("sk-"):
            self.log(f"   Key format: Valid DeepSeek format (sk-)")
        else:
            self.log(f"   ⚠️  Key format: Unexpected format (expected sk-)")

        # Check length
        if len(api_key) < 20:
            self.log(f"   ⚠️  Key length seems short: {len(api_key)} characters")
        else:
            self.log(f"   Key length: {len(api_key)} characters")

        return True

    def check_configuration_loading(self) -> bool:
        """Step 3: Load and validate configuration"""
        self.print_step(3, "Configuration Loading")

        try:
            self.config = DeepSeekConfig()
            self.print_result(True, "Configuration loaded successfully")

            # Display configuration
            self.log(f"   Base URL: {self.config.base_url}")
            self.log(f"   Model: {self.config.model}")
            self.log(f"   Timeout: {self.config.timeout}s")
            self.log(f"   API Key: {self.mask_api_key(self.config.api_key)}")

            # Override model if test model specified
            if self.test_model:
                self.config.model = self.test_model
                self.log(f"   ⚠️  Test model override: {self.test_model}")

            return True

        except Exception as e:
            self.print_result(False, f"Configuration loading failed: {e}")
            return False

    def check_network_connectivity(self) -> bool:
        """Step 4: Test network connectivity"""
        self.print_step(4, "Network Connectivity")

        if not REQUESTS_AVAILABLE:
            self.print_result(False, "requests library not available")
            self.log("💡 Install: pip install requests")
            return False

        try:
            response = requests.get("https://api.deepseek.com", timeout=10)
            self.print_result(True, f"Connected to api.deepseek.com (HTTP {response.status_code})")
            return True

        except requests.exceptions.ConnectionError:
            self.print_result(False, "Connection failed - check internet/firewall")
            return False
        except requests.exceptions.Timeout:
            self.print_result(False, "Connection timeout")
            return False
        except Exception as e:
            self.print_result(False, f"Network error: {e}")
            return False

    def check_api_authentication(self) -> bool:
        """Step 5: Test API authentication"""
        self.print_step(5, "API Authentication Test")

        url = f"{self.config.base_url}/models"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(url, headers=headers, timeout=self.config.timeout)

            if response.status_code == 200:
                data = response.json()
                model_count = len(data.get("data", []))
                self.print_result(True, "API key authenticated successfully")
                self.log(f"   Available models: {model_count}")
                return True
            elif response.status_code == 401:
                self.print_result(False, "Authentication failed - invalid API key")
                return False
            else:
                self.print_result(False, f"Authentication failed: HTTP {response.status_code}")
                self.log(f"   Response: {response.text[:200]}")
                return False

        except Exception as e:
            self.print_result(False, f"Authentication error: {e}")
            return False

    def check_model_availability(self) -> bool:
        """Step 6: Check if model is available"""
        self.print_step(6, "Model Availability Check")

        url = f"{self.config.base_url}/models"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(url, headers=headers, timeout=self.config.timeout)

            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])

                # Look for the specific model
                model_found = None
                for model in models:
                    if model.get("id") == self.config.model:
                        model_found = model
                        break

                if model_found:
                    self.print_result(True, f"Model '{self.config.model}' is available")
                    return True
                else:
                    self.print_result(False, f"Model '{self.config.model}' not found")
                    # List available models
                    available_models = [m.get("id") for m in models[:5]]
                    self.log(f"   Available models: {', '.join(available_models)}")
                    return False
            else:
                self.print_result(False, f"Failed to fetch models: HTTP {response.status_code}")
                return False

        except Exception as e:
            self.print_result(False, f"Model check error: {e}")
            return False

    def check_chat_completion_basic(self) -> bool:
        """Step 7: Test basic chat completion"""
        self.print_step(7, "Basic Chat Completion Test")

        url = f"{self.config.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "user", "content": "Say 'test successful' in exactly 3 words."}
            ],
            "max_tokens": 20,
            "temperature": 0.0
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.config.timeout)

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                usage = data.get("usage", {})

                self.print_result(True, "Chat completion successful")
                self.log(f"   Response: {content[:100]}")
                self.log(f"   Tokens used: {usage.get('total_tokens', 'N/A')}")

                # Calculate cost
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)
                cost = (input_tokens * 0.27 / 1_000_000) + (output_tokens * 1.10 / 1_000_000)
                self.log(f"   Estimated cost: ${cost:.6f}")

                return True
            else:
                self.print_result(False, f"Chat completion failed: HTTP {response.status_code}")
                self.log(f"   Error: {response.text[:200]}")
                return False

        except Exception as e:
            self.print_result(False, f"Chat completion error: {e}")
            return False

    def check_json_mode_support(self) -> bool:
        """Step 8: Test JSON mode support"""
        self.print_step(8, "JSON Mode Support Test")

        url = f"{self.config.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a JSON generator. Return only valid JSON, no other text."
                },
                {
                    "role": "user",
                    "content": 'Return this exact JSON: {"status": "ok", "message": "test", "number": 42}'
                }
            ],
            "response_format": {"type": "json_object"},  # JSON mode
            "max_tokens": 100,
            "temperature": 0.0
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.config.timeout)

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                # Try to parse as JSON
                try:
                    json_content = json.loads(content.strip())
                    self.print_result(True, "JSON mode supported and working")
                    self.log(f"   Parsed JSON: {json_content}")
                    return True
                except json.JSONDecodeError:
                    self.print_result(False, "JSON mode failed to return valid JSON")
                    self.log(f"   Response: {content[:200]}")
                    return False
            else:
                self.print_result(False, f"JSON mode test failed: HTTP {response.status_code}")
                self.log(f"   Error: {response.text[:200]}")
                return False

        except Exception as e:
            self.print_result(False, f"JSON mode error: {e}")
            return False

    def check_legal_event_extraction(self) -> bool:
        """Step 9: Test legal event extraction"""
        self.print_step(9, "Legal Event Extraction Test")

        url = f"{self.config.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        legal_text = """
        Settlement Agreement signed on March 15, 2024. The plaintiff and defendant
        reached a mutual settlement for $500,000. Final hearing scheduled for April 1, 2024.
        """

        payload = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "system",
                    "content": LEGAL_EVENTS_PROMPT + "\n\nReturn your response as valid JSON array containing the extracted events."
                },
                {
                    "role": "user",
                    "content": f"Extract legal events from this document and return as JSON:\n\n{legal_text}"
                }
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0,
            "max_tokens": 500
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.config.timeout)

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                # Try to parse as JSON
                try:
                    events_data = json.loads(content)

                    # Handle both array and object responses
                    if isinstance(events_data, dict):
                        if "events" in events_data:
                            events_data = events_data["events"]
                        elif "extractions" in events_data:
                            events_data = events_data["extractions"]

                    if isinstance(events_data, list):
                        self.print_result(True, f"Legal event extraction successful")
                        self.log(f"   Extracted {len(events_data)} events")
                        return True
                    else:
                        self.print_result(False, "Response is not a JSON array")
                        self.log(f"   Response type: {type(events_data)}")
                        return False

                except json.JSONDecodeError as e:
                    self.print_result(False, f"Failed to parse JSON: {e}")
                    self.log(f"   Response: {content[:300]}")
                    return False
            else:
                self.print_result(False, f"Legal extraction failed: HTTP {response.status_code}")
                self.log(f"   Error: {response.text[:200]}")
                return False

        except Exception as e:
            self.print_result(False, f"Legal extraction error: {e}")
            return False

    def check_rate_limiting(self) -> bool:
        """Step 10: Test dynamic rate limiting behavior"""
        self.print_step(10, "Dynamic Rate Limiting Test")

        self.log("   DeepSeek uses dynamic rate limiting (no fixed RPM)")
        self.log("   Making 3 rapid requests to observe behavior...")

        url = f"{self.config.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 5,
            "temperature": 0.0
        }

        import time
        response_times = []
        rate_limited = False

        for i in range(3):
            try:
                start = time.time()
                response = requests.post(url, headers=headers, json=payload, timeout=self.config.timeout)
                elapsed = time.time() - start

                if response.status_code == 429:
                    rate_limited = True
                    self.log(f"   Request {i+1}: Rate limited (429)")
                elif response.status_code == 200:
                    response_times.append(elapsed)
                    self.log(f"   Request {i+1}: {elapsed:.2f}s")

                time.sleep(0.5)  # Small delay between requests

            except Exception as e:
                self.log(f"   Request {i+1}: Error - {e}")

        if rate_limited:
            self.print_result(True, "Rate limiting detected (normal behavior)")
            self.log("   💡 DeepSeek throttles requests during high load")
        elif response_times:
            avg_time = sum(response_times) / len(response_times)
            self.print_result(True, f"Rate limiting working (avg: {avg_time:.2f}s)")
            self.log("   💡 Response times may increase during peak usage")
        else:
            self.print_result(False, "Could not test rate limiting")

        return True  # This check always passes (informational only)

    def print_summary(self):
        """Print diagnostic summary"""
        self.log("\n" + "=" * 70)
        self.log("📊 DIAGNOSTIC SUMMARY")
        self.log("=" * 70)

        success_rate = (self.checks_passed / self.total_checks) * 100
        self.log(f"Checks Passed: {self.checks_passed}/{self.total_checks} ({success_rate:.1f}%)")
        self.log("")

        if self.checks_passed == self.total_checks:
            self.log("✅ ALL CHECKS PASSED - DeepSeek Direct API is properly configured!")
            self.log("")
            self.log("💡 Next steps:")
            self.log("   1. Ready to use in Streamlit: Select 'DeepSeek (Direct API)' in UI")
            self.log("   2. Monitor usage at: https://platform.deepseek.com")
            self.log("   3. Cost tracking: $0.27/M input, $1.10/M output")
            self.log("")
        elif self.checks_passed >= 7:
            self.log("⚠️ MOSTLY WORKING - Minor issues to address")
            self.log("")
            self.log("💡 Recommendations:")
            self.log("   - Review failed checks above")
            self.log("   - Verify API key is correct")
            self.log("")
        else:
            self.log("❌ MULTIPLE ISSUES - Configuration needs attention")
            self.log("")
            self.log("💡 Troubleshooting:")
            self.log("   - Verify DEEPSEEK_API_KEY is correct")
            self.log("   - Check network connectivity")
            self.log("   - Get API key from: https://platform.deepseek.com")
            self.log("")

        self.log(f"📄 Detailed log saved to: {self.log_file}")
        self.log("=" * 70)

    def run_all_checks(self) -> int:
        """Run all diagnostic checks"""
        self.print_header()

        checks = [
            self.check_environment_file,
            self.check_api_key_format,
            self.check_configuration_loading,
            self.check_network_connectivity,
            self.check_api_authentication,
            self.check_model_availability,
            self.check_chat_completion_basic,
            self.check_json_mode_support,
            self.check_legal_event_extraction,
            self.check_rate_limiting
        ]

        for check in checks:
            try:
                check()
            except Exception as e:
                self.log(f"❌ Check failed with exception: {e}")
                import traceback
                self.log(traceback.format_exc())

        self.print_summary()

        # Return exit code
        if self.checks_passed == self.total_checks:
            return 0  # Success
        elif self.checks_passed >= 7:
            return 1  # Partial success
        else:
            return 2  # Critical failures


def main():
    parser = argparse.ArgumentParser(
        description="DeepSeek Direct API diagnostic tool"
    )
    parser.add_argument(
        "--test-model",
        help="Override model to test (default: deepseek-chat)",
        default=None
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    diagnostic = DeepSeekDiagnostic(
        test_model=args.test_model,
        verbose=args.verbose
    )

    exit_code = diagnostic.run_all_checks()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
