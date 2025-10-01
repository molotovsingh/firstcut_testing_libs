"""
Date Extraction Module - Core Business Logic for Paralegal App
"""

import re
import logging
from datetime import datetime
from dateutil import parser as date_parser
from typing import List, Dict

logger = logging.getLogger(__name__)


class DateExtractor:
    """Extracts and normalizes dates from text - CORE BUSINESS USE CASE"""

    def __init__(self):
        # Comprehensive date patterns for legal documents
        self.date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or MM-DD-YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY/MM/DD or YYYY-MM-DD
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',  # Month DD, YYYY
            r'\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b',  # DD Month YYYY
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2},? \d{4}\b',  # Full month names
            r'\b\d{1,2}(?:st|nd|rd|th) (?:of )?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b',  # 1st of January 2024
        ]

    def extract_dates(self, text: str) -> List[datetime]:
        """
        Extract all dates from text and return as datetime objects

        Args:
            text: Input text to search for dates

        Returns:
            List of datetime objects found in text
        """
        dates = []

        if not text:
            return dates

        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    parsed_date = date_parser.parse(match.group(), fuzzy=True)
                    # Filter out obviously wrong dates (e.g., year > 2050 or < 1900)
                    if 1900 <= parsed_date.year <= 2050:
                        dates.append(parsed_date)
                        logger.debug(f"Found date: {match.group()} -> {parsed_date}")
                except (ValueError, TypeError) as e:
                    logger.debug(f"Failed to parse date '{match.group()}': {e}")
                    continue

        # Remove duplicates and sort
        unique_dates = list(set(dates))
        unique_dates.sort()

        logger.info(f"Extracted {len(unique_dates)} unique dates from text")
        return unique_dates

    def extract_dates_with_context(self, text: str) -> List[Dict]:
        """
        Extract dates with surrounding context for event classification

        Args:
            text: Input text to search for dates

        Returns:
            List of dictionaries with date, context, and event type
        """
        dates_with_context = []

        if not text:
            return dates_with_context

        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    parsed_date = date_parser.parse(match.group(), fuzzy=True)

                    # Filter out obviously wrong dates
                    if not (1900 <= parsed_date.year <= 2050):
                        continue

                    # Get context around the date (50 chars before and after)
                    start_pos = max(0, match.start() - 50)
                    end_pos = min(len(text), match.end() + 50)
                    context = text[start_pos:end_pos].strip()

                    # Classify the event type based on context
                    event_type = self._classify_date_event(context, match.group())

                    dates_with_context.append({
                        'date': parsed_date,
                        'original_text': match.group(),
                        'context': context,
                        'event_type': event_type,
                        'position': match.start()
                    })

                    logger.debug(f"Found date with context: {match.group()} -> {parsed_date} ({event_type})")

                except (ValueError, TypeError) as e:
                    logger.debug(f"Failed to parse date '{match.group()}': {e}")
                    continue

        # Remove duplicates based on date and sort
        seen_dates = set()
        unique_dates_with_context = []

        for item in sorted(dates_with_context, key=lambda x: x['date']):
            date_key = item['date'].strftime('%Y-%m-%d')
            if date_key not in seen_dates:
                seen_dates.add(date_key)
                unique_dates_with_context.append(item)

        logger.info(f"Extracted {len(unique_dates_with_context)} unique dates with context")
        return unique_dates_with_context

    def _classify_date_event(self, context: str, date_text: str) -> str:
        """
        Classify the type of date/event based on surrounding context

        Args:
            context: Text surrounding the date
            date_text: The original date text

        Returns:
            Event type classification
        """
        context_lower = context.lower()

        # Legal document date patterns
        if any(word in context_lower for word in ['contract', 'agreement', 'signed', 'entered into']):
            return 'Contract Date'
        elif any(word in context_lower for word in ['effective', 'commenc', 'start']):
            return 'Effective Date'
        elif any(word in context_lower for word in ['expir', 'terminat', 'end']):
            return 'Expiration Date'
        elif any(word in context_lower for word in ['due', 'deadline', 'payment due', 'submit']):
            return 'Due Date'
        elif any(word in context_lower for word in ['filed', 'filing', 'submitted']):
            return 'Filing Date'
        elif any(word in context_lower for word in ['notice', 'notif']):
            return 'Notice Date'
        elif any(word in context_lower for word in ['birth', 'born']):
            return 'Birth Date'
        elif any(word in context_lower for word in ['death', 'died', 'deceased']):
            return 'Death Date'
        elif any(word in context_lower for word in ['meeting', 'conference', 'hearing']):
            return 'Meeting Date'
        elif any(word in context_lower for word in ['today', 'current', 'as of']):
            return 'Reference Date'
        else:
            return 'General Date'

    def get_earliest_date(self, dates: List[datetime]) -> datetime:
        """Get the earliest date from a list of dates"""
        return min(dates) if dates else None

    def get_latest_date(self, dates: List[datetime]) -> datetime:
        """Get the latest date from a list of dates"""
        return max(dates) if dates else None

    def format_dates(self, dates: List[datetime], format_str: str = '%Y-%m-%d') -> List[str]:
        """Format dates as strings"""
        return [date.strftime(format_str) for date in dates]