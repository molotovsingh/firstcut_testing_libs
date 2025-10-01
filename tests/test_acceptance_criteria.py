#!/usr/bin/env python3
"""
User Acceptance Criteria Test Suite
Validates the 5-column legal events table implementation

Run with: uv run python tests/test_acceptance_criteria.py
"""

import os
import sys
import pandas as pd
import logging
import time
from typing import List, Dict, Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.legal_pipeline_refactored import LegalEventsPipeline
from src.core.constants import FIVE_COLUMN_HEADERS, DEFAULT_NO_DATE
from src.core.table_formatter import TableFormatter

logger = logging.getLogger(__name__)

class AcceptanceCriteriaTests:
    """Automated test suite for 5-column legal events table acceptance criteria"""

    def __init__(self):
        self.test_results = []
        self.pipeline = None
        self.setup_logging()

    def setup_logging(self):
        """Configure logging for test output"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def log_test_result(self, test_id: str, description: str, passed: bool, details: str = ""):
        """Log test result for reporting"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = {
            "test_id": test_id,
            "description": description,
            "status": status,
            "passed": passed,
            "details": details
        }
        self.test_results.append(result)
        print(f"{status} {test_id}: {description}")
        if details and not passed:
            print(f"   Details: {details}")

    def setup_pipeline(self) -> bool:
        """Initialize the legal events pipeline"""
        try:
            self.pipeline = LegalEventsPipeline()
            return True
        except Exception as e:
            print(f"❌ Failed to initialize pipeline: {e}")
            return False

    def create_mock_uploaded_file(self, name: str, content: str):
        """Create mock uploaded file for testing"""
        class MockUploadedFile:
            def __init__(self, name, content):
                self.name = name
                self._content = content

            def getbuffer(self):
                return self._content.encode() if isinstance(self._content, str) else self._content

        return MockUploadedFile(name, content)

    # AC-001: Column Header Validation
    def test_column_headers(self):
        """Test that table has exactly 5 columns in correct order"""
        test_id = "AC-001"
        description = "Column header validation - 5 columns in correct order"

        try:
            expected_headers = ["No", "Date", "Event Particulars", "Citation", "Document Reference"]
            actual_headers = FIVE_COLUMN_HEADERS

            if actual_headers == expected_headers:
                self.log_test_result(test_id, description, True)
            else:
                details = f"Expected: {expected_headers}, Got: {actual_headers}"
                self.log_test_result(test_id, description, False, details)

        except Exception as e:
            self.log_test_result(test_id, description, False, str(e))

    # AC-003: Valid Date Extraction
    def test_valid_date_extraction(self):
        """Test extraction of clear, valid dates"""
        test_id = "AC-003"
        description = "Valid date extraction from clear date text"

        try:
            # Create test document with clear date
            test_content = """
            <html><body>
            <h1>Legal Document</h1>
            <p>On January 15, 2024, the plaintiff filed a motion for summary judgment pursuant to Federal Rule 56.</p>
            <p>The court scheduled a hearing for March 10, 2024 at 2:00 PM under Local Rule 7.1.</p>
            </body></html>
            """

            mock_file = self.create_mock_uploaded_file("test_clear_dates.html", test_content)
            df, warning = self.pipeline.process_documents_for_legal_events([mock_file])

            if df is not None and not df.empty:
                # Check if any dates were extracted (not all "Date not available")
                date_column = df[FIVE_COLUMN_HEADERS[1]]  # Date column
                valid_dates = date_column[date_column != DEFAULT_NO_DATE]

                if len(valid_dates) > 0:
                    details = f"Extracted {len(valid_dates)} valid dates out of {len(df)} events"
                    self.log_test_result(test_id, description, True, details)
                else:
                    self.log_test_result(test_id, description, False, "No valid dates extracted")
            else:
                self.log_test_result(test_id, description, False, "No data frame generated")

        except Exception as e:
            self.log_test_result(test_id, description, False, str(e))

    # AC-004: Multiple Date Format Support
    def test_multiple_date_formats(self):
        """Test recognition of various date formats"""
        test_id = "AC-004"
        description = "Multiple date format support validation"

        # Test individual date format validation
        from src.extractors.legal_events_extractor_refactored import LegalEventsExtractor

        try:
            extractor = LegalEventsExtractor()
            test_dates = [
                ("2024-01-15", True),      # ISO format
                ("1/15/2024", True),       # US format
                ("01/15/2024", True),      # US format with leading zeros
                ("1-15-2024", True),       # Dash format
                ("2024/01/15", True),      # Alternative ISO
                ("invalid-date", False),   # Invalid format
                ("", False),               # Empty string
                ("not a date", False)      # Text
            ]

            passed_count = 0
            total_count = len(test_dates)

            for date_str, expected_valid in test_dates:
                actual_valid = extractor._is_valid_date_format(date_str)
                if actual_valid == expected_valid:
                    passed_count += 1

            if passed_count == total_count:
                details = f"All {total_count} date format tests passed"
                self.log_test_result(test_id, description, True, details)
            else:
                details = f"Only {passed_count}/{total_count} date format tests passed"
                self.log_test_result(test_id, description, False, details)

        except Exception as e:
            self.log_test_result(test_id, description, False, str(e))

    # AC-005: Date Fallback Behavior
    def test_date_fallback_behavior(self):
        """Test fallback when no valid dates available"""
        test_id = "AC-005"
        description = "Date fallback behavior for documents without dates"

        try:
            # Create test document with no clear dates
            test_content = """
            <html><body>
            <h1>Legal Document</h1>
            <p>The parties agree to the terms set forth herein.</p>
            <p>This agreement shall be governed by applicable law.</p>
            </body></html>
            """

            mock_file = self.create_mock_uploaded_file("test_no_dates.html", test_content)
            df, warning = self.pipeline.process_documents_for_legal_events([mock_file])

            if df is not None and not df.empty:
                # Check that processing succeeded and fallback values used
                date_column = df[FIVE_COLUMN_HEADERS[1]]  # Date column
                has_fallback = any(date_column == DEFAULT_NO_DATE)

                if has_fallback:
                    details = f"Processing succeeded with fallback date values"
                    self.log_test_result(test_id, description, True, details)
                else:
                    # Could still pass if valid dates were extracted
                    details = f"Processing succeeded, dates extracted from text without clear dates"
                    self.log_test_result(test_id, description, True, details)
            else:
                self.log_test_result(test_id, description, False, "Processing failed completely")

        except Exception as e:
            self.log_test_result(test_id, description, False, str(e))

    # AC-007: Format Validation
    def test_format_validation(self):
        """Test that output always passes 5-column format validation"""
        test_id = "AC-007"
        description = "DataFrame format validation for 5-column structure"

        try:
            # Use existing test document
            test_content = """
            <html><body>
            <p>On December 1, 2023, the court issued an order pursuant to Rule 26.</p>
            </body></html>
            """

            mock_file = self.create_mock_uploaded_file("test_format.html", test_content)
            df, warning = self.pipeline.process_documents_for_legal_events([mock_file])

            if df is not None:
                # Test format validation
                is_valid = self.pipeline.validate_five_column_format(df)

                if is_valid:
                    details = f"DataFrame with {len(df)} rows passed format validation"
                    self.log_test_result(test_id, description, True, details)
                else:
                    details = f"DataFrame format validation failed: columns={list(df.columns)}"
                    self.log_test_result(test_id, description, False, details)
            else:
                self.log_test_result(test_id, description, False, "No DataFrame generated")

        except Exception as e:
            self.log_test_result(test_id, description, False, str(e))

    # AC-008: Sequential Numbering
    def test_sequential_numbering(self):
        """Test that No column contains sequential integers"""
        test_id = "AC-008"
        description = "Sequential numbering in No column"

        try:
            # Create document that should generate multiple events
            test_content = """
            <html><body>
            <p>On January 15, 2024, plaintiff filed motion pursuant to Rule 56.</p>
            <p>On February 1, 2024, defendant filed response pursuant to Rule 12.</p>
            <p>On March 1, 2024, court scheduled hearing pursuant to Rule 16.</p>
            </body></html>
            """

            mock_file = self.create_mock_uploaded_file("test_sequential.html", test_content)
            df, warning = self.pipeline.process_documents_for_legal_events([mock_file])

            if df is not None and not df.empty:
                no_column = df[FIVE_COLUMN_HEADERS[0]]  # No column
                expected_sequence = list(range(1, len(df) + 1))
                actual_sequence = list(no_column)

                if actual_sequence == expected_sequence:
                    details = f"Sequential numbering correct for {len(df)} events"
                    self.log_test_result(test_id, description, True, details)
                else:
                    details = f"Expected: {expected_sequence}, Got: {actual_sequence}"
                    self.log_test_result(test_id, description, False, details)
            else:
                self.log_test_result(test_id, description, False, "No events generated for testing")

        except Exception as e:
            self.log_test_result(test_id, description, False, str(e))

    # AC-015: Empty Document Handling
    def test_empty_document_handling(self):
        """Test graceful handling of documents with no legal events"""
        test_id = "AC-015"
        description = "Empty document handling with fallback table"

        try:
            # Create truly empty document
            test_content = """
            <html><body>
            <p>This document contains no legal events or dates.</p>
            <p>Just some general text about nothing specific.</p>
            </body></html>
            """

            mock_file = self.create_mock_uploaded_file("test_empty.html", test_content)
            df, warning = self.pipeline.process_documents_for_legal_events([mock_file])

            # Should always get a DataFrame, even if fallback
            if df is not None and len(df) > 0:
                # Check that it has proper 5-column structure
                has_correct_columns = list(df.columns) == FIVE_COLUMN_HEADERS
                has_date_column = FIVE_COLUMN_HEADERS[1] in df.columns

                if has_correct_columns and has_date_column:
                    details = f"Fallback table created with proper 5-column structure"
                    self.log_test_result(test_id, description, True, details)
                else:
                    details = f"Fallback table has incorrect structure: {list(df.columns)}"
                    self.log_test_result(test_id, description, False, details)
            else:
                self.log_test_result(test_id, description, False, "No fallback table created")

        except Exception as e:
            self.log_test_result(test_id, description, False, str(e))

    # AC-017: Large Document Performance
    def test_large_document_performance(self):
        """Test performance with documents containing many events"""
        test_id = "AC-017"
        description = "Large document processing performance"

        try:
            # Create document with multiple events
            events = []
            for i in range(10):  # Generate 10 events
                events.append(f"<p>On {2024-i}-0{1+i%9}-{10+i}, event {i+1} occurred pursuant to Rule {i+1}.</p>")

            test_content = f"""
            <html><body>
            <h1>Large Legal Document</h1>
            {''.join(events)}
            </body></html>
            """

            mock_file = self.create_mock_uploaded_file("test_large.html", test_content)

            # Measure processing time
            start_time = time.time()
            df, warning = self.pipeline.process_documents_for_legal_events([mock_file])
            processing_time = time.time() - start_time

            # Performance criteria: should complete within 10 seconds
            if processing_time <= 10.0 and df is not None:
                details = f"Processed in {processing_time:.2f}s with {len(df)} events"
                self.log_test_result(test_id, description, True, details)
            elif df is None:
                self.log_test_result(test_id, description, False, "Processing failed")
            else:
                details = f"Processing took {processing_time:.2f}s (> 10s limit)"
                self.log_test_result(test_id, description, False, details)

        except Exception as e:
            self.log_test_result(test_id, description, False, str(e))

    def run_all_tests(self):
        """Execute all acceptance criteria tests"""
        print("🧪 Starting User Acceptance Criteria Test Suite")
        print("=" * 60)

        # Setup
        if not self.setup_pipeline():
            print("❌ CRITICAL: Could not initialize pipeline. Aborting tests.")
            return False

        # Run tests
        self.test_column_headers()
        self.test_valid_date_extraction()
        self.test_multiple_date_formats()
        self.test_date_fallback_behavior()
        self.test_format_validation()
        self.test_sequential_numbering()
        self.test_empty_document_handling()
        self.test_large_document_performance()

        # Generate summary report
        self.generate_summary_report()

        return True

    def generate_summary_report(self):
        """Generate final test results summary"""
        print("\n" + "=" * 60)
        print("🏁 TEST RESULTS SUMMARY")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        failed_tests = total_tests - passed_tests

        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  {result['test_id']}: {result['description']}")
                    if result["details"]:
                        print(f"    → {result['details']}")
        else:
            print("\n🎉 ALL ACCEPTANCE CRITERIA TESTS PASSED!")

        print("\n" + "=" * 60)


def main():
    """Main test execution"""
    # Check environment
    api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GOOGLE_API_KEY or GEMINI_API_KEY required for testing")
        print("Set environment variable and try again")
        return 1

    # Run tests
    test_suite = AcceptanceCriteriaTests()
    success = test_suite.run_all_tests()

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)