#!/usr/bin/env python3
"""
Comprehensive Test Suite Runner
Executes all acceptance criteria and validation tests for 5-column legal events table

Usage:
    GOOGLE_API_KEY=your_key uv run python tests/run_all_tests.py
    GOOGLE_API_KEY=your_key uv run python tests/run_all_tests.py --quick    # Skip performance tests
    GOOGLE_API_KEY=your_key uv run python tests/run_all_tests.py --report   # Generate detailed report
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load .env file from project root
project_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / ".env")

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from test_acceptance_criteria import AcceptanceCriteriaTests
from test_performance_integration import PerformanceIntegrationTests


class TestSuiteRunner:
    """Comprehensive test suite runner and results validator"""

    def __init__(self, quick_mode: bool = False, generate_report: bool = True):
        self.quick_mode = quick_mode
        self.generate_report = generate_report
        self.test_results = {
            "execution_info": {
                "timestamp": datetime.now().isoformat(),
                "quick_mode": quick_mode,
                "environment": self._get_environment_info()
            },
            "acceptance_criteria": {
                "executed": False,
                "results": [],
                "summary": {}
            },
            "performance_integration": {
                "executed": False,
                "results": [],
                "summary": {}
            },
            "overall_summary": {}
        }

    def _get_environment_info(self) -> Dict[str, Any]:
        """Gather environment information for test report"""
        return {
            "python_version": sys.version,
            "api_key_configured": bool(os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')),
            "working_directory": str(Path.cwd()),
            "test_documents_available": self._check_test_documents()
        }

    def _check_test_documents(self) -> List[str]:
        """Check availability of test documents"""
        test_docs_dir = Path(__file__).parent / "test_documents"
        if test_docs_dir.exists():
            return [f.name for f in test_docs_dir.glob("*.html")]
        return []

    def run_acceptance_criteria_tests(self) -> bool:
        """Execute acceptance criteria test suite"""
        print("🧪 RUNNING ACCEPTANCE CRITERIA TESTS")
        print("=" * 60)

        try:
            ac_tests = AcceptanceCriteriaTests()
            success = ac_tests.run_all_tests()

            # Capture results
            self.test_results["acceptance_criteria"]["executed"] = True
            self.test_results["acceptance_criteria"]["results"] = ac_tests.test_results
            self.test_results["acceptance_criteria"]["summary"] = self._summarize_ac_results(ac_tests.test_results)

            return success

        except Exception as e:
            print(f"❌ CRITICAL ERROR in acceptance criteria tests: {e}")
            self.test_results["acceptance_criteria"]["error"] = str(e)
            return False

    def run_performance_integration_tests(self) -> bool:
        """Execute performance and integration test suite"""
        if self.quick_mode:
            print("⚡ SKIPPING PERFORMANCE TESTS (Quick Mode)")
            return True

        print("🚀 RUNNING PERFORMANCE & INTEGRATION TESTS")
        print("=" * 60)

        try:
            perf_tests = PerformanceIntegrationTests()
            success = perf_tests.run_all_tests()

            # Capture results
            self.test_results["performance_integration"]["executed"] = True
            self.test_results["performance_integration"]["results"] = perf_tests.test_results
            self.test_results["performance_integration"]["summary"] = self._summarize_perf_results(perf_tests.test_results)

            return success

        except Exception as e:
            print(f"❌ CRITICAL ERROR in performance/integration tests: {e}")
            self.test_results["performance_integration"]["error"] = str(e)
            return False

    def _summarize_ac_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Summarize acceptance criteria test results"""
        if not results:
            return {"total": 0, "passed": 0, "failed": 0, "success_rate": 0.0}

        total = len(results)
        passed = sum(1 for r in results if r["passed"])
        failed = total - passed

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "success_rate": round((passed / total) * 100, 1) if total > 0 else 0.0,
            "failed_tests": [r["test_id"] for r in results if not r["passed"]]
        }

    def _summarize_perf_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Summarize performance test results"""
        if not results:
            return {"total": 0, "passed": 0, "failed": 0, "avg_time": 0.0}

        total = len(results)
        passed = sum(1 for r in results if r["success"])
        failed = total - passed

        execution_times = [r["execution_time"] for r in results if r["success"]]
        avg_time = sum(execution_times) / len(execution_times) if execution_times else 0.0

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "success_rate": round((passed / total) * 100, 1) if total > 0 else 0.0,
            "avg_execution_time": round(avg_time, 2),
            "failed_tests": [r["test_name"] for r in results if not r["success"]]
        }

    def generate_overall_summary(self):
        """Generate overall test execution summary"""
        ac_summary = self.test_results["acceptance_criteria"]["summary"]
        perf_summary = self.test_results["performance_integration"]["summary"]

        total_tests = ac_summary.get("total", 0) + perf_summary.get("total", 0)
        total_passed = ac_summary.get("passed", 0) + perf_summary.get("passed", 0)
        total_failed = total_tests - total_passed

        overall_success_rate = round((total_passed / total_tests) * 100, 1) if total_tests > 0 else 0.0

        # Determine overall status
        if overall_success_rate >= 95.0:
            status = "EXCELLENT"
            recommendation = "Ready for production deployment"
        elif overall_success_rate >= 85.0:
            status = "GOOD"
            recommendation = "Minor issues to address before deployment"
        elif overall_success_rate >= 70.0:
            status = "ACCEPTABLE"
            recommendation = "Several issues require attention"
        else:
            status = "NEEDS_WORK"
            recommendation = "Significant issues must be resolved"

        self.test_results["overall_summary"] = {
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "overall_success_rate": overall_success_rate,
            "status": status,
            "recommendation": recommendation,
            "acceptance_criteria_passed": ac_summary.get("success_rate", 0) >= 90.0,
            "performance_passed": perf_summary.get("success_rate", 0) >= 80.0,
            "ready_for_production": overall_success_rate >= 95.0 and total_failed == 0
        }

    def print_executive_summary(self):
        """Print executive summary of test results"""
        print("\n" + "=" * 80)
        print("🏆 EXECUTIVE SUMMARY - 5-COLUMN LEGAL EVENTS TABLE VALIDATION")
        print("=" * 80)

        overall = self.test_results["overall_summary"]
        ac = self.test_results["acceptance_criteria"]["summary"]
        perf = self.test_results["performance_integration"]["summary"]

        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Status: {overall['status']}")
        print(f"   Total Tests: {overall['total_tests']}")
        print(f"   ✅ Passed: {overall['total_passed']}")
        print(f"   ❌ Failed: {overall['total_failed']}")
        print(f"   Success Rate: {overall['overall_success_rate']}%")

        print(f"\n🧪 ACCEPTANCE CRITERIA:")
        print(f"   Tests: {ac.get('total', 0)}")
        print(f"   Success Rate: {ac.get('success_rate', 0)}%")
        if ac.get('failed_tests'):
            print(f"   Failed: {', '.join(ac['failed_tests'])}")

        if not self.quick_mode and perf:
            print(f"\n🚀 PERFORMANCE & INTEGRATION:")
            print(f"   Tests: {perf.get('total', 0)}")
            print(f"   Success Rate: {perf.get('success_rate', 0)}%")
            print(f"   Avg Execution Time: {perf.get('avg_execution_time', 0)}s")
            if perf.get('failed_tests'):
                print(f"   Failed: {', '.join(perf['failed_tests'])}")

        print(f"\n💡 RECOMMENDATION:")
        print(f"   {overall['recommendation']}")

        if overall["ready_for_production"]:
            print("\n🎉 ✅ READY FOR PRODUCTION DEPLOYMENT!")
        else:
            print("\n⚠️  ❌ REQUIRES ATTENTION BEFORE DEPLOYMENT")

        print("\n" + "=" * 80)

    def save_test_report(self):
        """Save detailed test report to file"""
        if not self.generate_report:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = Path(__file__).parent / f"test_report_{timestamp}.json"

        try:
            with open(report_file, 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)

            print(f"\n📄 Detailed test report saved: {report_file}")

        except Exception as e:
            print(f"❌ Failed to save test report: {e}")

    def run_all_tests(self) -> bool:
        """Execute complete test suite"""
        print("🔬 STARTING COMPREHENSIVE 5-COLUMN TABLE TEST SUITE")
        print(f"Mode: {'Quick' if self.quick_mode else 'Full'}")
        print(f"Report Generation: {'Enabled' if self.generate_report else 'Disabled'}")
        print("=" * 80)

        start_time = time.time()

        # Pre-flight checks
        if not self._pre_flight_checks():
            return False

        # Execute test suites
        ac_success = self.run_acceptance_criteria_tests()
        perf_success = self.run_performance_integration_tests()

        # Generate results
        self.generate_overall_summary()

        # Calculate total execution time
        total_time = time.time() - start_time
        self.test_results["execution_info"]["total_execution_time"] = round(total_time, 2)

        # Display results
        self.print_executive_summary()

        # Save report
        if self.generate_report:
            self.save_test_report()

        # Overall success determination
        overall_success = (ac_success and
                          (perf_success or self.quick_mode) and
                          self.test_results["overall_summary"]["overall_success_rate"] >= 85.0)

        return overall_success

    def _pre_flight_checks(self) -> bool:
        """Perform pre-flight checks before running tests"""
        print("🔍 PRE-FLIGHT CHECKS")
        print("-" * 40)

        # Check API key
        api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ Missing API key (GOOGLE_API_KEY or GEMINI_API_KEY)")
            return False
        print("✅ API key configured")

        # Check test documents
        test_docs = self.test_results["execution_info"]["environment"]["test_documents_available"]
        if not test_docs:
            print("❌ No test documents found in tests/test_documents/")
            return False
        print(f"✅ Test documents available: {len(test_docs)}")

        # Check imports
        try:
            from src.core.legal_pipeline_refactored import LegalEventsPipeline
            from src.core.constants import FIVE_COLUMN_HEADERS
            print("✅ Core modules importable")
        except ImportError as e:
            print(f"❌ Import error: {e}")
            return False

        print("✅ Pre-flight checks passed\n")
        return True


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Run 5-column table test suite")
    parser.add_argument("--quick", action="store_true",
                       help="Skip performance tests for faster execution")
    parser.add_argument("--no-report", action="store_true",
                       help="Skip generating detailed JSON report")

    args = parser.parse_args()

    # Create and run test suite
    runner = TestSuiteRunner(
        quick_mode=args.quick,
        generate_report=not args.no_report
    )

    success = runner.run_all_tests()

    # Exit with appropriate code
    exit_code = 0 if success else 1
    print(f"\n🏁 Test suite completed with exit code: {exit_code}")

    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)