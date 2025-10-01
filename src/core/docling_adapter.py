"""
Docling Document Extractor Adapter
Wraps DocumentProcessor with configured options to implement DocumentExtractor interface
"""

import logging
from pathlib import Path
from typing import List

from .interfaces import DocumentExtractor, ExtractedDocument
from .document_processor import DocumentProcessor
from .config import DoclingConfig

logger = logging.getLogger(__name__)


class DoclingDocumentExtractor:
    """Adapter that wraps DocumentProcessor to implement DocumentExtractor interface"""

    def __init__(self, config: DoclingConfig):
        """
        Initialize with Docling configuration

        Args:
            config: DoclingConfig instance with all Docling settings
        """
        self.config = config
        self.processor = DocumentProcessor(config)
        logger.info("✅ DoclingDocumentExtractor initialized")

    def extract(self, file_path: Path) -> ExtractedDocument:
        """
        Extract text using configured DocumentProcessor

        Args:
            file_path: Path to the document file

        Returns:
            ExtractedDocument with markdown, plain_text and metadata
        """
        try:
            # Get file extension from path
            file_type = file_path.suffix.lstrip('.')

            # Use DocumentProcessor to get Docling result
            text, extraction_method = self.processor.extract_text(file_path, file_type)

            if extraction_method == "failed" or not text.strip():
                # Return empty strings instead of error flags
                return ExtractedDocument(
                    markdown="",
                    plain_text="",
                    metadata={
                        "file_path": str(file_path),
                        "file_type": file_type,
                        "extraction_method": "failed",
                        "config": {
                            "do_ocr": self.config.do_ocr,
                            "table_mode": self.config.table_mode,
                            "backend": self.config.backend
                        }
                    }
                )

            # For Docling extractions, get both markdown and plain text
            if extraction_method == "docling":
                # Re-run Docling to get both formats
                result = self.processor.converter.convert(file_path)
                markdown = result.document.export_to_markdown()
                plain_text = result.document.export_to_text()
            else:
                # For non-Docling extractions (email, etc.), text is plain text
                markdown = text  # Use same content for both
                plain_text = text

            return ExtractedDocument(
                markdown=markdown,
                plain_text=plain_text,
                metadata={
                    "file_path": str(file_path),
                    "file_type": file_type,
                    "extraction_method": extraction_method,
                    "config": {
                        "do_ocr": self.config.do_ocr,
                        "table_mode": self.config.table_mode,
                        "backend": self.config.backend
                    }
                }
            )

        except Exception as e:
            logger.error(f"❌ DoclingDocumentExtractor failed for {file_path.name}: {e}")
            # Return empty strings on exception
            return ExtractedDocument(
                markdown="",
                plain_text="",
                metadata={
                    "file_path": str(file_path),
                    "file_type": file_path.suffix.lstrip('.'),
                    "extraction_method": "failed",
                    "error": str(e)
                }
            )

    def get_supported_types(self) -> List[str]:
        """
        Get supported file types from DocumentProcessor

        Returns:
            List of supported file extensions
        """
        return self.processor.get_supported_types()