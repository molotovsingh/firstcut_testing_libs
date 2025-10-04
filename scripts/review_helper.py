#!/usr/bin/env python3
"""Helper script to view and compare provider outputs"""
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
results_dir = PROJECT_ROOT / "test_results" / "manual_comparison_2025-10-03"

providers = ["langextract", "openrouter", "openai", "anthropic"]

for provider in providers:
    csv_file = results_dir / f"{provider}_events.csv"
    if not csv_file.exists():
        print(f"⚠️  Missing: {provider}")
        continue

    df = pd.read_csv(csv_file)
    print(f"\n{'='*80}")
    print(f"{provider.upper()} - {len(df)} events")
    print(f"{'='*80}")

    # Show first 3 events
    for idx, row in df.head(3).iterrows():
        print(f"\n[Event {row['number']}]")
        print(f"Date: {row['date']}")
        print(f"Particulars: {row['event_particulars'][:200]}..." if len(str(row['event_particulars'])) > 200 else f"Particulars: {row['event_particulars']}")
        print(f"Citation: {row['citation']}")

    if len(df) > 3:
        print(f"\n... and {len(df) - 3} more events")

print(f"\n{'='*80}")
print("MANUAL REVIEW QUESTIONS")
print(f"{'='*80}\n")

print("For quality assessment, consider:")
print("1. Are the extracted events actually legal events?")
print("2. Are dates accurate and properly extracted?")
print("3. Are event descriptions complete and contextual?")
print("4. Are citations correct (or appropriately empty)?")
print("5. Are there obvious missing events?")

print("\nQuality Scoring (0-10):")
print("- Accuracy: Are extracted events correct?")
print("- Completeness: Are all events captured?")
print("- Precision: Any false positives?")
print("- Format: Does output match schema?")

print(f"\n{'='*80}\n")
