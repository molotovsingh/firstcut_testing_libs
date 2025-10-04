#!/usr/bin/env python3
"""
OpenCode Zen Models Testing Script
Comprehensive testing of all available OpenCode Zen models for legal event extraction
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
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

# Load environment FIRST (before imports that need it)
from dotenv import load_dotenv
load_dotenv()

from src.core.constants import LEGAL_EVENTS_PROMPT

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
    quality_score: int = 0  # 0-10
    reliability_score: int = 0  # 0-10
    cost_per_million: float = 0.0
    error_message: str = ""
    notes: List[str] = field(default_factory=list)
    json_clean: bool = False
    all_fields_present: bool = False


class OpenCodeZenModelsTester:
    """Test multiple OpenCode Zen models for legal extraction"""

    def __init__(self, specific_models: Optional[List[str]] = None, verbose: bool = False):
        self.api_key = os.getenv("OPENCODEZEN_API_KEY", "")
        self.base_url = os.getenv("OPENCODEZEN_BASE_URL", "https://opencode.ai/zen/v1").rstrip('/').replace('/chat/completions', '')
        self.verbose = verbose
        self.log_file = Path(__file__).parent / "opencode_zen_models_test.log"
        self.results: List[ModelTestResult] = []

        # Setup file logging
        file_handler = logging.FileHandler(self.log_file, mode='w')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

        # Legal test text
        self.legal_text = "On January 15, 2024, the plaintiff filed a motion to dismiss the complaint. The court granted the motion on February 3, 2024."

        # Known OpenCode Zen models (will try to discover more)
        self.known_models = [
            ("grok-code", "Grok Code", "paid", 0.50),
            ("qwen-3-coder-480b", "Qwen 3 Coder 480B", "paid", 1.20),
            ("grok-code-fast-1", "Grok Code Fast", "free", 0.00),
            ("code-supernova", "Code Supernova", "free", 0.00),
        ]

        # Use specific models if provided
        if specific_models:
            self.known_models = [
                (m[0], m[1], m[2], m[3]) for m in self.known_models
                if m[0] in specific_models
            ]

        if not self.api_key:
            logger.error("❌ OPENCODEZEN_API_KEY not set in .env")
            sys.exit(1)

    def log(self, message: str):
        """Log to console and file"""
        logger.info(message)

    def discover_models(self) -> List[Tuple[str, str, str, float]]:
        """Try to discover available models from API"""
        # Try /models endpoint
        url = f"{self.base_url}/models"
        headers = {"X-API-Key": self.api_key}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])

                discovered = []
                for model in models:
                    model_id = model.get("id", "")
                    name = model.get("name", model_id)
                    tier = "free" if ":free" in model_id or model.get("free", False) else "paid"
                    cost = model.get("pricing", {}).get("completion", 0.0)
                    discovered.append((model_id, name, tier, cost))

                if discovered:
                    self.log(f"✅ Discovered {len(discovered)} models from API")
                    return discovered
        except Exception as e:
            if self.verbose:
                self.log(f"⚠️  Could not discover models: {e}")

        # Fallback to known models
        self.log(f"📋 Using known models list ({len(self.known_models)} models)")
        return self.known_models

    def test_basic_chat(self, model_id: str) -> Tuple[bool, float, int, str]:
        """Test 1: Basic chat completion"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "model": model_id,
            "messages": [
                {"role": "user", "content": "Say 'hello' in one word."}
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

                if content.strip():
                    return True, elapsed, tokens, ""
                else:
                    return False, elapsed, 0, "Empty response"
            else:
                return False, elapsed, 0, f"HTTP {response.status_code}"

        except Exception as e:
            return False, 0.0, 0, str(e)[:100]

    def test_json_mode(self, model_id: str) -> Tuple[bool, bool, float, int, str]:
        """Test 2: JSON response format support"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "X-API-Key": self.api_key,
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

                # Check for markdown wrapping
                clean = not ("```" in content)

                try:
                    # Handle markdown-wrapped JSON (DeepSeek-style)
                    if "```json" in content:
                        json_text = content.split("```json")[1].split("```")[0].strip()
                        json.loads(json_text)
                        return True, False, elapsed, tokens, ""  # Works but not clean
                    else:
                        json.loads(content.strip())
                        return True, clean, elapsed, tokens, ""  # Clean JSON
                except json.JSONDecodeError as e:
                    return False, False, elapsed, tokens, f"Invalid JSON: {str(e)[:50]}"
            else:
                return False, False, elapsed, 0, f"HTTP {response.status_code}"

        except Exception as e:
            return False, False, 0.0, 0, str(e)[:100]

    def test_legal_extraction(self, model_id: str) -> Tuple[bool, bool, bool, float, int, str]:
        """Test 3: Legal event extraction with quality scoring"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "X-API-Key": self.api_key,
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

                # Check for markdown wrapping
                clean = not ("```" in content)

                try:
                    # Extract JSON from potential markdown
                    clean_content = content.strip()
                    if "```json" in clean_content:
                        clean_content = clean_content.split("```json")[1].split("```")[0].strip()
                        clean = False
                    elif "```" in clean_content:
                        clean_content = clean_content.split("```")[1].split("```")[0].strip()
                        clean = False

                    parsed = json.loads(clean_content)

                    # Handle different response structures
                    events = parsed
                    if isinstance(parsed, dict):
                        if "events" in parsed:
                            events = parsed["events"]
                        elif "extractions" in parsed:
                            events = parsed["extractions"]
                        else:
                            events = [parsed]  # Single event as dict

                    if not isinstance(events, list):
                        return False, False, False, elapsed, tokens, "Response not a list"

                    if not events:
                        return False, False, False, elapsed, tokens, "No events extracted"

                    # Check first event for required fields
                    first_event = events[0] if events else {}
                    required_fields = ["event_particulars"]
                    optional_fields = ["date", "citation", "document_reference"]

                    has_required = all(field in first_event for field in required_fields)
                    field_count = sum(1 for field in optional_fields if field in first_event and first_event[field])

                    # Quality scoring: has_required + field_coverage + event_count
                    all_fields = has_required and field_count >= 2

                    return True, clean, all_fields, elapsed, tokens, ""

                except json.JSONDecodeError as e:
                    return False, False, False, elapsed, tokens, f"JSON error: {str(e)[:50]}"
            else:
                return False, False, False, elapsed, 0, f"HTTP {response.status_code}"

        except Exception as e:
            return False, False, False, 0.0, 0, str(e)[:100]

    def calculate_scores(self, result: ModelTestResult) -> None:
        """Calculate quality and reliability scores (0-10)"""
        # Quality score based on test results
        quality = 0
        if result.basic_chat_passed:
            quality += 2
        if result.json_mode_passed:
            quality += 3
        if result.legal_extraction_passed:
            quality += 3
        if result.all_fields_present:
            quality += 2

        result.quality_score = min(quality, 10)

        # Reliability score based on output cleanliness
        reliability = 10
        if not result.json_clean:
            reliability -= 3  # Markdown wrapping penalty
            result.notes.append("JSON wrapped in markdown")
        if result.error_message:
            reliability -= 5
        if not result.all_fields_present and result.legal_extraction_passed:
            reliability -= 2  # Missing some fields

        result.reliability_score = max(reliability, 0)

    def test_model(self, model_id: str, display_name: str, tier: str, cost: float) -> ModelTestResult:
        """Run comprehensive test suite on a single model"""
        result = ModelTestResult(
            model_id=model_id,
            display_name=display_name,
            tier=tier,
            cost_per_million=cost
        )

        self.log(f"\n{'='*70}")
        self.log(f"Testing: {display_name} ({model_id})")
        self.log(f"Tier: {tier} | Cost: ${cost}/M tokens")
        self.log(f"{'='*70}")

        # Test 1: Basic chat
        basic_pass, basic_time, basic_tokens, basic_error = self.test_basic_chat(model_id)
        result.basic_chat_passed = basic_pass
        result.response_time = basic_time
        result.tokens_used = basic_tokens

        if basic_pass:
            self.log(f"✅ Basic chat: PASS ({basic_time:.2f}s, {basic_tokens} tokens)")
        else:
            result.error_message = basic_error
            self.log(f"❌ Basic chat: FAIL - {basic_error}")
            self.calculate_scores(result)
            return result

        # Test 2: JSON mode
        json_pass, json_clean, json_time, json_tokens, json_error = self.test_json_mode(model_id)
        result.json_mode_passed = json_pass
        result.json_clean = json_clean

        if json_pass:
            clean_text = "clean" if json_clean else "wrapped in markdown"
            self.log(f"✅ JSON mode: PASS ({clean_text}, {json_time:.2f}s)")
        else:
            result.error_message = json_error
            self.log(f"❌ JSON mode: FAIL - {json_error}")
            self.calculate_scores(result)
            return result

        # Test 3: Legal extraction
        legal_pass, legal_clean, fields_ok, legal_time, legal_tokens, legal_error = self.test_legal_extraction(model_id)
        result.legal_extraction_passed = legal_pass
        result.all_fields_present = fields_ok

        if legal_pass:
            fields_text = "all fields" if fields_ok else "some fields missing"
            self.log(f"✅ Legal extraction: PASS ({fields_text}, {legal_time:.2f}s)")
        else:
            result.error_message = legal_error
            self.log(f"❌ Legal extraction: FAIL - {legal_error}")

        # Calculate final scores
        self.calculate_scores(result)

        self.log(f"\n📊 Final Scores:")
        self.log(f"   Quality: {result.quality_score}/10")
        self.log(f"   Reliability: {result.reliability_score}/10")
        if result.notes:
            self.log(f"   Notes: {', '.join(result.notes)}")

        return result

    def print_summary(self):
        """Print comprehensive summary and recommendations"""
        self.log("\n\n" + "="*70)
        self.log("📊 TEST SUMMARY")
        self.log("="*70)

        # Overall stats
        total = len(self.results)
        passed_all = sum(1 for r in self.results if r.quality_score >= 8)
        self.log(f"\nModels Tested: {total}")
        self.log(f"Fully Passing (Quality ≥8): {passed_all}/{total}")

        # Results table
        self.log(f"\n{'Model':<35} {'Q':>3} {'R':>3} {'Time':>7} {'Cost':>8}")
        self.log("-" * 70)

        for result in sorted(self.results, key=lambda x: x.quality_score, reverse=True):
            cost_text = "FREE" if result.cost_per_million == 0 else f"${result.cost_per_million:.2f}/M"
            self.log(
                f"{result.display_name:<35} "
                f"{result.quality_score:>3}/10 "
                f"{result.reliability_score:>3}/10 "
                f"{result.response_time:>6.2f}s "
                f"{cost_text:>8}"
            )

        # Champions
        if self.results:
            quality_champ = max(self.results, key=lambda x: x.quality_score)
            reliable_champ = max(self.results, key=lambda x: x.reliability_score)
            speed_champ = min([r for r in self.results if r.quality_score >= 7],
                            key=lambda x: x.response_time, default=None)
            free_champ = max([r for r in self.results if r.cost_per_million == 0],
                           key=lambda x: x.quality_score, default=None)

            self.log(f"\n🏆 CHAMPIONS BY CATEGORY:")
            self.log(f"   Quality: {quality_champ.display_name} ({quality_champ.quality_score}/10)")
            self.log(f"   Reliability: {reliable_champ.display_name} ({reliable_champ.reliability_score}/10)")
            if speed_champ:
                self.log(f"   Speed: {speed_champ.display_name} ({speed_champ.response_time:.2f}s)")
            if free_champ:
                self.log(f"   Free Tier: {free_champ.display_name} ({free_champ.quality_score}/10)")

            # Recommendations
            self.log(f"\n💡 RECOMMENDATIONS:")

            production = max([r for r in self.results if r.quality_score >= 9 and r.reliability_score >= 9],
                           key=lambda x: (x.quality_score, -x.response_time), default=None)
            if production:
                self.log(f"   Production: {production.model_id} (Q:{production.quality_score}/10, R:{production.reliability_score}/10)")

            if free_champ and free_champ.quality_score >= 7:
                self.log(f"   Budget: {free_champ.model_id} (FREE, Q:{free_champ.quality_score}/10)")

            if speed_champ:
                self.log(f"   Speed: {speed_champ.model_id} ({speed_champ.response_time:.2f}s avg)")

        self.log(f"\n📄 Detailed log: {self.log_file}")
        self.log("="*70 + "\n")

    def run(self):
        """Execute comprehensive model testing"""
        self.log("="*70)
        self.log("🔍 OpenCode Zen Models Comprehensive Testing")
        self.log("="*70)
        self.log(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Discover or use known models
        models_to_test = self.discover_models()

        self.log(f"Testing {len(models_to_test)} models...\n")

        # Test each model
        for i, (model_id, name, tier, cost) in enumerate(models_to_test, 1):
            self.log(f"\n[{i}/{len(models_to_test)}] {name}")
            result = self.test_model(model_id, name, tier, cost)
            self.results.append(result)

            # Brief pause between tests
            if i < len(models_to_test):
                time.sleep(1)

        # Print summary
        self.print_summary()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Test OpenCode Zen models comprehensively")
    parser.add_argument("--models", help="Comma-separated list of specific models to test")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    specific_models = args.models.split(",") if args.models else None

    tester = OpenCodeZenModelsTester(
        specific_models=specific_models,
        verbose=args.verbose
    )

    tester.run()


if __name__ == "__main__":
    main()
