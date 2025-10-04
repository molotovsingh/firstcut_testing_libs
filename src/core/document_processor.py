"""
Core Document Processing Module - Docling Integration with Configurable Options
"""

import logging
from pathlib import Path
from typing import Tuple, Optional
from docling.document_converter import DocumentConverter, FormatOption
from docling.datamodel.pipeline_options import (
    ConvertPipelineOptions,
    PdfPipelineOptions,
    TableStructureOptions,
    AcceleratorOptions,
    TableFormerMode
)
from docling.datamodel.base_models import InputFormat
from docling.backend.docling_parse_v2_backend import DoclingParseV2DocumentBackend
from docling.backend.docling_parse_v4_backend import DoclingParseV4DocumentBackend
from docling.backend.msword_backend import MsWordDocumentBackend
from docling.backend.mspowerpoint_backend import MsPowerpointDocumentBackend
from docling.backend.html_backend import HTMLDocumentBackend
from docling.pipeline.simple_pipeline import SimplePipeline
try:
    from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
except ImportError:  # pragma: no cover
    StandardPdfPipeline = None  # type: ignore
import extract_msg

from .config import DoclingConfig, load_config

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Handles document text extraction using Docling with configurable options"""

    def __init__(self, config: Optional[DoclingConfig] = None):
        """
        Initialize DocumentProcessor with configurable Docling options

        Args:
            config: DoclingConfig instance, defaults to loaded from environment
        """
        if config is None:
            config, _ = load_config()

        self.config = config

        # Build accelerator options
        accelerator_options = AcceleratorOptions(
            device=config.accelerator_device,
            num_threads=config.accelerator_threads
        )

        # Build table structure options
        table_mode = TableFormerMode.ACCURATE if config.table_mode == "ACCURATE" else TableFormerMode.FAST
        table_options = TableStructureOptions(
            mode=table_mode,
            do_cell_matching=config.do_cell_matching
        )

        # Build OCR options based on configured engine
        ocr_options = None
        if config.do_ocr:
            if config.ocr_engine == "tesseract":
                from docling.datamodel.pipeline_options import TesseractOcrOptions
                # Validate TESSDATA_PREFIX for Tesseract
                import os
                tessdata = os.getenv("TESSDATA_PREFIX")
                if not tessdata:
                    logger.warning("⚠️ TESSDATA_PREFIX not set - Tesseract OCR may fail. "
                                   "Set it to your Tesseract language data directory.")
                ocr_options = TesseractOcrOptions()
                logger.info(f"✅ Using Tesseract OCR (TESSDATA_PREFIX: {tessdata or 'NOT SET'})")
            elif config.ocr_engine == "ocrmac":
                from docling.datamodel.pipeline_options import OcrMacOptions
                ocr_options = OcrMacOptions()
                logger.info("✅ Using OCRmac (macOS Vision Framework)")
            elif config.ocr_engine == "rapidocr":
                from docling.datamodel.pipeline_options import RapidOcrOptions
                ocr_options = RapidOcrOptions()
                logger.info("✅ Using RapidOCR (lightweight)")
            else:  # easyocr (fallback)
                from docling.datamodel.pipeline_options import EasyOcrOptions
                ocr_options = EasyOcrOptions()
                logger.info("✅ Using EasyOCR (PyTorch-based)")

        # Build format options for each supported document type with appropriate backends
        format_options = {}

        # PDF format with configurable backend and pipeline
        if config.backend == "v2":
            # Parse V2: Use ConvertPipelineOptions + SimplePipeline
            pdf_backend = DoclingParseV2DocumentBackend
            pdf_pipeline = SimplePipeline
            pdf_pipeline_options = ConvertPipelineOptions(
                accelerator_options=accelerator_options,
                artifacts_path=config.artifacts_path,
                document_timeout=config.document_timeout
            )
            logger.info("✅ Using Docling Parse V2 backend with SimplePipeline for PDF")
        else:
            # Parse V4: Use PdfPipelineOptions + StandardPdfPipeline
            pdf_backend = DoclingParseV4DocumentBackend  # Default modern backend
            if StandardPdfPipeline is None:
                raise ImportError(
                    "Docling Parse V4 backend requires docling.pipeline.standard_pdf_pipeline."
                )
            pdf_pipeline = StandardPdfPipeline
            # Construct PdfPipelineOptions; avoid passing ocr_options when OCR is disabled
            kwargs = dict(
                # Base options
                accelerator_options=accelerator_options,
                artifacts_path=config.artifacts_path,
                document_timeout=config.document_timeout,

                # PDF-specific options mapped from DoclingConfig
                do_ocr=config.do_ocr,
                do_table_structure=config.do_table_structure,
                table_structure_options=table_options,

                # Optimized defaults for legal document processing
                generate_page_images=False,  # Performance optimization
                images_scale=1.0,
                generate_picture_images=False,
                generate_table_images=False,
                generate_parsed_pages=False,
            )
            # Only provide explicit ocr_options if OCR is enabled; otherwise let
            # PdfPipelineOptions use its default (avoids pydantic validation error)
            if config.do_ocr and ocr_options is not None:
                kwargs["ocr_options"] = ocr_options
            pdf_pipeline_options = PdfPipelineOptions(**kwargs)
            logger.info("✅ Using Docling Parse V4 backend with StandardPdfPipeline for PDF")

        format_options[InputFormat.PDF] = FormatOption(
            pipeline_options=pdf_pipeline_options,
            backend=pdf_backend,
            pipeline_cls=pdf_pipeline
        )

        # Non-PDF formats continue using ConvertPipelineOptions
        non_pdf_pipeline_options = ConvertPipelineOptions(
            accelerator_options=accelerator_options,
            artifacts_path=config.artifacts_path,
            document_timeout=config.document_timeout
        )

        # Word documents
        format_options[InputFormat.DOCX] = FormatOption(
            pipeline_options=non_pdf_pipeline_options,
            backend=MsWordDocumentBackend,
            pipeline_cls=SimplePipeline
        )

        # PowerPoint documents
        format_options[InputFormat.PPTX] = FormatOption(
            pipeline_options=non_pdf_pipeline_options,
            backend=MsPowerpointDocumentBackend,
            pipeline_cls=SimplePipeline
        )

        # HTML documents
        format_options[InputFormat.HTML] = FormatOption(
            pipeline_options=non_pdf_pipeline_options,
            backend=HTMLDocumentBackend,
            pipeline_cls=SimplePipeline
        )

        # Initialize DocumentConverter with full configuration
        self.converter = DocumentConverter(format_options=format_options)

        logger.info(f"✅ DocumentProcessor initialized with config: OCR={config.do_ocr}, "
                   f"Table={config.table_mode}, Device={config.accelerator_device}, "
                   f"Backend={config.backend}, Timeout={config.document_timeout}s")

    def extract_text(self, file_path: Path, file_type: str) -> Tuple[str, str]:
        """
        Extract text from document using DOCLING ONLY - Pure test pipeline

        Args:
            file_path: Path to the document
            file_type: File extension without dot

        Returns:
            Tuple of (extracted_text, extraction_method)
        """
        try:
            text = ""
            extraction_method = "failed"

            if file_type in ['pdf', 'docx', 'txt', 'pptx', 'html']:
                # PURE DOCLING PROCESSING - NO FALLBACKS
                result = self.converter.convert(file_path)
                text = result.document.export_to_markdown()
                extraction_method = "docling"
                logger.info(f"✅ DOCLING SUCCESS: {file_path.name}")

            elif file_type in ['eml', 'msg']:
                # Only email files use extract_msg
                if file_type == 'msg':
                    msg = extract_msg.openMsg(file_path)
                    text = f"Subject: {msg.subject}\nFrom: {msg.sender}\nDate: {msg.date}\n\n{msg.body}"
                    extraction_method = "extract_msg"
                else:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()
                    extraction_method = "raw_text"

            return text.strip(), extraction_method

        except Exception as e:
            logger.error(f"❌ DOCLING FAILED: {file_path.name} - {str(e)}")
            return "", "failed"

    def get_supported_types(self) -> list[str]:
        """Get list of supported file types"""
        return ['pdf', 'docx', 'txt', 'pptx', 'html', 'eml', 'msg']
