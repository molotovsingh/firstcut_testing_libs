#!/usr/bin/env python3
"""
Fallback Models Testing Script
Tests additional OpenRouter models to build a reliable fallback strategy
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
from dataclasses import dataclass, field

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("❌ Error: requests library not available")
    sys.exit(1)

from dotenv import load_dotenv
from src.core.constants import LEGAL_EVENTS_PROMPT

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ModelTestResult:
    """Results for a single model test"""
    model_id: str
    display_name: str
    tier: str  # "free" or "paid"
    basic_chat_passed: bool = False
    json_mode_passed: bool = False
    legal_extraction_passed: bool = False
    response_time: float = 0.0
    tokens_used: int = 0
    quality_score: int = 0
    cost_per_million: float = 0.0
    error_message: str = ""
    notes: List[str] = field(default_factory=list)
    json_clean: bool = False
    all_fields_present: bool = False
    reliability_score: int = 0  # 0-10 based on quirks


class FallbackModelTester:
    """Test multiple models to establish fallback hierarchy"""

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.base_url = "https://openrouter.ai/api/v1"
        self.log_file = Path(__file__).parent / "fallback_models_test.log"
        self.results: List[ModelTestResult] = []

        # Setup file logging
        file_handler = logging.FileHandler(self.log_file, mode='w')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

        # Expanded model list for fallback testing
        self.models_to_test = [
            # Tier 1: Premium OpenAI models
            ("openai/gpt-4o", "GPT-4o", "paid", 3.00),
            ("openai/gpt-4o-mini", "GPT-4o Mini", "paid", 0.15),
            ("openai/gpt-4-turbo", "GPT-4 Turbo", "paid", 10.00),

            # Tier 2: Other OpenAI variants
            ("openai/gpt-3.5-turbo", "GPT-3.5 Turbo", "paid", 0.50),

            # Tier 3: Google models
            ("google/gemini-pro-1.5", "Gemini Pro 1.5", "paid", 1.25),
            ("google/gemini-flash-1.5", "Gemini Flash 1.5", "paid", 0.075),
            ("google/gemini-2.0-flash-exp:free", "Gemini 2.0 Flash (FREE)", "free", 0.0),

            # Tier 4: Anthropic models
            ("anthropic/claude-3-5-sonnet", "Claude 3.5 Sonnet", "paid", 3.00),
            ("anthropic/claude-3-haiku", "Claude 3 Haiku", "paid", 0.25),

            # Tier 5: Meta Llama models
            ("meta-llama/llama-3.3-70b-instruct", "Llama 3.3 70B", "paid", 0.60),
            ("meta-llama/llama-3.3-70b-instruct:free", "Llama 3.3 70B (FREE)", "free", 0.0),
            ("meta-llama/llama-3.1-405b-instruct", "Llama 3.1 405B", "paid", 2.00),

            # Tier 6: DeepSeek models
            ("deepseek/deepseek-chat", "DeepSeek V3", "paid", 0.25),
            ("deepseek/deepseek-r1-distill-llama-70b", "DeepSeek R1 Distill", "paid", 0.03),

            # Tier 7: Mistral models
            ("mistralai/mistral-large", "Mistral Large", "paid", 2.00),
            ("mistralai/mistral-small", "Mistral Small", "paid", 0.20),

            # Tier 8: Other promising models
            ("cohere/command-r-plus", "Cohere Command R+", "paid", 2.50),
            ("perplexity/llama-3.1-sonar-large-128k-online", "Perplexity Sonar", "paid", 1.00),
        ]

        # Legal text for testing
        self.legal_text = """
        Motion to Dismiss filed on January 15, 2024, pursuant to Federal Rules of Civil Procedure 12(b)(6).
        The defendant argues failure to state a claim upon which relief can be granted.
        Plaintiff has 21 days to respond per Local Rule 7.1. Hearing scheduled for March 1, 2024
        in the United States District Court, Northern District of California, Case No. 3:24-cv-00123.
        """

    def log(self, message: str):
        """Log to both console and file"""
        logger.info(message)

    def print_header(self):
        """Print test header"""
        print("\n" + "=" * 85)
        print("🔄 OpenRouter Fallback Models Testing")
        print("=" * 85)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Testing {len(self.models_to_test)} models")
        print(f"Log file: {self.log_file}")
        print("=" * 85 + "\n")

    def test_basic_chat(self, model_id: str) -> Tuple[bool, float, int, str]:
        """Test 1: Basic chat completion"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model_id,
            "messages": [
                {"role": "user", "content": "Reply with only the word 'OK'."}
            ],
            "max_tokens": 10,
            "temperature": 0.0
        }

        try:
            start_time = time.time()
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            elapsed = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                tokens = data.get("usage", {}).get("total_tokens", 0)
                return True, elapsed, tokens, ""
            else:
                return False, elapsed, 0, f"HTTP {response.status_code}"

        except Exception as e:
            return False, 0.0, 0, str(e)[:100]

    def test_json_mode(self, model_id: str) -> Tuple[bool, bool, float, int, str]:
        """Test 2: JSON mode with response_format"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": "Return only valid JSON."},
                {"role": "user", "content": 'Return: {"test": "ok", "value": 42}'}
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 50,
            "temperature": 0.0
        }

        try:
            start_time = time.time()
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            elapsed = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                tokens = data.get("usage", {}).get("total_tokens", 0)

                clean = not ("```" in content)

                try:
                    if "```json" in content:
                        json_text = content.split("```json")[1].split("```")[0].strip()
                        json.loads(json_text)
                        return True, False, elapsed, tokens, ""
                    else:
                        json.loads(content.strip())
                        return True, clean, elapsed, tokens, ""
                except json.JSONDecodeError as e:
                    return False, False, elapsed, tokens, f"Invalid JSON: {str(e)[:50]}"
            else:
                return False, False, elapsed, 0, f"HTTP {response.status_code}"

        except Exception as e:
            return False, False, 0.0, 0, str(e)[:100]

    def test_legal_extraction(self, model_id: str) -> Tuple[bool, bool, bool, float, int, str]:
        """Test 3: Legal event extraction"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model_id,
            "messages": [
                {
                    "role": "system",
                    "content": LEGAL_EVENTS_PROMPT + "\n\nReturn ONLY valid JSON array."
                },
                {
                    "role": "user",
                    "content": f"Extract legal events:\n\n{self.legal_text}"
                }
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0,
            "max_tokens": 800
        }

        try:
            start_time = time.time()
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            elapsed = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                tokens = data.get("usage", {}).get("total_tokens", 0)

                clean = not ("```" in content)

                try:
                    clean_content = content.strip()
                    if "```json" in clean_content:
                        clean_content = clean_content.split("```json")[1].split("```")[0].strip()
                        clean = False
                    elif "```" in clean_content:
                        clean_content = clean_content.split("```")[1].split("```")[0].strip()
                        clean = False

                    parsed = json.loads(clean_content)

                    events = parsed
                    if isinstance(parsed, dict):
                        if "events" in parsed:
                            events = parsed["events"]
                        else:
                            events = [parsed]

                    if not isinstance(events, list):
                        return False, False, False, elapsed, tokens, "Not a list"

                    all_fields_present = True
                    for event in events:
                        if not isinstance(event, dict):
                            all_fields_present = False
                            break
                        required = ["event_particulars", "citation", "document_reference", "date"]
                        for field in required:
                            if field not in event:
                                all_fields_present = False
                                break

                    return True, clean, all_fields_present, elapsed, tokens, ""

                except json.JSONDecodeError as e:
                    return False, False, False, elapsed, tokens, f"JSON error: {str(e)[:50]}"
            else:
                return False, False, False, elapsed, 0, f"HTTP {response.status_code}"

        except Exception as e:
            return False, False, False, 0.0, 0, str(e)[:100]

    def calculate_scores(self, result: ModelTestResult) -> Tuple[int, int]:
        """Calculate quality and reliability scores"""
        quality = 0
        reliability = 10  # Start at max, deduct for quirks

        if result.basic_chat_passed:
            quality += 2
        else:
            reliability -= 3

        if result.json_mode_passed:
            quality += 3
            if result.json_clean:
                quality += 2
                reliability += 0  # Clean JSON is expected
            else:
                reliability -= 2  # Markdown wrapping is a quirk
        else:
            reliability -= 5

        if result.legal_extraction_passed:
            quality += 2
            if result.all_fields_present:
                quality += 1
            else:
                reliability -= 1

        return min(quality, 10), max(reliability, 0)

    def test_model(self, model_id: str, display_name: str, tier: str, cost: float) -> ModelTestResult:
        """Run all tests for a single model"""
        print(f"\n{'─' * 85}")
        tier_emoji = "💰" if tier == "paid" else "🆓"
        print(f"{tier_emoji} Testing: {display_name}")
        print(f"   Model: {model_id}")
        print(f"   Cost: ${cost}/M tokens" if cost > 0 else "   Cost: FREE")
        print(f"{'─' * 85}")

        result = ModelTestResult(
            model_id=model_id,
            display_name=display_name,
            tier=tier,
            cost_per_million=cost
        )

        # Test 1: Basic Chat
        print("   [1/3] Basic chat...", end=" ", flush=True)
        passed, elapsed, tokens, error = self.test_basic_chat(model_id)
        result.basic_chat_passed = passed
        result.response_time += elapsed
        result.tokens_used += tokens
        if passed:
            print(f"✅ ({elapsed:.2f}s)")
        else:
            print(f"❌ {error}")
            result.error_message = error
            result.notes.append(f"Basic chat failed: {error}")

        # Test 2: JSON Mode
        if passed:
            print("   [2/3] JSON mode...", end=" ", flush=True)
            passed, clean, elapsed, tokens, error = self.test_json_mode(model_id)
            result.json_mode_passed = passed
            result.json_clean = clean
            result.response_time += elapsed
            result.tokens_used += tokens
            if passed:
                status = "clean ✨" if clean else "wrapped ⚠️"
                print(f"✅ {status} ({elapsed:.2f}s)")
                if not clean:
                    result.notes.append("JSON in markdown")
            else:
                print(f"❌ {error}")
                result.notes.append(f"JSON failed: {error}")

        # Test 3: Legal Extraction
        if result.json_mode_passed:
            print("   [3/3] Legal extraction...", end=" ", flush=True)
            passed, clean, all_fields, elapsed, tokens, error = self.test_legal_extraction(model_id)
            result.legal_extraction_passed = passed
            result.json_clean = result.json_clean and clean
            result.all_fields_present = all_fields
            result.response_time += elapsed
            result.tokens_used += tokens
            if passed:
                status = "all fields ✓" if all_fields else "missing fields ⚠️"
                print(f"✅ {status} ({elapsed:.2f}s)")
            else:
                print(f"❌ {error}")
                result.notes.append(f"Extraction failed: {error}")
        else:
            print("   [3/3] Legal extraction... ⏭️ Skipped")

        # Calculate scores
        result.quality_score, result.reliability_score = self.calculate_scores(result)

        print(f"\n   Quality: {result.quality_score}/10 | Reliability: {result.reliability_score}/10")
        if result.notes:
            print(f"   Notes: {'; '.join(result.notes)}")

        return result

    def print_summary(self):
        """Print comprehensive summary with fallback recommendations"""
        print("\n" + "=" * 85)
        print("📊 FALLBACK STRATEGY RESULTS")
        print("=" * 85)

        # Separate by tier
        free_models = [r for r in self.results if r.tier == "free"]
        paid_models = [r for r in self.results if r.tier == "paid"]

        # Sort by quality score
        free_models.sort(key=lambda x: (x.quality_score, x.reliability_score), reverse=True)
        paid_models.sort(key=lambda x: (x.quality_score, x.reliability_score, -x.cost_per_million), reverse=True)

        # Print free models
        print("\n🆓 FREE MODELS:")
        print(f"{'Model':<50}{'Quality':<12}{'Reliability':<15}{'Status'}")
        print("─" * 85)
        for r in free_models:
            name = r.display_name[:48]
            quality = f"{r.quality_score}/10"
            reliability = f"{r.reliability_score}/10"
            if r.quality_score >= 9:
                status = "🥇 EXCELLENT"
            elif r.quality_score >= 7:
                status = "🥈 GOOD"
            elif r.quality_score >= 5:
                status = "🥉 OK"
            else:
                status = "❌ FAILED"
            print(f"{name:<50}{quality:<12}{reliability:<15}{status}")

        # Print paid models
        print("\n💰 PAID MODELS:")
        print(f"{'Model':<40}{'Cost/M':<10}{'Quality':<10}{'Reliability':<12}{'Status'}")
        print("─" * 85)
        for r in paid_models:
            name = r.display_name[:38]
            cost = f"${r.cost_per_million}"
            quality = f"{r.quality_score}/10"
            reliability = f"{r.reliability_score}/10"
            if r.quality_score >= 9:
                status = "🥇 EXCELLENT"
            elif r.quality_score >= 7:
                status = "🥈 GOOD"
            else:
                status = "❌ FAILED"
            print(f"{name:<40}{cost:<10}{quality:<10}{reliability:<12}{status}")

        # Fallback strategy
        print("\n" + "=" * 85)
        print("🎯 RECOMMENDED FALLBACK STRATEGY")
        print("=" * 85)

        excellent_paid = [r for r in paid_models if r.quality_score >= 9]
        good_paid = [r for r in paid_models if 7 <= r.quality_score < 9]
        excellent_free = [r for r in free_models if r.quality_score >= 9]

        if excellent_paid:
            print("\n**Primary (Paid - Best Quality):**")
            for i, r in enumerate(excellent_paid[:3], 1):
                print(f"  {i}. {r.model_id}")
                print(f"     Cost: ${r.cost_per_million}/M | Reliability: {r.reliability_score}/10")

        if excellent_free:
            print("\n**Fallback (Free - Cost Savings):**")
            for i, r in enumerate(excellent_free[:2], 1):
                print(f"  {i}. {r.model_id}")
                print(f"     FREE | Reliability: {r.reliability_score}/10")

        if good_paid:
            print("\n**Emergency Fallback (Good Enough):**")
            for i, r in enumerate(good_paid[:2], 1):
                print(f"  {i}. {r.model_id}")
                print(f"     Cost: ${r.cost_per_million}/M | Reliability: {r.reliability_score}/10")

        print(f"\n📄 Detailed log: {self.log_file}")
        print("=" * 85 + "\n")

    def run_all_tests(self):
        """Run tests for all models"""
        self.print_header()

        for model_id, display_name, tier, cost in self.models_to_test:
            result = self.test_model(model_id, display_name, tier, cost)
            self.results.append(result)
            self.log(f"Completed: {model_id} | Q:{result.quality_score}/10 R:{result.reliability_score}/10")

        self.print_summary()


def main():
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ Error: OPENROUTER_API_KEY not found")
        sys.exit(1)

    tester = FallbackModelTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
