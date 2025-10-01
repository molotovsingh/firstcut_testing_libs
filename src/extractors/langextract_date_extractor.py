"""
Langextract Date Extractor - PROPER LLM-powered structured date extraction
This is the TRUE test of langextract for paralegal applications
"""

import logging
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
from dateutil import parser as date_parser

try:
    import langextract
    LANGEXTRACT_AVAILABLE = True
except ImportError:
    LANGEXTRACT_AVAILABLE = False

logger = logging.getLogger(__name__)


class LangextractDateExtractor:
    """
    Proper langextract implementation for structured date extraction
    Uses LLM-powered extraction with examples and schemas
    """

    def __init__(self):
        self.available = LANGEXTRACT_AVAILABLE
        self.extractor = None

        if self.available:
            try:
                # Initialize langextract with proper configuration
                self._setup_extractor()
            except Exception as e:
                logger.error(f"Failed to initialize langextract: {e}")
                self.available = False

    def _setup_extractor(self):
        """Setup langextract with proper configuration for date extraction"""
        try:
            # Check for API key (usually Gemini for Google's implementation)
            api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            if not api_key:
                logger.warning("No Gemini/Google API key found. Langextract may not work properly.")
                self.available = False
                return

            # Define extraction schema for legal date extraction
            self.date_extraction_schema = {
                "extraction_class": "LegalDateExtraction",
                "fields": {
                    "contract_date": {
                        "type": "date",
                        "description": "The primary contract or agreement date"
                    },
                    "effective_date": {
                        "type": "date",
                        "description": "When the contract or agreement becomes effective"
                    },
                    "expiration_date": {
                        "type": "date",
                        "description": "When the contract or agreement expires"
                    },
                    "filing_date": {
                        "type": "date",
                        "description": "Date when document was filed or submitted"
                    },
                    "due_date": {
                        "type": "date",
                        "description": "Any due dates or deadlines mentioned"
                    },
                    "other_dates": {
                        "type": "list[date]",
                        "description": "Any other significant dates mentioned in the document"
                    }
                }
            }

            # Create few-shot examples for the extractor
            self.examples = [
                {
                    "text": "This Agreement is entered into on March 15, 2024, and shall become effective on April 1, 2024. The contract expires on December 31, 2025.",
                    "extraction": {
                        "contract_date": "2024-03-15",
                        "effective_date": "2024-04-01",
                        "expiration_date": "2025-12-31",
                        "filing_date": None,
                        "due_date": None,
                        "other_dates": []
                    }
                },
                {
                    "text": "Filed on January 10, 2023. Payment is due by February 28, 2023. The original contract was signed on November 5, 2022.",
                    "extraction": {
                        "contract_date": "2022-11-05",
                        "effective_date": None,
                        "expiration_date": None,
                        "filing_date": "2023-01-10",
                        "due_date": "2023-02-28",
                        "other_dates": []
                    }
                }
            ]

            # Initialize the extractor (implementation depends on langextract version)
            self.extractor = self._create_extractor()

        except Exception as e:
            logger.error(f"Langextract setup failed: {e}")
            self.available = False

    def _create_extractor(self):
        """Create the REAL langextract configuration using correct API"""
        try:
            # REAL LANGEXTRACT IMPLEMENTATION - TRUE TEST OF LIBRARY
            import langextract as lx

            # Get API key
            api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            if not api_key:
                logger.error("No API key found for langextract")
                return None

            # Store configuration for langextract.extract() calls - using actual API from README
            self.langextract_config = {
                'api_key': api_key,
                'model_id': 'gemini-2.0-flash-exp',  # Use latest model from sample
                'prompt_description': 'Extract every legally meaningful date and provide a normalized ISO date.'
            }

            # Create few-shot examples using correct API structure from README
            self.examples = [
                lx.data.ExampleData(
                    text="This Agreement is entered into on March 15, 2024, and shall become effective on April 1, 2024. The contract expires on December 31, 2025.",
                    extractions=[
                        lx.data.Extraction(
                            extraction_class="contract_date",
                            extraction_text="March 15, 2024",
                            attributes={"normalized_date": "2024-03-15", "type": "signing_date"}
                        ),
                        lx.data.Extraction(
                            extraction_class="effective_date",
                            extraction_text="April 1, 2024",
                            attributes={"normalized_date": "2024-04-01", "type": "effective_date"}
                        ),
                        lx.data.Extraction(
                            extraction_class="expiration_date",
                            extraction_text="December 31, 2025",
                            attributes={"normalized_date": "2025-12-31", "type": "expiration_date"}
                        )
                    ]
                ),
                lx.data.ExampleData(
                    text="Filed on January 10, 2023. Payment is due by February 28, 2023. The original contract was signed on November 5, 2022.",
                    extractions=[
                        lx.data.Extraction(
                            extraction_class="filing_date",
                            extraction_text="January 10, 2023",
                            attributes={"normalized_date": "2023-01-10", "type": "filing_date"}
                        ),
                        lx.data.Extraction(
                            extraction_class="due_date",
                            extraction_text="February 28, 2023",
                            attributes={"normalized_date": "2023-02-28", "type": "due_date"}
                        ),
                        lx.data.Extraction(
                            extraction_class="contract_date",
                            extraction_text="November 5, 2022",
                            attributes={"normalized_date": "2022-11-05", "type": "signing_date"}
                        )
                    ]
                )
            ]

            logger.info("✅ REAL LANGEXTRACT CONFIGURATION initialized successfully using correct API")
            return True  # Return True to indicate success

        except ImportError as e:
            logger.error(f"Langextract import failed: {e}")
            logger.error("Make sure langextract is properly installed from Google's repository")
            return None
        except Exception as e:
            logger.error(f"Failed to configure REAL langextract: {e}")
            return None

    def extract_structured_dates(self, text: str) -> Dict[str, Any]:
        """
        Extract structured dates using langextract LLM-powered extraction

        Args:
            text: Input document text

        Returns:
            Dictionary with structured date extraction results
        """
        if not self.available:
            # Per README: "If Gemini access is missing, halt and report the gap—do not introduce regex or other fallbacks"
            logger.error("❌ LANGEXTRACT NOT AVAILABLE - Halting per README guardrails")
            return {
                "langextract_success": False,
                "extraction_method": "langextract_unavailable",
                "structured_dates": {},
                "all_dates": [],
                "confidence": 0.0,
                "source_spans": [],
                "error": "API key missing - operation failed per README guardrails",
                "error_category": "api_key_missing"
            }

        try:
            # REAL LANGEXTRACT API CALL - TRUE TEST using correct API from README!
            import langextract as lx

            logger.info("🚀 Making REAL langextract API call to Gemini using correct API...")

            # Call the REAL langextract.extract() function with correct API structure from README
            response = lx.extract(
                text_or_documents=text,
                prompt_description=self.langextract_config['prompt_description'],
                examples=self.examples,
                model_id=self.langextract_config['model_id'],
                api_key=self.langextract_config['api_key']
            )

            # Process the REAL langextract response
            structured_dates = self._process_langextract_response(response)

            logger.info(f"✅ REAL LANGEXTRACT SUCCESS: Extracted {len(structured_dates.get('all_dates', []))} structured dates")
            logger.info(f"📊 Langextract extractions found: {len(response.extractions)}")

            return structured_dates

        except Exception as e:
            logger.error(f"❌ REAL LANGEXTRACT FAILED: {str(e)}")
            logger.error("Per README guardrails: NOT falling back to regex - halting langextract test")

            # Per README: "If Gemini access is missing, halt and report the gap—do not introduce regex or other fallbacks"
            return {
                "langextract_success": False,
                "extraction_method": "langextract_failed",
                "structured_dates": {},
                "all_dates": [],
                "confidence": 0.0,
                "source_spans": [],
                "error": str(e),
                "error_category": "langextract_execution_failed"
            }

    def _process_langextract_response(self, response) -> Dict[str, Any]:
        """Process REAL langextract response using correct API structure from README"""
        processed = {
            "langextract_success": True,
            "extraction_method": "langextract_llm",
            "structured_dates": {},
            "all_dates": [],
            "confidence": 0.8,  # High confidence for successful LLM extraction
            "source_spans": [],
            "raw_extractions": []  # Store raw extractions for debugging
        }

        try:
            logger.info(f"🔍 Processing langextract response with {len(response.extractions)} extractions")

            all_dates = []

            # Process each extraction using the correct API structure from README
            for item in response.extractions:
                extraction_class = item.extraction_class
                extraction_text = item.extraction_text
                attributes = item.attributes or {}

                # Log each extraction for debugging
                logger.info(f"📅 Found: {extraction_class} → {extraction_text} → {attributes.get('normalized_date', 'N/A')}")

                # Store raw extraction for debugging
                processed["raw_extractions"].append({
                    "class": extraction_class,
                    "text": extraction_text,
                    "attributes": attributes
                })

                # Parse the normalized date if available
                normalized_date = attributes.get('normalized_date')
                if normalized_date:
                    try:
                        parsed_date = date_parser.parse(normalized_date)
                        all_dates.append(parsed_date)

                        # Store in structured format
                        if extraction_class not in processed["structured_dates"]:
                            processed["structured_dates"][extraction_class] = []
                        processed["structured_dates"][extraction_class].append({
                            "date": parsed_date,
                            "original_text": extraction_text,
                            "normalized": normalized_date,
                            "attributes": attributes
                        })

                    except Exception as e:
                        logger.warning(f"Failed to parse normalized date '{normalized_date}': {e}")
                        # Try parsing the original extraction text
                        try:
                            parsed_date = date_parser.parse(extraction_text, fuzzy=True)
                            if 1900 <= parsed_date.year <= 2050:
                                all_dates.append(parsed_date)
                        except Exception:
                            logger.warning(f"Failed to parse extraction text '{extraction_text}'")

            # Remove duplicates and sort
            processed["all_dates"] = sorted(list(set(all_dates)))
            logger.info(f"📊 Successfully processed {len(processed['all_dates'])} unique dates from langextract")

        except Exception as e:
            logger.error(f"Failed to process langextract response: {e}")
            processed["langextract_success"] = False
            processed["error"] = str(e)

        return processed

    def _process_langextract_result(self, result: Dict) -> Dict[str, Any]:
        """Process REAL langextract extraction result"""
        processed = {
            "langextract_success": True,
            "extraction_method": "langextract_llm",
            "structured_dates": {},
            "all_dates": [],
            "confidence": 0.0,
            "source_spans": [],
            "raw_result": result  # Store raw result for debugging
        }

        try:
            logger.info(f"🔍 Processing langextract result: {result}")

            # Handle the actual langextract response format
            # The exact format depends on langextract's implementation
            if isinstance(result, dict):
                # Case 1: Result has extractions field
                if "extractions" in result:
                    extractions = result["extractions"]
                    if extractions and len(extractions) > 0:
                        extraction = extractions[0]
                        self._process_extraction_fields(extraction, processed)

                # Case 2: Result is direct field mapping
                elif any(field in result for field in ["contract_date", "effective_date", "expiration_date", "filing_date", "due_date"]):
                    self._process_extraction_fields(result, processed)

                # Case 3: Result has different structure
                else:
                    logger.warning(f"Unexpected langextract result format: {result.keys()}")
                    self._process_generic_result(result, processed)

            else:
                logger.warning(f"Unexpected langextract result type: {type(result)}")
                processed["langextract_success"] = False

            # Calculate overall confidence
            if processed["all_dates"]:
                processed["confidence"] = processed.get("confidence", 0.8)  # Default high confidence if dates found
            else:
                processed["confidence"] = 0.0

            logger.info(f"📊 Processed {len(processed['all_dates'])} dates from langextract")

        except Exception as e:
            logger.error(f"Failed to process langextract result: {e}")
            processed["langextract_success"] = False

        return processed

    def _process_extraction_fields(self, extraction: Dict, processed: Dict):
        """Process individual extraction fields"""
        # Standard date fields for legal documents
        date_fields = ["contract_date", "effective_date", "expiration_date", "filing_date", "due_date", "other_important_dates"]
        all_dates = []

        for field in date_fields:
            field_value = extraction.get(field)
            if field_value:
                # Handle different value formats
                if isinstance(field_value, list):
                    # Multiple dates in this field
                    for date_str in field_value:
                        date_obj = self._parse_date_safely(date_str)
                        if date_obj:
                            all_dates.append(date_obj)
                            processed["structured_dates"][field] = processed["structured_dates"].get(field, [])
                            if not isinstance(processed["structured_dates"][field], list):
                                processed["structured_dates"][field] = [processed["structured_dates"][field]]
                            processed["structured_dates"][field].append(date_obj)
                else:
                    # Single date
                    date_obj = self._parse_date_safely(field_value)
                    if date_obj:
                        all_dates.append(date_obj)
                        processed["structured_dates"][field] = date_obj

        # Remove duplicates and sort
        processed["all_dates"] = sorted(list(set(all_dates)))

        # Extract confidence and spans if available
        processed["confidence"] = extraction.get("confidence", 0.8)
        processed["source_spans"] = extraction.get("spans", extraction.get("source_spans", []))

    def _process_generic_result(self, result: Dict, processed: Dict):
        """Process generic result format"""
        all_dates = []

        # Try to extract any date-like values from the result
        for key, value in result.items():
            if "date" in key.lower():
                if isinstance(value, list):
                    for item in value:
                        date_obj = self._parse_date_safely(item)
                        if date_obj:
                            all_dates.append(date_obj)
                else:
                    date_obj = self._parse_date_safely(value)
                    if date_obj:
                        all_dates.append(date_obj)

        processed["all_dates"] = sorted(list(set(all_dates)))

    def _parse_date_safely(self, date_str) -> Optional[datetime]:
        """Safely parse a date string"""
        try:
            if isinstance(date_str, str) and date_str.strip():
                parsed_date = date_parser.parse(date_str, fuzzy=True)
                # Validate reasonable date range
                if 1900 <= parsed_date.year <= 2050:
                    return parsed_date
        except Exception as e:
            logger.debug(f"Failed to parse date '{date_str}': {e}")
        return None


    def is_available(self) -> bool:
        """Check if langextract is properly configured and available"""
        return self.available

    def get_required_env_vars(self) -> List[str]:
        """Get list of required environment variables"""
        return ["GEMINI_API_KEY", "GOOGLE_API_KEY"]

    def get_extraction_schema(self) -> Dict:
        """Get the extraction schema used by langextract"""
        return self.date_extraction_schema