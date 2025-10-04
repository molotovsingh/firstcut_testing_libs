#!/usr/bin/env python3
"""
DeepSeek via OpenRouter Diagnostic Script
Tests DeepSeek R1 Distill compatibility for legal event extraction
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from dotenv import load_dotenv
from src.core.config import OpenRouterConfig, env_str
from src.core.constants import LEGAL_EVENTS_PROMPT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class DeepSeekDiagnostic:
    """Comprehensive DeepSeek R1 Distill configuration validation"""

    def __init__(self, test_model: Optional[str] = None, verbose: bool = False):
        self.test_model = test_model or "deepseek/deepseek-r1-distill-llama-70b"
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

    def log(self, message: str):
        """Log message to both console and file"""
        logger.info(message)

    def print_header(self):
        """Print diagnostic header"""
        print("=" * 70)
        print("🧠 DeepSeek R1 Distill Configuration Diagnostic")
        print("=" * 70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Log file: {self.log_file}")
        print("=" * 70)
        print()

    def print_step(self, step: int, title: str):
        """Print step header"""
        msg = f"\n[Step {step}/{self.total_checks}] {title}"
        print(msg)
        print("-" * 50)
        self.log(msg)

    def print_result(self, success: bool, message: str):
        """Print check result"""
        icon = "✅" if success else "❌"
        print(f"{icon} {message}")
        if success:
            self.checks_passed += 1

    def mask_key(self, key: str) -> str:
        """Mask API key for safe display"""
        if not key or len(key) < 12:
            return "***"
        return f"{key[:10]}...{key[-8:]}"

    def check_environment_file(self) -> bool:
        """Step 1: Check if .env file exists"""
        self.print_step(1, "Environment File Check")

        env_path = Path.cwd() / ".env"
        if env_path.exists():
            self.print_result(True, f".env file found at {env_path}")
            load_dotenv()
            self.log(f"   Loaded environment variables from {env_path}")
            return True
        else:
            self.print_result(False, f".env file not found at {env_path}")
            self.log("   Create a .env file with OPENROUTER_API_KEY")
            return False

    def check_api_key_format(self) -> bool:
        """Step 2: Validate API key format"""
        self.print_step(2, "API Key Format Validation")

        api_key = os.getenv("OPENROUTER_API_KEY", "")

        if not api_key:
            self.print_result(False, "OPENROUTER_API_KEY not found in environment")
            return False

        self.api_key_safe = self.mask_key(api_key)

        # Check format
        if not api_key.startswith("sk-or-v1-"):
            self.print_result(False, f"Invalid key format: {self.api_key_safe}")
            self.log("   Expected format: sk-or-v1-...")
            return False

        if len(api_key) < 40:
            self.print_result(False, f"Key too short: {len(api_key)} characters")
            return False

        if api_key != api_key.strip():
            self.print_result(False, "Key contains leading/trailing whitespace")
            return False

        self.print_result(True, f"API key found: {self.api_key_safe}")
        self.log(f"   Key format: Valid OpenRouter format (sk-or-v1-)")
        self.log(f"   Key length: {len(api_key)} characters")
        return True

    def check_configuration_loading(self) -> bool:
        """Step 3: Load OpenRouter configuration"""
        self.print_step(3, "Configuration Loading")

        try:
            self.config = OpenRouterConfig()

            # Override model if specified
            if self.test_model:
                self.config.model = self.test_model

            self.print_result(True, "Configuration loaded successfully")
            self.log(f"   Base URL: {self.config.base_url}")
            self.log(f"   Model: {self.config.model}")
            self.log(f"   Timeout: {self.config.timeout}s")
            self.log(f"   API Key: {self.api_key_safe}")
            return True

        except Exception as e:
            self.print_result(False, f"Configuration loading failed: {e}")
            return False

    def check_network_connectivity(self) -> bool:
        """Step 4: Test network connectivity to OpenRouter"""
        self.print_step(4, "Network Connectivity")

        if not REQUESTS_AVAILABLE:
            self.print_result(False, "requests library not available")
            return False

        try:
            response = requests.get("https://openrouter.ai", timeout=10)
            self.print_result(True, f"Connected to openrouter.ai (HTTP {response.status_code})")
            return True
        except Exception as e:
            self.print_result(False, f"Connection failed: {e}")
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
            else:
                self.print_result(False, f"Authentication failed: HTTP {response.status_code}")
                self.log(f"   Response: {response.text[:200]}")
                return False

        except Exception as e:
            self.print_result(False, f"Authentication error: {e}")
            return False

    def check_model_availability(self) -> bool:
        """Step 6: Check if DeepSeek model is available"""
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

                    # Extract pricing info
                    pricing = model_found.get("pricing", {})
                    prompt_price = pricing.get("prompt")
                    completion_price = pricing.get("completion")

                    if prompt_price and completion_price:
                        self.log(f"   Prompt: ${float(prompt_price)} per token")
                        self.log(f"   Completion: ${float(completion_price)} per token")

                    return True
                else:
                    self.print_result(False, f"Model '{self.config.model}' not found")

                    # Suggest alternatives
                    deepseek_models = [m["id"] for m in models if "deepseek" in m["id"].lower()]
                    if deepseek_models:
                        self.log("\n   Available DeepSeek models:")
                        for dm in deepseek_models[:5]:
                            self.log(f"   - {dm}")

                    return False
            else:
                self.print_result(False, f"Failed to fetch models: HTTP {response.status_code}")
                return False

        except Exception as e:
            self.print_result(False, f"Model check error: {e}")
            return False

    def check_chat_completion_basic(self) -> bool:
        """Step 7: Test basic chat completion (NO response_format)"""
        self.print_step(7, "Basic Chat Completion Test (No response_format)")

        url = f"{self.config.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "user", "content": "Say 'test successful' in 3 words."}
            ],
            "max_tokens": 20,
            "temperature": 0.0
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.config.timeout
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                self.print_result(True, "Chat completion successful")
                self.log(f"   Response: {content[:100]}")

                usage = data.get("usage", {})
                if usage:
                    self.log(f"   Tokens used: {usage.get('total_tokens', 'N/A')}")

                return True
            else:
                self.print_result(False, f"Chat completion failed: HTTP {response.status_code}")
                self.log(f"   Error: {response.text[:200]}")
                return False

        except Exception as e:
            self.print_result(False, f"Chat completion error: {e}")
            return False

    def check_json_via_prompt(self) -> bool:
        """Step 8: Test JSON extraction using prompt only (NO response_format)"""
        self.print_step(8, "JSON Extraction via Prompt (No response_format)")

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
            "max_tokens": 100,
            "temperature": 0.0
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.config.timeout
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                # Try to parse as JSON
                try:
                    json_content = json.loads(content.strip())
                    self.print_result(True, "JSON extraction via prompt successful")
                    self.log(f"   Parsed JSON: {json_content}")
                    return True
                except json.JSONDecodeError:
                    # Maybe JSON is wrapped in markdown
                    if "```json" in content:
                        try:
                            json_text = content.split("```json")[1].split("```")[0].strip()
                            json_content = json.loads(json_text)
                            self.print_result(True, "JSON extraction successful (from markdown)")
                            self.log(f"   Parsed JSON: {json_content}")
                            self.log("   Note: Response wrapped in markdown code block")
                            return True
                        except:
                            pass

                    self.print_result(False, "Response is not valid JSON")
                    self.log(f"   Response: {content[:200]}")
                    return False
            else:
                self.print_result(False, f"JSON test failed: HTTP {response.status_code}")
                self.log(f"   Error: {response.text[:200]}")
                return False

        except Exception as e:
            self.print_result(False, f"JSON test error: {e}")
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
                    "content": LEGAL_EVENTS_PROMPT + "\n\nReturn ONLY a valid JSON array. No markdown, no other text."
                },
                {
                    "role": "user",
                    "content": f"Extract legal events from this document:\n\n{legal_text}"
                }
            ],
            "temperature": 0.0,
            "max_tokens": 500
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.config.timeout
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                # Try to parse as JSON
                try:
                    # Clean content
                    clean_content = content.strip()
                    if clean_content.startswith("```json"):
                        clean_content = clean_content.split("```json")[1].split("```")[0].strip()
                    elif clean_content.startswith("```"):
                        clean_content = clean_content.split("```")[1].split("```")[0].strip()

                    events = json.loads(clean_content)

                    if isinstance(events, dict) and "events" in events:
                        events = events["events"]

                    if isinstance(events, list):
                        self.print_result(True, f"Legal event extraction successful (array)")
                        self.log(f"   Extracted {len(events)} events")
                        return True
                    else:
                        self.print_result(False, "Response is not a JSON array")
                        self.log(f"   Response type: {type(events)}")
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

    def check_reasoning_mode(self) -> bool:
        """Step 10: Test DeepSeek reasoning mode"""
        self.print_step(10, "DeepSeek Reasoning Mode Test")

        url = f"{self.config.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "user",
                    "content": "What is 2+2? Think step by step."
                }
            ],
            "temperature": 0.0,
            "max_tokens": 200,
            "reasoning": True,  # DeepSeek-specific parameter
            "include_reasoning": True
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.config.timeout
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                # Check if reasoning tokens are present
                has_thinking = "<think>" in content or "</think>" in content

                self.print_result(True, "Reasoning mode supported")
                self.log(f"   Reasoning tags detected: {has_thinking}")
                self.log(f"   Response length: {len(content)} chars")

                if has_thinking:
                    self.log("   ✅ Model uses <think> tags for reasoning")

                return True
            else:
                self.print_result(False, f"Reasoning test failed: HTTP {response.status_code}")
                self.log(f"   Error: {response.text[:200]}")
                return False

        except Exception as e:
            self.print_result(False, f"Reasoning test error: {e}")
            return False

    def print_summary(self):
        """Print diagnostic summary"""
        print("\n" + "=" * 70)
        print("📊 DIAGNOSTIC SUMMARY")
        print("=" * 70)

        success_rate = (self.checks_passed / self.total_checks) * 100
        print(f"Checks Passed: {self.checks_passed}/{self.total_checks} ({success_rate:.1f}%)")
        print()

        if self.checks_passed == self.total_checks:
            print("✅ ALL CHECKS PASSED - DeepSeek is properly configured!")
            print()
            print("💡 Next steps:")
            print("   1. Update .env: OPENROUTER_MODEL=deepseek/deepseek-r1-distill-llama-70b")
            print("   2. Fix adapter: Remove 'response_format' parameter")
            print("   3. Add JSON instruction to system prompt")
            print()
        elif self.checks_passed >= 7:
            print("⚠️ MOSTLY WORKING - Minor issues to address")
            print()
            print("💡 Recommendations:")
            print("   - Review failed checks above")
            print("   - Consider using prompt-only JSON extraction")
            print()
        else:
            print("❌ MULTIPLE ISSUES - Configuration needs attention")
            print()
            print("💡 Troubleshooting:")
            print("   - Verify OPENROUTER_API_KEY is correct")
            print("   - Check network connectivity")
            print("   - Review model availability")
            print()

        print(f"📄 Detailed log saved to: {self.log_file}")
        print("=" * 70)

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
            self.check_json_via_prompt,
            self.check_legal_event_extraction,
            self.check_reasoning_mode
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
        description="DeepSeek R1 Distill via OpenRouter diagnostic tool"
    )
    parser.add_argument(
        "--test-model",
        help="Override model to test (default: deepseek/deepseek-r1-distill-llama-70b)",
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
