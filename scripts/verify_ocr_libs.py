#!/usr/bin/env python3
"""Verify all OCR libraries are working"""
import sys
from pathlib import Path

print("="*70)
print("OCR LIBRARIES VERIFICATION")
print("="*70)

# Test 1: Tesserocr
print("\n1. Testing tesserocr...")
try:
    import tesserocr
    print(f"   ✅ tesserocr {tesserocr.tesseract_version()}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: EasyOCR
print("\n2. Testing easyocr...")
try:
    import easyocr
    print(f"   ✅ easyocr installed")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: PaddleOCR
print("\n3. Testing paddleocr...")
try:
    from paddleocr import PaddleOCR
    print(f"   ✅ paddleocr installed")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: RapidOCR
print("\n4. Testing rapidocr...")
try:
    from rapidocr_onnxruntime import RapidOCR
    print(f"   ✅ rapidocr-onnxruntime installed")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Check Docling OCR options
print("\n5. Testing Docling OCR options...")
try:
    from docling.datamodel.pipeline_options import (
        PipelineOptions,
        TesseractOcrOptions,
        EasyOcrOptions
    )
    print(f"   ✅ Docling OCR options available")
    print(f"      - TesseractOcrOptions")
    print(f"      - EasyOcrOptions")

    # Check if OCRmac is available (macOS only)
    try:
        from docling.datamodel.pipeline_options import OcrMacOptions
        print(f"      - OcrMacOptions (macOS native)")
    except:
        print(f"      - OcrMacOptions (not available)")

except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*70)
print("VERIFICATION COMPLETE")
print("="*70 + "\n")
