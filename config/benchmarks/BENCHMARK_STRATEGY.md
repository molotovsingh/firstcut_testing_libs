# Phase 4 Benchmark Strategy: Single-Case Coherent Testing

## ✅ Critical Design Fix (2025-10-04)

**Problem Identified**: Original test set mixed documents from TWO different legal cases (Famas arbitration + Amrapali real estate), which breaks LLM-as-judge evaluation logic.

**Why mixing cases is problematic**:
- Each case has its OWN timeline, parties, facts, and dates
- LLM judge cannot properly assess **completeness** without case context
- No way to know if a provider "captured all events" when events come from unrelated cases
- Citation assessment fails when mixing cases with different legal references

**Solution**: Run TWO separate benchmarks, one per case

---

## 📊 Two-Benchmark Approach

### Benchmark A: **Famas Dispute** (Quick Validation)

**Case**: Famas GmbH vs Elcomponics Sales - International Arbitration

**Documents** (2 from same case):
1. Answer to Request for Arbitration.pdf (677KB) - Jurisdictional objection
2. Transaction_Fee_Invoice.pdf (222KB) - Invoice

**Extractions**: 2 docs × 6 providers = **12 extractions**

**Runtime**: ~5-10 minutes

**Purpose**:
- ✅ Quick validation that all providers work
- ✅ Tests arbitration document handling
- ✅ Baseline comparison with Phase 2 (doc 1 was Phase 2 baseline)
- ✅ Fast feedback loop

**Judge evaluation context**:
- Single arbitration case with coherent timeline
- Judge can assess if provider captured all events from THIS arbitration
- Proper completeness evaluation within case context

---

### Benchmark B: **Amrapali Case** (Comprehensive)

**Case**: Amrapali Real Estate Property Transaction

**Documents** (8 from same transaction series):
1. Amrapali No Objection.pdf (266KB) - Certificate
2. Amrapali Receipts - 2nd Buyer.pdf (639KB) - Payment receipts
3. Amrapali Allotment Letter.pdf (1.4MB) - Allocation letter
4. Amrapali D.D-CHEQUE COPY.pdf (1.7MB) - Bank instruments
5. Amrapali Reciepts _1st_Buyer.pdf (1.9MB) - Payment series
6. Affidavits - Amrapali.pdf (2.9MB) - Sworn statements
7. Amrapali - Agreement To Sell (2nd_Sale).pdf (4.0MB) - Sale contract
8. Amarapali - Bank Statement Stamped 2nd Buyer.pdf (4.7MB) - Bank statement

**Excluded**: Amrapali Builder Buyer Agreement.pdf (17MB - too large, slows benchmark)

**Extractions**: 8 docs × 6 providers = **48 extractions**

**Runtime**: ~20-25 minutes

**Purpose**:
- ✅ Tests provider ability to track events across **document series**
- ✅ Real-world scenario: Complete transaction trail (agreements → payments → statements)
- ✅ Diverse document types within single case
- ✅ Tests completeness: Did provider capture all payments, all agreements, all dates from the transaction?

**Judge evaluation context**:
- Single real estate transaction with multiple related documents
- Judge can assess if provider tracked complete timeline across document series
- Proper evaluation: "Did provider extract all payments from receipts + bank statements?"

---

## 🎯 Why This Approach Works

### Coherent Case Context
- Judge has full context of what events SHOULD exist in the case
- Can properly evaluate completeness ("Did provider miss the July 1, 2020 engagement letter clause?")
- Citation assessment makes sense (all docs cite same agreements/laws)

### Document Series Testing
- Benchmark B tests critical capability: Tracking events across multiple docs from SAME transaction
- Example: Provider should extract:
  - Payment dates from receipts
  - Agreement dates from contracts
  - Transaction dates from bank statements
  - ALL from the SAME property sale

### Validation Against Phase 2
- Benchmark A includes Phase 2 baseline document
- Can verify automated LLM judge matches manual evaluation
- OpenAI should still win on Benchmark A (validates calibration)

---

## 📋 Running the Benchmarks

### Quick Start (Benchmark A only):
```bash
uv run python scripts/benchmark_combinations.py config/benchmarks/test_set_famas_dispute.json
```

### Comprehensive (Benchmark B):
```bash
uv run python scripts/benchmark_combinations.py config/benchmarks/test_set_amrapali_case.json
```

### Both (full evaluation):
```bash
# Run Benchmark A
uv run python scripts/benchmark_combinations.py config/benchmarks/test_set_famas_dispute.json

# Then Benchmark B
uv run python scripts/benchmark_combinations.py config/benchmarks/test_set_amrapali_case.json
```

---

## 📊 Expected Outcomes

### Benchmark A (Famas Dispute):
- **OpenAI/OpenRouter**: Should win (matches Phase 2 preference)
- **LangExtract**: High completeness but missing citations
- **Anthropic**: Good citations, moderate completeness
- **Validation**: LLM judge should match Phase 2 manual rankings

### Benchmark B (Amrapali Case):
- Tests whether providers can:
  - Track payment series across multiple receipts
  - Extract dates from bank statements consistently
  - Capture agreement clauses from contracts
  - Handle diverse document types (PDFs, scanned images)
- **Hypothesis**: Provider with best citation quality (OpenAI/Anthropic) will also track document series best

---

## 🔍 Judge Evaluation Improvements

With single-case benchmarks, the judge can now properly assess:

1. **Completeness**: "Did provider extract all 5 payments mentioned across receipts?"
2. **Accuracy**: "Are dates/amounts consistent with source documents from same transaction?"
3. **Citation Quality**: "Did provider properly reference the 2nd Sale Agreement vs Builder Agreement?"
4. **Hallucinations**: "Did provider invent events not in ANY document from this case?"
5. **Overall Quality**: "Can I trust this provider to extract complete timeline from a document series?"

---

## ✅ Design Validation

**User Insight** (2025-10-04): "Each case has a unique set of dates originating in a documents set. If we mix two document sets then the assessment won't be correct."

**Fix Applied**: Split into two single-case benchmarks with coherent timelines and case context.

**Result**: LLM-as-judge can now properly evaluate completeness, accuracy, and quality within case context.

---

## 📁 File Structure

```
config/benchmarks/
├── BENCHMARK_STRATEGY.md (this file)
├── test_set_famas_dispute.json (Benchmark A - 2 docs)
├── test_set_amrapali_case.json (Benchmark B - 8 docs)
├── test_set_phase4.json (DEPRECATED - mixed cases, do not use)
└── results/
    ├── phase4_famas_*.json (Benchmark A results)
    ├── phase4_amrapali_*.json (Benchmark B results)
    └── llm_judge_validation.json (Phase 2 validation)
```

---

**Ready to run coherent single-case benchmarks!** 🚀
