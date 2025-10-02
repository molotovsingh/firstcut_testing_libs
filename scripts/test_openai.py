#!/usr/bin/env python3
"""
OpenAI Configuration Diagnostic Script
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
from src.core.config import OpenAIConfig, env_str

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class OpenAIDiagnostic:
    """Comprehensive OpenAI configuration validation"""

    def __init__(self, test_model: Optional[str] = None, verbose: bool = False):
        self.test_model = test_model
        self.verbose = verbose
        self.checks_passed = 0
        self.total_checks = 10
        self.config = None
        self.api_key_safe = None
        self.log_file = Path(__file__).parent / "openai_diagnostic.log"

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
        self.log("🔍 OpenAI Configuration Diagnostic")
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

        api_key = os.getenv("OPENAI_API_KEY", "")

        if not api_key:
            self.print_result(False, "OPENAI_API_KEY not set in .env")
            self.log("💡 Get API key from: https://platform.openai.com/api-keys")
            self.log("💡 Add to .env: OPENAI_API_KEY=sk-...")
            return False

        # Check for whitespace
        if api_key != api_key.strip():
            self.print_result(False, "API key contains leading/trailing whitespace")
            return False

        self.api_key_safe = self.mask_api_key(api_key)
        self.print_result(True, f"API key found: {self.api_key_safe}")

        # Check expected format (OpenAI keys typically start with sk-)
        if api_key.startswith("sk-"):
            self.log(f"   Key format: Valid OpenAI format (sk-)")
        elif api_key.startswith("sk-proj-"):
            self.log(f"   Key format: Valid OpenAI project key (sk-proj-)")
        else:
            self.log(f"   ⚠️  Key format: Unexpected format (expected sk- or sk-proj-)")

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
            self.config = OpenAIConfig()
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
            response = requests.get("https://api.openai.com", timeout=10)
            self.print_result(True, f"Connected to api.openai.com (HTTP {response.status_code})")
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

    def check_api_authentication(self) -> Tuple[bool, Optional[Dict]]:
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
                self.print_result(True, f"Authentication successful (HTTP {response.status_code})")
                models_data = response.json()
                self.log(f"   Available models: {len(models_data.get('data', []))}")
                return True, models_data

            elif response.status_code == 401:
                self.print_result(False, "Authentication failed - Invalid API key")
                self.log("💡 Verify API key at: https://platform.openai.com/api-keys")
                return False, None

            elif response.status_code == 429:
                self.print_result(False, "Rate limit exceeded")
                return False, None

            else:
                self.print_result(False, f"Authentication failed (HTTP {response.status_code})")
                self.log(f"   Response: {response.text[:200]}")
                return False, None

        except requests.exceptions.Timeout:
            self.print_result(False, f"Request timeout ({self.config.timeout}s)")
            return False, None
        except Exception as e:
            self.print_result(False, f"Authentication error: {e}")
            return False, None

    def check_model_availability(self, models_data: Optional[Dict]) -> bool:
        """Step 6: Check if configured model is available"""
        self.print_step(6, "Model Availability Check")

        if not models_data:
            self.print_result(False, "No models data available from previous step")
            return False

        model_list = models_data.get("data", [])
        model_ids = [m.get("id") for m in model_list if m.get("id")]

        # Check if configured model is available
        if self.config.model in model_ids:
            self.print_result(True, f"Model '{self.config.model}' is available")

            # Check if model supports JSON mode
            json_compatible = ["gpt-4o", "gpt-4-turbo", "gpt-4-1106", "gpt-4-0125", "gpt-3.5-turbo-1106", "gpt-3.5-turbo-0125"]
            if any(compatible in self.config.model for compatible in json_compatible):
                self.log(f"   ✅ Model supports native JSON mode (response_format)")
            else:
                self.log(f"   ⚠️  Model may not support native JSON mode")

            return True

        else:
            self.print_result(False, f"Model '{self.config.model}' not found in available models")
            self.log("   💡 Available GPT models:")
            gpt_models = [m for m in model_ids if "gpt" in m.lower()][:10]
            for model in gpt_models:
                self.log(f"      - {model}")
            return False

    def check_minimal_chat_completion(self) -> bool:
        """Step 7: Test minimal chat completion"""
        self.print_step(7, "Minimal Chat Completion Test")

        url = f"{self.config.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 10,
            "temperature": 0.0
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.config.timeout)

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                tokens = data.get("usage", {}).get("total_tokens", 0)
                self.print_result(True, f"Chat completion successful ({tokens} tokens)")
                self.log(f"   Response: {content}")
                return True

            else:
                self.print_result(False, f"Chat completion failed (HTTP {response.status_code})")
                self.log(f"   Response: {response.text[:200]}")
                return False

        except Exception as e:
            self.print_result(False, f"Chat completion error: {e}")
            return False

    def check_json_response_format(self) -> bool:
        """Step 8: Test JSON response format (required for legal extraction)"""
        self.print_step(8, "JSON Response Format Test")

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
                    "content": "Extract events as JSON array. Return valid JSON only."
                },
                {
                    "role": "user",
                    "content": "Contract signed on March 15, 2024."
                }
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.config.timeout)

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                # Try to parse as JSON
                try:
                    parsed = json.loads(content)
                    self.print_result(True, "JSON response format working correctly")
                    self.log(f"   Parsed JSON: {json.dumps(parsed, indent=2)[:200]}")
                    return True
                except json.JSONDecodeError as e:
                    self.print_result(False, f"Response is not valid JSON: {e}")
                    self.log(f"   Response: {content[:200]}")
                    return False

            elif response.status_code == 400:
                error_msg = response.json().get("error", {}).get("message", "Unknown error")
                if "response_format" in error_msg.lower():
                    self.print_result(False, f"Model does not support JSON mode: {error_msg}")
                    self.log("   💡 Use a model that supports response_format: gpt-4o, gpt-4-turbo, gpt-3.5-turbo-1106+")
                else:
                    self.print_result(False, f"Bad request: {error_msg}")
                return False

            else:
                self.print_result(False, f"JSON format test failed (HTTP {response.status_code})")
                self.log(f"   Response: {response.text[:200]}")
                return False

        except Exception as e:
            self.print_result(False, f"JSON format test error: {e}")
            return False

    def check_rate_limits(self) -> bool:
        """Step 9: Check rate limit information"""
        self.print_step(9, "Rate Limit Information")

        url = f"{self.config.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": "Test"}],
            "max_tokens": 5
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.config.timeout)

            # Extract rate limit headers
            rate_limit_headers = {
                "requests_limit": response.headers.get("x-ratelimit-limit-requests"),
                "requests_remaining": response.headers.get("x-ratelimit-remaining-requests"),
                "tokens_limit": response.headers.get("x-ratelimit-limit-tokens"),
                "tokens_remaining": response.headers.get("x-ratelimit-remaining-tokens"),
            }

            if any(rate_limit_headers.values()):
                self.print_result(True, "Rate limit information retrieved")
                self.log(f"   Requests Limit: {rate_limit_headers['requests_limit']}")
                self.log(f"   Requests Remaining: {rate_limit_headers['requests_remaining']}")
                self.log(f"   Tokens Limit: {rate_limit_headers['tokens_limit']}")
                self.log(f"   Tokens Remaining: {rate_limit_headers['tokens_remaining']}")
                return True
            else:
                self.print_result(True, "No rate limit headers found (tier-based limits may apply)")
                self.log("   💡 Check your tier at: https://platform.openai.com/settings/organization/limits")
                return True

        except Exception as e:
            self.print_result(False, f"Rate limit check error: {e}")
            return False

    def check_full_integration(self) -> bool:
        """Step 10: Test full legal events extraction integration"""
        self.print_step(10, "Full Legal Events Extraction Test")

        try:
            # Import adapter
            from src.core.openai_adapter import OpenAIEventExtractor

            # Create extractor
            extractor = OpenAIEventExtractor(self.config)

            if not extractor.is_available():
                self.print_result(False, "OpenAI adapter not available")
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

                return True
            else:
                self.print_result(False, "No legal events extracted")
                return False

        except ImportError as e:
            self.print_result(False, f"Import error: {e}")
            self.log("   💡 Ensure openai library is installed: pip install openai")
            return False
        except Exception as e:
            self.print_result(False, f"Integration test failed: {e}")
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
        ]

        # API authentication (returns models data)
        auth_passed, models_data = self.check_api_authentication()
        checks.append(auth_passed)

        # Model availability check (needs models data)
        checks.append(self.check_model_availability(models_data))

        # Remaining checks
        checks.extend([
            self.check_minimal_chat_completion(),
            self.check_json_response_format(),
            self.check_rate_limits(),
            self.check_full_integration(),
        ])

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
            self.log("✅ OpenAI configuration is fully operational!")
            self.log("   You can use 'openai' as EVENT_EXTRACTOR in your .env file")
        elif pass_rate >= 70:
            self.log("⚠️  OpenAI configuration has some issues")
            self.log("   Review the failed checks above and fix the configuration")
        else:
            self.log("❌ OpenAI configuration has critical issues")
            self.log("   Fix the failed checks before using OpenAI extractor")

        self.log(f"\n💾 Full diagnostic log: {self.log_file}")
        self.log("=" * 70)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="OpenAI Configuration Diagnostic Tool")
    parser.add_argument(
        "--model",
        type=str,
        help="Test with specific model (overrides OPENAI_MODEL env var)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose debug logging",
    )

    args = parser.parse_args()

    diagnostic = OpenAIDiagnostic(test_model=args.model, verbose=args.verbose)
    success = diagnostic.run_diagnostics()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
