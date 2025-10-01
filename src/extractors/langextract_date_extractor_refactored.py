"""
Simplified LangExtract Date Extractor - Uses centralized client
Minimal implementation focused only on what the pipeline needs
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
from dateutil import parser as date_parser

from ..core.langextract_client import LangExtractClient

logger = logging.getLogger(__name__)


class LangextractDateExtractor:
    """
    Simplified LangExtract date extractor using centralized client
    Returns only what the pipeline actually uses
    """

    def __init__(self):
        try:
            self.client = LangExtractClient()
            logger.info("✅ LangExtract date extractor initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LangExtract client: {e}")
            self.client = None

    def extract_structured_dates(self, text: str) -> Dict[str, Any]:
        """
        Extract dates using centralized client
        Returns only fields the pipeline actually uses
        """
        if not self.client:
            return {
                "langextract_success": False,
                "error": "LangExtract client not available",
                "all_dates": [],
                "confidence": 0.0,
                "structured_dates": {}
            }

        # Use centralized client for date extraction
        result = self.client.extract_dates(text)

        if not result.get("success", False):
            error_msg = result.get("error", "Unknown extraction error")
            logger.error(f"❌ Date extraction failed: {error_msg}")
            return {
                "langextract_success": False,
                "error": error_msg,
                "all_dates": [],
                "confidence": 0.0,
                "structured_dates": {}
            }

        # Process extracted dates
        try:
            extracted_dates = result.get("dates", [])
            processed_dates = []
            structured_dates = {}

            for date_item in extracted_dates:
                # Try to parse the date
                date_text = date_item.get("date_text", "")
                attributes = date_item.get("attributes", {})

                try:
                    # Extract actual date value
                    parsed_date = None
                    if "date" in attributes:
                        parsed_date = date_parser.parse(attributes["date"])
                    else:
                        # Try to parse from extraction text
                        parsed_date = date_parser.parse(date_text, fuzzy=True)

                    if parsed_date and 1900 <= parsed_date.year <= 2050:
                        processed_dates.append(parsed_date)

                        # Categorize by event type
                        event_type = attributes.get("event_type", "other")
                        if event_type not in structured_dates:
                            structured_dates[event_type] = []
                        structured_dates[event_type].append(parsed_date)

                except Exception as e:
                    logger.debug(f"Failed to parse date '{date_text}': {e}")
                    continue

            # Calculate confidence based on extraction success
            confidence = 0.8 if processed_dates else 0.0

            logger.info(f"✅ Extracted {len(processed_dates)} dates from {len(extracted_dates)} candidates")

            return {
                "langextract_success": True,
                "all_dates": processed_dates,
                "confidence": confidence,
                "structured_dates": structured_dates,
                "raw_extractions": extracted_dates
            }

        except Exception as e:
            logger.error(f"❌ Failed to process date extraction results: {e}")
            return {
                "langextract_success": False,
                "error": f"Date processing error: {str(e)}",
                "all_dates": [],
                "confidence": 0.0,
                "structured_dates": {}
            }

    def is_available(self) -> bool:
        """Check if LangExtract is available"""
        return self.client and self.client.is_available()

    def get_required_env_vars(self) -> List[str]:
        """Return required environment variables"""
        return self.client.get_required_env_vars() if self.client else ["GEMINI_API_KEY"]