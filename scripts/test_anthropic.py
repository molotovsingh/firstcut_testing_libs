#!/usr/bin/env python3
"""
Anthropic Configuration Diagnostic Script
Validates API key, configuration, and connectivity with detailed error reporting
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
from src.core.config import AnthropicConfig, env_str

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class AnthropicDiagnostic:
    """Comprehensive Anthropic configuration validation"""

    def __init__(self, test_model: Optional[str] = None, verbose: bool = False):
        self.test_model = test_model
        self.verbose = verbose
        self.checks_passed = 0
        self.total_checks = 10
        self.config = None
        self.api_key_safe = None
        self.log_file = Path(__file__).parent / "anthropic_diagnostic.log"

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
        return f"{api_key[:12]}...{api_key[-8:]}"

    def print_header(self):
        """Print diagnostic header"""
        self.log("=" * 70)
        self.log("🔍 Anthropic Configuration Diagnostic")
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

        api_key = os.getenv("ANTHROPIC_API_KEY", "")

        if not api_key:
            self.print_result(False, "ANTHROPIC_API_KEY not set in .env")
            self.log("💡 Get API key from: https://console.anthropic.com/settings/keys")
            self.log("💡 Add to .env: ANTHROPIC_API_KEY=sk-ant-api03-...")
            return False

        # Check for whitespace
        if api_key != api_key.strip():
            self.print_result(False, "API key contains leading/trailing whitespace")
            return False

        self.api_key_safe = self.mask_api_key(api_key)
        self.print_result(True, f"API key found: {self.api_key_safe}")

        # Check expected format (Anthropic keys start with sk-ant-api03-)
        if api_key.startswith("sk-ant-api03-"):
            self.log(f"   Key format: Valid Anthropic format (sk-ant-api03-)")
        elif api_key.startswith("sk-ant-"):
            self.log(f"   Key format: Valid Anthropic format (sk-ant-)")
        else:
            self.log(f"   ⚠️  Key format: Unexpected format (expected sk-ant-api03- or sk-ant-)")

        # Check length
        if len(api_key) < 40:
            self.log(f"   ⚠️  Key length seems short: {len(api_key)} characters")
        else:
            self.log(f"   Key length: {len(api_key)} characters")

        return True

    def check_configuration_loading(self) -> bool:
        """Step 3: Load and validate configuration"""
        self.print_step(3, "Configuration Loading")

        try:
            self.config = AnthropicConfig()
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
            response = requests.get("https://api.anthropic.com", timeout=10)
            self.print_result(True, f"Connected to api.anthropic.com (HTTP {response.status_code})")
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

        # Anthropic doesn't have a /models endpoint, so we test with minimal message
        url = f"{self.config.base_url}/v1/messages"
        headers = {
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.config.model,
            "max_tokens": 10,
            "messages": [{"role": "user", "content": "Hello"}]
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.config.timeout)

            if response.status_code == 200:
                self.print_result(True, f"Authentication successful (HTTP {response.status_code})")
                return True

            elif response.status_code == 401:
                self.print_result(False, "Authentication failed - Invalid API key")
                self.log("💡 Verify API key at: https://console.anthropic.com/settings/keys")
                return False

            elif response.status_code == 429:
                self.print_result(False, "Rate limit exceeded")
                return False

            else:
                self.print_result(False, f"Authentication failed (HTTP {response.status_code})")
                self.log(f"   Response: {response.text[:200]}")
                return False

        except requests.exceptions.Timeout:
            self.print_result(False, f"Request timeout ({self.config.timeout}s)")
            return False
        except Exception as e:
            self.print_result(False, f"Authentication error: {e}")
            return False

    def check_model_availability(self) -> bool:
        """Step 6: Check if configured model works"""
        self.print_step(6, "Model Availability Check")

        # List of known Claude models
        known_models = [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]

        # Check if configured model is known
        model_known = any(known in self.config.model for known in known_models)

        if model_known:
            self.print_result(True, f"Model '{self.config.model}' is a known Claude model")
            self.log(f"   ✅ All Claude models support tool calling for structured JSON")
            return True
        else:
            self.print_result(True, f"Model '{self.config.model}' will be tested")
            self.log(f"   ⚠️  Model not in known list, will validate with API call")
            self.log(f"   💡 Known Claude models: {', '.join(known_models[:3])}")
            return True

    def check_minimal_message_completion(self) -> bool:
        """Step 7: Test minimal message completion"""
        self.print_step(7, "Minimal Message Completion Test")

        url = f"{self.config.base_url}/v1/messages"
        headers = {
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.config.model,
            "max_tokens": 20,
            "messages": [{"role": "user", "content": "Say 'Hello' in 1 word"}],
            "temperature": 0.0
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.config.timeout)

            if response.status_code == 200:
                data = response.json()
                content = data.get("content", [{}])[0].get("text", "")
                input_tokens = data.get("usage", {}).get("input_tokens", 0)
                output_tokens = data.get("usage", {}).get("output_tokens", 0)
                total_tokens = input_tokens + output_tokens

                self.print_result(True, f"Message completion successful ({total_tokens} tokens)")
                self.log(f"   Response: {content}")
                self.log(f"   Tokens: {input_tokens} in + {output_tokens} out = {total_tokens} total")
                return True

            else:
                self.print_result(False, f"Message completion failed (HTTP {response.status_code})")
                self.log(f"   Response: {response.text[:200]}")
                return False

        except Exception as e:
            self.print_result(False, f"Message completion error: {e}")
            return False

    def check_tool_use_pattern(self) -> bool:
        """Step 8: Test tool use pattern (Anthropic's JSON enforcement)"""
        self.print_step(8, "Tool Use Pattern Test (JSON Enforcement)")

        url = f"{self.config.base_url}/v1/messages"
        headers = {
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

        # Define a simple tool for testing
        tools = [{
            "name": "extract_info",
            "description": "Extract information from text",
            "input_schema": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "The date mentioned"},
                    "event": {"type": "string", "description": "The event described"}
                },
                "required": ["date", "event"]
            }
        }]

        payload = {
            "model": self.config.model,
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": "Extract the date and event: Contract signed on March 15, 2024."
                }
            ],
            "tools": tools,
            "tool_choice": {"type": "tool", "name": "extract_info"},
            "temperature": 0.0
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.config.timeout)

            if response.status_code == 200:
                data = response.json()
                content = data.get("content", [])

                # Find tool use block
                tool_use_block = None
                for block in content:
                    if block.get("type") == "tool_use":
                        tool_use_block = block
                        break

                if tool_use_block:
                    tool_input = tool_use_block.get("input", {})
                    self.print_result(True, "Tool use pattern working correctly")
                    self.log(f"   Tool input: {json.dumps(tool_input, indent=2)[:200]}")
                    self.log(f"   ✅ Anthropic enforces JSON structure via tool calling")
                    return True
                else:
                    self.print_result(False, "No tool_use block found in response")
                    self.log(f"   Response: {json.dumps(data, indent=2)[:200]}")
                    return False

            elif response.status_code == 400:
                error = response.json().get("error", {})
                error_msg = error.get("message", "Unknown error")
                self.print_result(False, f"Tool use test failed: {error_msg}")
                self.log(f"   Error type: {error.get('type')}")
                return False

            else:
                self.print_result(False, f"Tool use test failed (HTTP {response.status_code})")
                self.log(f"   Response: {response.text[:200]}")
                return False

        except Exception as e:
            self.print_result(False, f"Tool use test error: {e}")
            return False

    def check_rate_limits(self) -> bool:
        """Step 9: Check rate limit information"""
        self.print_step(9, "Rate Limit Information")

        url = f"{self.config.base_url}/v1/messages"
        headers = {
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.config.model,
            "max_tokens": 5,
            "messages": [{"role": "user", "content": "Test"}]
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.config.timeout)

            # Anthropic rate limit headers (if present)
            rate_limit_headers = {
                "requests_limit": response.headers.get("anthropic-ratelimit-requests-limit"),
                "requests_remaining": response.headers.get("anthropic-ratelimit-requests-remaining"),
                "requests_reset": response.headers.get("anthropic-ratelimit-requests-reset"),
                "tokens_limit": response.headers.get("anthropic-ratelimit-tokens-limit"),
                "tokens_remaining": response.headers.get("anthropic-ratelimit-tokens-remaining"),
                "tokens_reset": response.headers.get("anthropic-ratelimit-tokens-reset"),
            }

            if any(rate_limit_headers.values()):
                self.print_result(True, "Rate limit information retrieved")
                if rate_limit_headers["requests_limit"]:
                    self.log(f"   Requests Limit: {rate_limit_headers['requests_limit']}")
                    self.log(f"   Requests Remaining: {rate_limit_headers['requests_remaining']}")
                    self.log(f"   Requests Reset: {rate_limit_headers['requests_reset']}")
                if rate_limit_headers["tokens_limit"]:
                    self.log(f"   Tokens Limit: {rate_limit_headers['tokens_limit']}")
                    self.log(f"   Tokens Remaining: {rate_limit_headers['tokens_remaining']}")
                    self.log(f"   Tokens Reset: {rate_limit_headers['tokens_reset']}")
                return True
            else:
                self.print_result(True, "No rate limit headers found (tier-based limits may apply)")
                self.log("   💡 Check your limits at: https://console.anthropic.com/settings/limits")
                return True

        except Exception as e:
            self.print_result(False, f"Rate limit check error: {e}")
            return False

    def check_full_integration(self) -> bool:
        """Step 10: Test full legal events extraction integration"""
        self.print_step(10, "Full Legal Events Extraction Test")

        try:
            # Import adapter
            from src.core.anthropic_adapter import AnthropicEventExtractor

            # Create extractor
            extractor = AnthropicEventExtractor(self.config)

            if not extractor.is_available():
                self.print_result(False, "Anthropic adapter not available")
                return False

            # Test legal events extraction
            test_text = """
            This Lease Agreement is entered into on September 21, 2024, between John Doe (Landlord)
            and Jane Smith (Tenant). The lease term begins on October 1, 2024 and continues for
            twelve (12) months. Rent is due on the 5th of each month. A security deposit of $2,000
            was paid on September 15, 2024. Per Section 8.2 of the Residential Tenancies Act 2010,
            the landlord must provide 24 hours notice before entry.
            """

            metadata = {"document_name": "test_lease_agreement.pdf"}
            events = extractor.extract_events(test_text, metadata)

            if events and len(events) > 0:
                self.print_result(True, f"Legal events extraction successful ({len(events)} events)")

                # Display first event
                first_event = events[0]
                self.log(f"   Sample Event:")
                self.log(f"      Date: {first_event.date}")
                self.log(f"      Event: {first_event.event_particulars[:100]}...")
                self.log(f"      Citation: {first_event.citation}")
                self.log(f"      Document: {first_event.document_reference}")

                # Display cost info if available
                if hasattr(extractor, '_total_cost') and extractor._total_cost > 0:
                    self.log(f"   Cost: ${extractor._total_cost:.4f}")

                return True
            else:
                self.print_result(False, "No legal events extracted")
                return False

        except ImportError as e:
            self.print_result(False, f"Import error: {e}")
            self.log("   💡 Ensure anthropic library is installed: pip install anthropic")
            return False
        except Exception as e:
            self.print_result(False, f"Integration test failed: {e}")
            import traceback
            self.log(f"   Error details: {traceback.format_exc()}")
            return False

    def run_diagnostics(self) -> bool:
        """Run all diagnostic checks"""
        self.print_header()

        # Run all checks in sequence
        checks = [
            self.check_environment_file(),
            self.check_api_key_format(),
            self.check_configuration_loading(),
            self.check_network_connectivity(),
            self.check_api_authentication(),
            self.check_model_availability(),
            self.check_minimal_message_completion(),
            self.check_tool_use_pattern(),
            self.check_rate_limits(),
            self.check_full_integration(),
        ]

        # Print summary
        self.print_summary()

        return self.checks_passed == self.total_checks

    def print_summary(self):
        """Print diagnostic summary"""
        self.log("\n" + "=" * 70)
        self.log("📊 Diagnostic Summary")
        self.log("=" * 70)

        pass_rate = (self.checks_passed / self.total_checks) * 100
        status_icon = "✅" if pass_rate == 100 else ("⚠️" if pass_rate >= 70 else "❌")

        self.log(f"{status_icon} Checks Passed: {self.checks_passed}/{self.total_checks} ({pass_rate:.0f}%)")

        if self.checks_passed == self.total_checks:
            self.log("✅ Anthropic configuration is fully operational!")
            self.log("   You can use 'anthropic' as EVENT_EXTRACTOR in your .env file")
        elif pass_rate >= 70:
            self.log("⚠️  Anthropic configuration has some issues")
            self.log("   Review the failed checks above and fix the configuration")
        else:
            self.log("❌ Anthropic configuration has critical issues")
            self.log("   Fix the failed checks before using Anthropic extractor")

        self.log(f"\n💾 Full diagnostic log: {self.log_file}")
        self.log("=" * 70)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Anthropic Configuration Diagnostic Tool")
    parser.add_argument(
        "--model",
        type=str,
        help="Test with specific model (overrides ANTHROPIC_MODEL env var)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose debug logging",
    )

    args = parser.parse_args()

    diagnostic = AnthropicDiagnostic(test_model=args.model, verbose=args.verbose)
    success = diagnostic.run_diagnostics()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
