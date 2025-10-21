"""
DeepSeek-OCR Document Extractor Adapter
Implements DocumentExtractor interface using DeepSeek-OCR for vision-based OCR
"""

import logging
from pathlib import Path
from typing import List, Optional
import os
import tempfile

from .interfaces import DocumentExtractor, ExtractedDocument

logger = logging.getLogger(__name__)


class DeepSeekOCRDocumentExtractor:
    """
    Adapter for DeepSeek-OCR vision model for document extraction

    DeepSeek-OCR is a 3B-parameter vision-language model that converts documents
    to Markdown using visual perception. Requires GPU with CUDA support.

    Requirements:
        - CUDA 11.8+ GPU
        - PyTorch 2.6.0
        - transformers 4.46.3
        - flash-attn 2.7.3
        - ~4GB+ GPU memory

    Features:
        - Converts PDFs and images to Markdown
        - Layout-aware parsing (preserves structure)
        - 7-20x token compression vs traditional OCR
        - MIT licensed (free for commercial use)

    Limitations:
        - Requires GPU (no CPU fallback)
        - Slower than CPU-based OCR (~2-3s per page on A100)
        - Large model download (~6GB)
    """

    def __init__(self, model_name: str = "deepseek-ai/DeepSeek-OCR", device: str = "cuda:0"):
        """
        Initialize DeepSeek-OCR extractor

        Args:
            model_name: Hugging Face model identifier
            device: CUDA device to use (e.g., "cuda:0")

        Raises:
            RuntimeError: If CUDA not available or dependencies missing
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        self.tokenizer = None
        self._initialized = False
        self._availability_checked = False
        self._is_available = False

        logger.info(f"🔧 DeepSeekOCRDocumentExtractor created (lazy initialization)")

    def _check_availability(self) -> bool:
        """
        Check if DeepSeek-OCR can run in this environment

        Returns:
            True if all requirements met, False otherwise
        """
        if self._availability_checked:
            return self._is_available

        self._availability_checked = True

        try:
            import torch

            if not torch.cuda.is_available():
                logger.warning("❌ CUDA not available - DeepSeek-OCR requires GPU")
                self._is_available = False
                return False

            # Check CUDA version
            cuda_version = torch.version.cuda
            if cuda_version:
                major, minor = map(int, cuda_version.split('.')[:2])
                if major < 11 or (major == 11 and minor < 8):
                    logger.warning(f"❌ CUDA {cuda_version} detected - DeepSeek-OCR requires 11.8+")
                    self._is_available = False
                    return False

            logger.info(f"✅ CUDA {cuda_version} available on {torch.cuda.get_device_name(0)}")
            self._is_available = True
            return True

        except ImportError as e:
            logger.warning(f"❌ PyTorch not installed - DeepSeek-OCR requires torch 2.6.0+: {e}")
            self._is_available = False
            return False
        except Exception as e:
            logger.warning(f"❌ Availability check failed: {e}")
            self._is_available = False
            return False

    def _initialize_model(self):
        """
        Lazy initialization of DeepSeek-OCR model

        Raises:
            RuntimeError: If model initialization fails
        """
        if self._initialized:
            return

        if not self._check_availability():
            raise RuntimeError(
                "DeepSeek-OCR not available. Requirements:\n"
                "  - CUDA 11.8+ GPU\n"
                "  - PyTorch 2.6.0+\n"
                "  - transformers 4.46.3+\n"
                "  - flash-attn 2.7.3\n"
                "See docs/deepseek_ocr_setup.md for installation instructions"
            )

        try:
            import torch
            from transformers import AutoModel, AutoTokenizer

            logger.info(f"📥 Loading DeepSeek-OCR model: {self.model_name}")
            logger.info("⏳ First-time download may take several minutes (~6GB)")

            # Set CUDA device
            os.environ["CUDA_VISIBLE_DEVICES"] = self.device.split(':')[1] if ':' in self.device else '0'

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )

            # Load model with flash attention
            self.model = AutoModel.from_pretrained(
                self.model_name,
                attn_implementation='flash_attention_2',
                trust_remote_code=True,
                use_safetensors=True
            )

            # Move to GPU and convert to bfloat16
            self.model = self.model.eval().cuda().to(torch.bfloat16)

            self._initialized = True
            logger.info(f"✅ DeepSeek-OCR model loaded on {torch.cuda.get_device_name(0)}")

        except ImportError as e:
            raise RuntimeError(
                f"Missing dependencies for DeepSeek-OCR: {e}\n"
                f"Install with: pip install transformers==4.46.3 flash-attn==2.7.3"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize DeepSeek-OCR model: {e}")

    def _convert_pdf_to_images(self, pdf_path: Path) -> List[Path]:
        """
        Convert PDF to images for processing

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of paths to temporary image files
        """
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(pdf_path)
            image_paths = []
            temp_dir = Path(tempfile.mkdtemp(prefix="deepseek_ocr_"))

            for page_num in range(len(doc)):
                page = doc[page_num]
                # Render at 2x resolution for better OCR quality
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

                img_path = temp_dir / f"page_{page_num + 1}.png"
                pix.save(str(img_path))
                image_paths.append(img_path)

            doc.close()
            logger.info(f"📄 Converted PDF to {len(image_paths)} images")
            return image_paths

        except ImportError:
            raise RuntimeError("PyMuPDF (fitz) required for PDF processing: pip install PyMuPDF")
        except Exception as e:
            raise RuntimeError(f"Failed to convert PDF to images: {e}")

    def _extract_from_image(self, image_path: Path) -> str:
        """
        Extract markdown from a single image

        Args:
            image_path: Path to image file

        Returns:
            Extracted markdown text
        """
        if not self._initialized:
            self._initialize_model()

        try:
            import torch
            from PIL import Image

            # Load image
            image = Image.open(image_path)

            # DeepSeek-OCR prompt for document conversion
            prompt = "<image>\n<|grounding|>Convert the document to markdown."

            # Process image
            inputs = self.tokenizer(
                prompt,
                images=[image],
                return_tensors="pt"
            ).to(self.device)

            # Generate markdown
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=2048,
                    do_sample=False,
                    temperature=0.0
                )

            # Decode output
            markdown = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Remove prompt from output
            if prompt in markdown:
                markdown = markdown.replace(prompt, "").strip()

            return markdown

        except Exception as e:
            logger.error(f"❌ DeepSeek-OCR extraction failed for {image_path.name}: {e}")
            raise

    def extract(self, file_path: Path) -> ExtractedDocument:
        """
        Extract text from document using DeepSeek-OCR

        Args:
            file_path: Path to document file (PDF or image)

        Returns:
            ExtractedDocument with markdown, plain_text, and metadata
        """
        if not self._check_availability():
            return ExtractedDocument(
                markdown="",
                plain_text="",
                metadata={
                    "file_path": str(file_path),
                    "file_type": file_path.suffix.lstrip('.'),
                    "extraction_method": "deepseek_ocr_failed",
                    "error": "GPU not available - DeepSeek-OCR requires CUDA 11.8+ GPU"
                }
            )

        try:
            file_type = file_path.suffix.lstrip('.').lower()
            markdown_parts = []

            # Handle PDFs (convert to images first)
            if file_type == 'pdf':
                logger.info(f"📄 Processing PDF: {file_path.name}")
                image_paths = self._convert_pdf_to_images(file_path)

                try:
                    for idx, img_path in enumerate(image_paths, 1):
                        logger.info(f"  📸 Processing page {idx}/{len(image_paths)}")
                        page_markdown = self._extract_from_image(img_path)
                        markdown_parts.append(page_markdown)

                        # Add page separator
                        if idx < len(image_paths):
                            markdown_parts.append("\n\n---\n\n")

                finally:
                    # Cleanup temporary images
                    for img_path in image_paths:
                        try:
                            img_path.unlink()
                        except:
                            pass
                    try:
                        img_path.parent.rmdir()
                    except:
                        pass

            # Handle images directly
            elif file_type in ['png', 'jpg', 'jpeg', 'tiff', 'bmp']:
                logger.info(f"🖼️ Processing image: {file_path.name}")
                page_markdown = self._extract_from_image(file_path)
                markdown_parts.append(page_markdown)

            else:
                return ExtractedDocument(
                    markdown="",
                    plain_text="",
                    metadata={
                        "file_path": str(file_path),
                        "file_type": file_type,
                        "extraction_method": "deepseek_ocr_failed",
                        "error": f"Unsupported file type: {file_type}"
                    }
                )

            # Combine all markdown parts
            markdown = "".join(markdown_parts)

            # Convert markdown to plain text (simple approach)
            # Remove markdown formatting for plain text version
            import re
            plain_text = re.sub(r'[#*`\[\]()]', '', markdown)
            plain_text = re.sub(r'\n{3,}', '\n\n', plain_text).strip()

            return ExtractedDocument(
                markdown=markdown,
                plain_text=plain_text,
                metadata={
                    "file_path": str(file_path),
                    "file_type": file_type,
                    "extraction_method": "deepseek_ocr",
                    "model": self.model_name,
                    "device": self.device,
                    "pages_processed": len(markdown_parts) if file_type == 'pdf' else 1
                }
            )

        except Exception as e:
            logger.error(f"❌ DeepSeek-OCR extraction failed for {file_path.name}: {e}")
            return ExtractedDocument(
                markdown="",
                plain_text="",
                metadata={
                    "file_path": str(file_path),
                    "file_type": file_path.suffix.lstrip('.'),
                    "extraction_method": "deepseek_ocr_failed",
                    "error": str(e)
                }
            )

    def get_supported_types(self) -> List[str]:
        """
        Get list of supported file types

        Returns:
            List of supported file extensions
        """
        return ['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp']

    def is_available(self) -> bool:
        """
        Check if DeepSeek-OCR is available in this environment

        Returns:
            True if GPU and dependencies available, False otherwise
        """
        return self._check_availability()
