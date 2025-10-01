"""
Language Analysis Module - Simple Language Detection
Note: Google's Langextract is for complex structured data extraction, not simple language detection
"""

import logging
import textstat
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class LanguageAnalyzer:
    """Simple language detection and text analysis"""

    def __init__(self):
        # Common words for basic language detection
        self.language_indicators = {
            'english': ['the', 'and', 'of', 'to', 'in', 'is', 'it', 'you', 'that', 'he', 'was', 'for', 'on', 'are', 'as'],
            'spanish': ['de', 'la', 'el', 'en', 'y', 'a', 'es', 'se', 'no', 'te', 'un', 'por', 'con', 'su', 'para'],
            'french': ['le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir', 'que', 'pour', 'dans', 'ce', 'son'],
        }

        # Stop words for keyword extraction
        self.stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'a', 'an', 'from', 'up', 'about', 'into', 'through',
            'during', 'before', 'after', 'above', 'below', 'out', 'off', 'over', 'under',
            'again', 'further', 'then', 'once'
        }

    def detect_language(self, text: str) -> str:
        """
        Simple language detection based on common words

        Args:
            text: Input text to analyze

        Returns:
            Detected language string
        """
        if not text:
            return 'unknown'

        text_lower = text.lower()
        scores = {}

        for language, indicators in self.language_indicators.items():
            score = sum(1 for word in indicators if word in text_lower)
            scores[language] = score

        # Return language with highest score
        if scores:
            detected = max(scores, key=scores.get)
            if scores[detected] > 0:
                logger.info(f"Language detected: {detected} (score: {scores[detected]})")
                return detected

        return 'unknown'

    def analyze_content(self, text: str) -> Dict:
        """
        Comprehensive text analysis

        Args:
            text: Input text to analyze

        Returns:
            Dictionary with analysis results
        """
        if not text:
            return {
                'word_count': 0,
                'character_count': 0,
                'sentence_count': 0,
                'paragraph_count': 0,
                'reading_time': 0,
                'language': 'unknown',
                'keywords': [],
                'flesch_reading_ease': 0,
                'grade_level': 0,
                'analysis_success': False
            }

        try:
            analysis = {
                'word_count': len(text.split()),
                'character_count': len(text),
                'sentence_count': text.count('.') + text.count('!') + text.count('?'),
                'paragraph_count': len([p for p in text.split('\n\n') if p.strip()]),
                'reading_time': round(len(text.split()) / 200, 1),  # Average reading speed
                'language': self.detect_language(text),
                'keywords': self.extract_keywords(text)[:10],  # Top 10 keywords
                'flesch_reading_ease': textstat.flesch_reading_ease(text),
                'grade_level': textstat.flesch_kincaid_grade(text),
                'analysis_success': True
            }

            logger.info(f"Content analysis completed: {analysis['word_count']} words, {analysis['language']} language")
            return analysis

        except Exception as e:
            logger.error(f"Content analysis failed: {str(e)}")
            return {
                'word_count': 0,
                'character_count': len(text) if text else 0,
                'sentence_count': 0,
                'paragraph_count': 0,
                'reading_time': 0,
                'language': 'FAILED',
                'keywords': [],
                'flesch_reading_ease': 0,
                'grade_level': 0,
                'analysis_success': False
            }

    def extract_keywords(self, text: str, min_length: int = 3) -> List[Tuple[str, int]]:
        """
        Extract keywords from text with frequency counts

        Args:
            text: Input text
            min_length: Minimum word length

        Returns:
            List of tuples (word, frequency) sorted by frequency
        """
        import re

        # Extract words
        words = re.findall(r'\b[a-zA-Z]{' + str(min_length) + ',}\b', text.lower())

        # Filter and count words
        word_freq = {}
        for word in words:
            if word not in self.stop_words and len(word) >= min_length:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency
        return sorted(word_freq.items(), key=lambda x: x[1], reverse=True)