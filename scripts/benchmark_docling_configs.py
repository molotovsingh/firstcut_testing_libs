#!/usr/bin/env python3
"""Benchmark Docling configuration variants for speed vs. extraction output."""

from __future__ import annotations

import json
import os
import statistics
import time
from copy import deepcopy
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List

import pandas as pd

# Ensure we can import project modules when running directly
PROJECT_ROOT = Path(__file__).resolve().parents[1]
import sys
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.docling_adapter import DoclingDocumentExtractor
from src.core.config import DoclingConfig


@dataclass
class DocBenchmarkResult:
    scenario: str
    file: str
    docling_seconds: float
    extraction_method: str
    plain_text_chars: int
    markdown_chars: int


SCENARIOS: List[Dict[str, str]] = [
    {
        "label": "baseline",
        "description": "Defaults (OCR on, table mode FAST, structure on)",
        "env": {}
    },
    {
        "label": "no_ocr",
        "description": "Disable OCR (expect faster on digital PDFs)",
        "env": {
            "DOCLING_DO_OCR": "false"
        }
    },
    {
        "label": "table_structure_off",
        "description": "Disable table structure + cell matching (text only)",
        "env": {
            "DOCLING_DO_TABLE_STRUCTURE": "false",
            "DOCLING_DO_CELL_MATCHING": "false"
        }
    },
    {
        "label": "accurate_mode",
        "description": "Use ACCURATE table mode (potentially slower, higher fidelity)",
        "env": {
            "DOCLING_TABLE_MODE": "ACCURATE"
        }
    },
]

SAMPLE_DOCS = [
    PROJECT_ROOT / "sample_pdf" / "famas_dispute" / "Answer to Request for Arbitration.pdf",
    PROJECT_ROOT / "sample_pdf" / "famas_dispute" / "Transaction_Fee_Invoice.pdf",
    PROJECT_ROOT / "sample_pdf" / "amrapali_case" / "Amrapali Allotment Letter.pdf",
]

OUTPUT_DIR = PROJECT_ROOT / "docs" / "reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def apply_env_overrides(overrides: Dict[str, str]) -> Dict[str, str]:
    """Apply overrides, returning previous values for restoration."""
    original = {}
    for key, value in overrides.items():
        original[key] = os.environ.get(key)
        os.environ[key] = value
    return original


def restore_env(original: Dict[str, str]) -> None:
    for key, value in original.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def run_benchmark() -> pd.DataFrame:
    results: List[DocBenchmarkResult] = []

    for scenario in SCENARIOS:
        label = scenario["label"]
        overrides = scenario["env"]
        print(f"\n=== Scenario: {label} ===")
        print(f"{scenario['description']}")
        original_env = apply_env_overrides(overrides)

        try:
            config = DoclingConfig()
            extractor = DoclingDocumentExtractor(config)

            for doc_path in SAMPLE_DOCS:
                if not doc_path.exists():
                    print(f"⚠️  Skipping missing file: {doc_path}")
                    continue

                start = time.perf_counter()
                extracted = extractor.extract(doc_path)
                elapsed = time.perf_counter() - start

                plain_text_chars = len(extracted.plain_text)
                markdown_chars = len(extracted.markdown)

                print(
                    f"  {doc_path.name}: {elapsed:.3f}s | method={extracted.metadata.get('extraction_method')} "
                    f"| text_len={plain_text_chars}"
                )

                results.append(
                    DocBenchmarkResult(
                        scenario=label,
                        file=doc_path.name,
                        docling_seconds=elapsed,
                        extraction_method=extracted.metadata.get("extraction_method", "unknown"),
                        plain_text_chars=plain_text_chars,
                        markdown_chars=markdown_chars,
                    )
                )
        finally:
            restore_env(original_env)

    df = pd.DataFrame([asdict(r) for r in results])
    return df


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby("scenario")
        .agg(
            documents_tested=("file", "nunique"),
            avg_docling_seconds=("docling_seconds", "mean"),
            median_docling_seconds=("docling_seconds", "median"),
            avg_plain_text_chars=("plain_text_chars", "mean"),
        )
        .reset_index()
    )
    summary["avg_docling_seconds"] = summary["avg_docling_seconds"].round(3)
    summary["median_docling_seconds"] = summary["median_docling_seconds"].round(3)
    summary["avg_plain_text_chars"] = summary["avg_plain_text_chars"].round(0)
    return summary


def main() -> None:
    df = run_benchmark()
    if df.empty:
        print("No results collected. Check sample paths.")
        return

    summary = summarize(df)
    print("\n=== Summary (seconds) ===")
    print(summary.to_string(index=False))

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    detailed_path = OUTPUT_DIR / f"docling_benchmark_{timestamp}.csv"
    summary_path = OUTPUT_DIR / f"docling_benchmark_summary_{timestamp}.csv"

    df.to_csv(detailed_path, index=False)
    summary.to_csv(summary_path, index=False)

    print(f"\nSaved detailed results to {detailed_path}")
    print(f"Saved summary to {summary_path}")


if __name__ == "__main__":
    main()
