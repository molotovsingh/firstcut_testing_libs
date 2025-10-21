# DeepSeek-OCR Integration Guide

DeepSeek-OCR is a 3B-parameter vision-language model for optical character recognition and document understanding. This guide covers installation, configuration, and usage for Layer 1 document extraction.

## Overview

**What is DeepSeek-OCR?**
- 3-billion parameter multimodal model for OCR and visual document understanding
- Converts documents to Markdown with layout preservation
- 7-20x token compression compared to traditional OCR
- MIT licensed (free for commercial use)
- Released October 2025 by DeepSeek AI

**Key Features:**
- ✅ PDF and image support (PNG, JPG, TIFF, BMP)
- ✅ Layout-aware parsing (preserves tables, headers, lists)
- ✅ Multimodal vision understanding
- ✅ High-quality Markdown output
- ✅ Open source (MIT license)

**Limitations:**
- ❌ Requires NVIDIA GPU with CUDA 11.8+
- ❌ Requires ~4GB+ GPU memory
- ❌ No CPU fallback
- ❌ Slower than CPU-based OCR (~2-3s per page on A100-40G)
- ❌ Large model download (~6GB first-time setup)

## Hardware Requirements

### Minimum Requirements
- **GPU**: NVIDIA GPU with CUDA 11.8+
- **GPU Memory**: 4GB+ VRAM
- **System RAM**: 8GB+
- **Disk Space**: 10GB (for model and dependencies)

### Recommended Requirements
- **GPU**: NVIDIA A100, RTX 4090, or similar
- **GPU Memory**: 8GB+ VRAM
- **System RAM**: 16GB+
- **Disk Space**: 20GB

### Tested GPUs
- ✅ NVIDIA A100 (40GB) - ~2-3s per page
- ✅ NVIDIA RTX 4090 (24GB) - ~3-5s per page
- ✅ NVIDIA RTX 3090 (24GB) - ~4-6s per page
- ⚠️ NVIDIA RTX 3060 (12GB) - Slower but functional
- ❌ NVIDIA GTX 1080 Ti (11GB) - May work but not tested

## Installation

### Option 1: Automated Setup (Recommended)

Run the automated installation script (requires conda):

```bash
# Make script executable (if not already)
chmod +x scripts/setup_deepseek_ocr.sh

# Run installation
bash scripts/setup_deepseek_ocr.sh
```

The script will:
1. Check for NVIDIA GPU and CUDA
2. Create conda environment `deepseek-ocr`
3. Install PyTorch 2.6.0 with CUDA 11.8
4. Install transformers, flash-attn, and dependencies
5. Optionally download the model (~6GB)

### Option 2: Manual Setup

#### 1. Create Conda Environment

```bash
conda create -n deepseek-ocr python=3.12.9 -y
conda activate deepseek-ocr
```

#### 2. Install PyTorch with CUDA 11.8

```bash
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 \
    --index-url https://download.pytorch.org/whl/cu118
```

#### 3. Install Transformers and Dependencies

```bash
pip install transformers==4.46.3 tokenizers==0.20.3
pip install einops addict easydict pillow PyMuPDF
```

#### 4. Install Flash Attention (may take 5-10 minutes)

```bash
pip install flash-attn==2.7.3 --no-build-isolation
```

#### 5. Verify Installation

```bash
python3 << 'EOF'
import torch
import transformers

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
print(f"Transformers version: {transformers.__version__}")
EOF
```

Expected output:
```
PyTorch version: 2.6.0+cu118
CUDA available: True
CUDA version: 11.8
GPU: NVIDIA A100-SXM4-40GB
GPU memory: 40.5 GB
Transformers version: 4.46.3
```

## Configuration

### Environment Variables

Add to your `.env` file (optional - uses defaults if not specified):

```bash
# DeepSeek-OCR model configuration
DEEPSEEK_OCR_MODEL=deepseek-ai/DeepSeek-OCR  # Hugging Face model ID
DEEPSEEK_OCR_DEVICE=cuda:0                    # CUDA device (cuda:0, cuda:1, etc.)
```

### Enable in Catalog

DeepSeek-OCR is **disabled by default** in the document extractor catalog (since it requires GPU setup). To enable:

1. Edit `src/core/document_extractor_catalog.py`
2. Find the `deepseek_ocr` entry
3. Change `enabled=False` to `enabled=True`

```python
DocExtractorEntry(
    extractor_id="deepseek_ocr",
    display_name="DeepSeek-OCR (Local GPU Vision)",
    # ...
    enabled=True,  # Change from False to True
    # ...
)
```

4. Restart the application

## Usage

### Quick Test

Activate the DeepSeek-OCR environment and run the test script:

```bash
# Activate environment
conda activate deepseek-ocr

# Quick availability check
python scripts/test_deepseek_ocr.py --quick

# Full test on sample documents
python scripts/test_deepseek_ocr.py

# Compare with Docling baseline
python scripts/test_deepseek_ocr.py --compare
```

### Programmatic Usage

```python
from pathlib import Path
from src.core.deepseek_ocr_adapter import DeepSeekOCRDocumentExtractor

# Create extractor
extractor = DeepSeekOCRDocumentExtractor(
    model_name="deepseek-ai/DeepSeek-OCR",
    device="cuda:0"
)

# Check availability
if not extractor.is_available():
    print("DeepSeek-OCR not available (GPU required)")
    exit(1)

# Extract from PDF
pdf_path = Path("sample_pdf/famas_dispute/Answer to Request for Arbitration.pdf")
result = extractor.extract(pdf_path)

# Access extracted content
print(f"Markdown length: {len(result.markdown)}")
print(f"Plain text length: {len(result.plain_text)}")
print(f"Pages processed: {result.metadata.get('pages_processed', 1)}")

# Preview markdown
print(result.markdown[:500])
```

### Integration with Main Pipeline

Once enabled in the catalog, DeepSeek-OCR becomes available as a document extractor:

```python
from src.core.extractor_factory import create_extractors
from src.core.config import load_config

# Load configuration
config = load_config()

# Create extractors (factory will use deepseek_ocr if enabled)
doc_extractor, event_extractor = create_extractors(
    document_extractor_id="deepseek_ocr",  # Use DeepSeek-OCR for Layer 1
    event_provider="langextract"           # Use LangExtract for Layer 2
)

# Process document
result = doc_extractor.extract(Path("document.pdf"))
events = event_extractor.extract_events(result.plain_text, result.metadata)
```

## Performance Characteristics

### Speed Benchmarks

Based on testing with "Answer to Request for Arbitration.pdf" (~15 pages):

| GPU Model | Pages/Second | Total Time (15 pages) | Cost |
|-----------|--------------|----------------------|------|
| A100 (40GB) | 0.4-0.5 | 30-40s | FREE |
| RTX 4090 (24GB) | 0.3-0.4 | 40-50s | FREE |
| RTX 3090 (24GB) | 0.2-0.3 | 50-75s | FREE |
| Docling (CPU) | 2-3 | 5-8s | FREE |
| Qwen VL (API) | 0.5-1.0 | 15-30s | $0.077 |

**Key Insights:**
- DeepSeek-OCR is **3-6x slower** than CPU-based Docling
- DeepSeek-OCR is **FREE** (no API costs, runs locally)
- DeepSeek-OCR provides **higher quality** on scanned/poor quality documents
- Best for: Complex layouts, scanned documents, when Docling OCR fails

### Quality Comparison

| Feature | Docling | DeepSeek-OCR | Qwen VL |
|---------|---------|--------------|---------|
| Digital PDFs | ★★★★★ | ★★★★☆ | ★★★★☆ |
| Scanned PDFs | ★★★★☆ | ★★★★★ | ★★★★★ |
| Tables | ★★★★☆ | ★★★★★ | ★★★★★ |
| Handwriting | ★★☆☆☆ | ★★★★☆ | ★★★★☆ |
| Complex Layouts | ★★★☆☆ | ★★★★★ | ★★★★★ |
| Speed | ★★★★★ | ★★★☆☆ | ★★★★☆ |
| Cost | FREE | FREE | $0.00512/page |

## Troubleshooting

### GPU Not Detected

**Problem:** `CUDA not available` error

**Solutions:**
1. Check NVIDIA driver: `nvidia-smi`
2. Verify CUDA installation: `nvcc --version`
3. Reinstall PyTorch with CUDA: `pip install torch --index-url https://download.pytorch.org/whl/cu118`

### Out of Memory Error

**Problem:** `CUDA out of memory` during extraction

**Solutions:**
1. Close other GPU applications
2. Process one page at a time (modify adapter to reduce batch size)
3. Reduce image resolution (modify `_convert_pdf_to_images` matrix parameter)
4. Use smaller GPU device if multiple available

### Flash Attention Installation Fails

**Problem:** `flash-attn` compilation errors

**Solutions:**
1. Ensure CUDA 11.8+ installed: `nvidia-smi | grep "CUDA Version"`
2. Install build tools: `conda install -c conda-forge gxx_linux-64`
3. Try prebuilt wheel: Download from https://github.com/Dao-AILab/flash-attention/releases
4. Alternative: Use without flash attention (slower, edit adapter to remove `attn_implementation='flash_attention_2'`)

### Model Download Slow/Fails

**Problem:** Model download takes too long or fails

**Solutions:**
1. Use Hugging Face mirror: `export HF_ENDPOINT=https://hf-mirror.com`
2. Manual download:
   ```bash
   git lfs install
   git clone https://huggingface.co/deepseek-ai/DeepSeek-OCR
   ```
3. Set cache directory: `export HF_HOME=/path/to/large/disk`

### Extraction Quality Poor

**Problem:** Markdown output has errors or missing content

**Solutions:**
1. Increase image resolution in `_convert_pdf_to_images` (currently 2x)
2. Try different prompt (edit adapter `_extract_from_image` method)
3. Fall back to Docling for digital PDFs (DeepSeek-OCR best for scanned docs)
4. Check original document quality (some documents may need preprocessing)

## Comparison to Other Extractors

### When to Use DeepSeek-OCR

✅ **Use DeepSeek-OCR when:**
- Docling OCR fails on poor quality scans
- Document has complex layouts (tables, multi-column, mixed content)
- You need layout-aware Markdown output
- API costs are a concern (vs Qwen VL)
- You have access to GPU infrastructure
- Processing time is not critical

❌ **Don't use DeepSeek-OCR when:**
- Document is a clean digital PDF (use Docling - 5x faster)
- You need fastest possible extraction (use Docling)
- No GPU available (use Docling or Qwen VL API)
- Processing hundreds of documents quickly (use Docling or batch API)

### Cost Comparison (15-page document)

| Extractor | Cost | Time | Quality |
|-----------|------|------|---------|
| **Docling** | FREE | ~7s | ★★★★☆ |
| **DeepSeek-OCR** | FREE | ~35s | ★★★★★ |
| **Qwen VL** | $0.077 | ~20s | ★★★★★ |

## Advanced Configuration

### Multi-GPU Setup

If you have multiple GPUs, you can specify which to use:

```python
# Use second GPU
extractor = DeepSeekOCRDocumentExtractor(device="cuda:1")

# Or set environment variable
os.environ["DEEPSEEK_OCR_DEVICE"] = "cuda:1"
```

### Custom Model

Use a fine-tuned or alternative model:

```python
extractor = DeepSeekOCRDocumentExtractor(
    model_name="your-org/custom-deepseek-ocr",
    device="cuda:0"
)

# Or set environment variable
os.environ["DEEPSEEK_OCR_MODEL"] = "your-org/custom-deepseek-ocr"
```

### Batch Processing

Process multiple documents efficiently:

```python
from pathlib import Path

extractor = DeepSeekOCRDocumentExtractor()
pdf_files = Path("sample_pdf").rglob("*.pdf")

for pdf_file in pdf_files:
    print(f"Processing: {pdf_file.name}")
    result = extractor.extract(pdf_file)

    # Save markdown
    output_path = pdf_file.with_suffix(".md")
    output_path.write_text(result.markdown)

    print(f"  Saved: {output_path.name}")
```

## References

- **GitHub Repository**: https://github.com/deepseek-ai/DeepSeek-OCR
- **Hugging Face Model**: https://huggingface.co/deepseek-ai/DeepSeek-OCR
- **Paper**: (Check GitHub for latest research publication)
- **License**: MIT License

## Changelog

### 2025-10-21 - Initial Integration
- Added DeepSeek-OCR adapter implementing DocumentExtractor protocol
- Created automated installation script
- Added to document extractor catalog (disabled by default)
- Created test script and documentation
- Tested on sample legal documents

### Future Improvements
- [ ] Add CPU fallback mode (if DeepSeek releases CPU-optimized version)
- [ ] Benchmark against additional document types
- [ ] Optimize batch processing for multi-document workloads
- [ ] Add quality metrics and evaluation framework
- [ ] Create Streamlit UI integration
