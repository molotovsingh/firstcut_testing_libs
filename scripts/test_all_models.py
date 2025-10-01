#!/usr/bin/env python3
"""
Multi-Model Comparison Test for OpenRouter
Tests multiple models to find the best one for legal event extraction
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
    basic_chat_passed: bool = False
    json_mode_passed: bool = False
    legal_extraction_passed: bool = False
    response_time: float = 0.0
    tokens_used: int = 0
    quality_score: int = 0
    error_message: str = ""
    notes: List[str] = field(default_factory=list)
    json_clean: bool = False  # No markdown wrapping
    all_fields_present: bool = False


class MultiModelTester:
    """Test multiple OpenRouter models for legal event extraction"""

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.base_url = "https://openrouter.ai/api/v1"
        self.log_file = Path(__file__).parent / "all_models_test.log"
        self.results: List[ModelTestResult] = []

        # Setup file logging
        file_handler = logging.FileHandler(self.log_file, mode='w')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

        # Models to test (in priority order)
        self.models_to_test = [
            ("google/gemini-2.0-flash-exp:free", "Gemini 2.0 Flash (FREE)"),
            ("meta-llama/llama-3.3-70b-instruct:free", "Llama 3.3 70B (FREE)"),
            ("qwen/qwq-32b:free", "Qwen QwQ 32B (FREE)"),
            ("openai/gpt-4o-mini", "GPT-4o Mini (Paid)"),
            ("openai/gpt-4o", "GPT-4o (Premium)"),
        ]

        # Legal text sample for testing
        self.legal_text = """
        Settlement Agreement executed on March 15, 2024, between Plaintiff Jane Doe and
        Defendant ABC Corporation. The parties agreed to settle all claims for $500,000,
        with payment due within 30 days. Pursuant to Federal Rules of Civil Procedure Rule 41(a)(1)(A)(ii),
        the case will be dismissed with prejudice. Final hearing scheduled for April 1, 2024,
        at 10:00 AM in the United States District Court for the Southern District of New York.
        Both parties agreed to mutual non-disparagement clauses.
        """

    def log(self, message: str):
        """Log to both console and file"""
        logger.info(message)

    def print_header(self):
        """Print test header"""
        print("\n" + "=" * 80)
        print("🧪 OpenRouter Multi-Model Comparison Test")
        print("=" * 80)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Testing {len(self.models_to_test)} models")
        print(f"Log file: {self.log_file}")
        print("=" * 80 + "\n")

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
                {"role": "user", "content": "Say 'OK' if you can understand this message."}
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
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                tokens = data.get("usage", {}).get("total_tokens", 0)
                return True, elapsed, tokens, ""
            else:
                return False, elapsed, 0, f"HTTP {response.status_code}: {response.text[:200]}"

        except Exception as e:
            return False, 0.0, 0, str(e)

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
                {
                    "role": "system",
                    "content": "You are a JSON generator. Return only valid JSON."
                },
                {
                    "role": "user",
                    "content": 'Return this JSON: {"status": "ok", "test": true, "number": 42}'
                }
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 100,
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

                # Check if JSON is clean (no markdown)
                clean = not ("```" in content)

                # Try to parse JSON
                try:
                    if "```json" in content:
                        # Extract from markdown
                        json_text = content.split("```json")[1].split("```")[0].strip()
                        json.loads(json_text)
                        return True, False, elapsed, tokens, ""  # Works but not clean
                    else:
                        json.loads(content.strip())
                        return True, clean, elapsed, tokens, ""  # Works and clean

                except json.JSONDecodeError as e:
                    return False, False, elapsed, tokens, f"Invalid JSON: {e}"

            else:
                # Model doesn't support response_format
                return False, False, elapsed, 0, f"HTTP {response.status_code}"

        except Exception as e:
            return False, False, 0.0, 0, str(e)

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
                    "content": LEGAL_EVENTS_PROMPT + "\n\nReturn ONLY a valid JSON array. No markdown, no extra text."
                },
                {
                    "role": "user",
                    "content": f"Extract legal events from this document:\n\n{self.legal_text}"
                }
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0,
            "max_tokens": 1000
        }

        try:
            start_time = time.time()
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            elapsed = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                tokens = data.get("usage", {}).get("total_tokens", 0)

                # Check if JSON is clean
                clean = not ("```" in content)

                # Parse JSON
                try:
                    # Clean content
                    clean_content = content.strip()
                    if "```json" in clean_content:
                        clean_content = clean_content.split("```json")[1].split("```")[0].strip()
                        clean = False
                    elif "```" in clean_content:
                        clean_content = clean_content.split("```")[1].split("```")[0].strip()
                        clean = False

                    parsed = json.loads(clean_content)

                    # Handle both array and object with events key
                    events = parsed
                    if isinstance(parsed, dict):
                        if "events" in parsed:
                            events = parsed["events"]
                        elif "extractions" in parsed:
                            events = parsed["extractions"]
                        else:
                            # Single event as object
                            events = [parsed]

                    if not isinstance(events, list):
                        return False, False, False, elapsed, tokens, "Response is not a list"

                    # Check if fields are present
                    all_fields_present = True
                    for event in events:
                        if not isinstance(event, dict):
                            all_fields_present = False
                            break
                        required_fields = ["event_particulars", "citation", "document_reference", "date"]
                        for field in required_fields:
                            if field not in event:
                                all_fields_present = False
                                break

                    return True, clean, all_fields_present, elapsed, tokens, ""

                except json.JSONDecodeError as e:
                    return False, False, False, elapsed, tokens, f"JSON parse error: {e}"

            else:
                return False, False, False, elapsed, 0, f"HTTP {response.status_code}: {response.text[:200]}"

        except Exception as e:
            return False, False, False, 0.0, 0, str(e)

    def calculate_quality_score(self, result: ModelTestResult) -> int:
        """Calculate quality score (0-10)"""
        score = 0

        if result.basic_chat_passed:
            score += 2

        if result.json_mode_passed:
            score += 3
            if result.json_clean:
                score += 2  # Bonus for clean JSON

        if result.legal_extraction_passed:
            score += 2
            if result.all_fields_present:
                score += 1  # Bonus for all fields

        return min(score, 10)

    def test_model(self, model_id: str, display_name: str) -> ModelTestResult:
        """Run all tests for a single model"""
        print(f"\n{'─' * 80}")
        print(f"🔍 Testing: {display_name}")
        print(f"   Model ID: {model_id}")
        print(f"{'─' * 80}")

        result = ModelTestResult(model_id=model_id)

        # Test 1: Basic Chat
        print("   [1/3] Basic chat test...", end=" ", flush=True)
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
            print("   [2/3] JSON mode test...", end=" ", flush=True)
            passed, clean, elapsed, tokens, error = self.test_json_mode(model_id)
            result.json_mode_passed = passed
            result.json_clean = clean
            result.response_time += elapsed
            result.tokens_used += tokens
            if passed:
                clean_status = "clean ✨" if clean else "wrapped ⚠️"
                print(f"✅ {clean_status} ({elapsed:.2f}s)")
                if not clean:
                    result.notes.append("JSON wrapped in markdown")
            else:
                print(f"❌ {error}")
                result.notes.append(f"JSON mode failed: {error}")

        # Test 3: Legal Extraction
        if result.json_mode_passed:
            print("   [3/3] Legal extraction test...", end=" ", flush=True)
            passed, clean, all_fields, elapsed, tokens, error = self.test_legal_extraction(model_id)
            result.legal_extraction_passed = passed
            result.json_clean = result.json_clean and clean
            result.all_fields_present = all_fields
            result.response_time += elapsed
            result.tokens_used += tokens
            if passed:
                fields_status = "all fields ✓" if all_fields else "missing fields ⚠️"
                print(f"✅ {fields_status} ({elapsed:.2f}s)")
                if not all_fields:
                    result.notes.append("Some required fields missing")
            else:
                print(f"❌ {error}")
                result.notes.append(f"Legal extraction failed: {error}")
        else:
            print("   [3/3] Legal extraction test... ⏭️ Skipped (JSON mode failed)")

        # Calculate quality score
        result.quality_score = self.calculate_quality_score(result)

        print(f"\n   Quality Score: {result.quality_score}/10")
        if result.notes:
            print(f"   Notes: {', '.join(result.notes)}")

        return result

    def print_summary(self):
        """Print comparison summary"""
        print("\n" + "=" * 80)
        print("📊 FINAL RESULTS - MODEL COMPARISON")
        print("=" * 80)

        # Sort by quality score
        sorted_results = sorted(self.results, key=lambda x: x.quality_score, reverse=True)

        print(f"\n{'Rank':<6}{'Model':<45}{'Score':<8}{'Status'}")
        print("─" * 80)

        for i, result in enumerate(sorted_results, 1):
            model_name = result.model_id.split("/")[-1]
            score = f"{result.quality_score}/10"

            # Determine status
            if result.quality_score >= 9:
                status = "🥇 EXCELLENT"
            elif result.quality_score >= 7:
                status = "🥈 GOOD"
            elif result.quality_score >= 5:
                status = "🥉 OK"
            else:
                status = "❌ FAILED"

            print(f"{i:<6}{model_name:<45}{score:<8}{status}")

        # Detailed breakdown
        print("\n" + "=" * 80)
        print("📋 DETAILED BREAKDOWN")
        print("=" * 80)

        for result in sorted_results:
            model_name = result.model_id.split("/")[-1]
            print(f"\n{model_name}:")
            print(f"  Basic Chat:        {'✅' if result.basic_chat_passed else '❌'}")
            print(f"  JSON Mode:         {'✅' if result.json_mode_passed else '❌'}")
            print(f"  Legal Extraction:  {'✅' if result.legal_extraction_passed else '❌'}")
            print(f"  Clean JSON:        {'✅' if result.json_clean else '❌'}")
            print(f"  All Fields:        {'✅' if result.all_fields_present else '❌'}")
            print(f"  Avg Response Time: {result.response_time:.2f}s")
            print(f"  Total Tokens:      {result.tokens_used}")
            if result.notes:
                print(f"  Notes:             {'; '.join(result.notes)}")

        # Recommendation
        print("\n" + "=" * 80)
        print("🎯 RECOMMENDATION")
        print("=" * 80)

        if sorted_results:
            best = sorted_results[0]
            best_name = best.model_id

            if best.quality_score >= 9:
                print(f"\n✅ **USE THIS MODEL**: {best_name}")
                print(f"\n   Update your .env:")
                print(f"   OPENROUTER_MODEL={best_name}")
                print(f"\n   Quality Score: {best.quality_score}/10")
                print(f"   Average Response: {best.response_time:.2f}s")
                print(f"   No code changes needed! ✨")
            elif best.quality_score >= 7:
                print(f"\n⚠️ **BEST AVAILABLE**: {best_name}")
                print(f"\n   Quality Score: {best.quality_score}/10")
                print(f"   Some minor quirks, but usable")
                if not best.json_clean:
                    print(f"   ⚠️ Requires markdown stripping in adapter")
            else:
                print(f"\n❌ **NO IDEAL MODEL FOUND**")
                print(f"   Best: {best_name} ({best.quality_score}/10)")
                print(f"   Consider using prompt engineering or different provider")

        print(f"\n📄 Detailed log saved to: {self.log_file}")
        print("=" * 80 + "\n")

    def run_all_tests(self):
        """Run tests for all models"""
        self.print_header()

        for model_id, display_name in self.models_to_test:
            result = self.test_model(model_id, display_name)
            self.results.append(result)
            self.log(f"Completed test for {model_id}: score={result.quality_score}/10")

        self.print_summary()


def main():
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ Error: OPENROUTER_API_KEY not found in environment")
        print("   Set it in your .env file")
        sys.exit(1)

    tester = MultiModelTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
