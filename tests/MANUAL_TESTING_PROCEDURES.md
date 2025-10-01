# Manual Testing Procedures for 5-Column Legal Events Table

## Overview

This document provides step-by-step manual testing procedures to validate the 5-column legal events table implementation. These tests complement the automated test suite and ensure comprehensive coverage of user-facing functionality.

## Prerequisites

### Environment Setup
- ✅ Python environment with UV package manager
- ✅ Valid Google API key set in environment (`GOOGLE_API_KEY` or `GEMINI_API_KEY`)
- ✅ All project dependencies installed via `uv sync`
- ✅ Test documents available in `tests/test_documents/` directory

### Verification Command
```bash
uv run python -c "from src.core.constants import FIVE_COLUMN_HEADERS; print('Headers:', FIVE_COLUMN_HEADERS)"
```
**Expected Output:**
```
Headers: ['No', 'Date', 'Event Particulars', 'Citation', 'Document Reference']
```

## Test Category 1: Core Functionality

### Test 1.1: Basic Table Structure Validation

**Objective:** Verify 5-column table structure and column ordering

**Steps:**
1. Start the Streamlit application:
   ```bash
   uv run streamlit run app.py
   ```
2. Upload any test document from `tests/test_documents/`
3. Wait for processing to complete
4. Observe the displayed table

**Expected Results:**
- ✅ Table displays exactly 5 columns
- ✅ Column headers in order: "No", "Date", "Event Particulars", "Citation", "Document Reference"
- ✅ No column should be missing or duplicated
- ✅ Date column appears as the 2nd column (between No and Event Particulars)

**Pass Criteria:** All expected results verified ✅

---

### Test 1.2: Column Width and Layout

**Objective:** Verify appropriate column widths for optimal display

**Steps:**
1. Process a document with multiple events
2. Observe column widths and content layout
3. Test on different screen sizes if possible

**Expected Results:**
- ✅ "No" column: small width, displays numbers clearly
- ✅ "Date" column: medium width, accommodates date formats
- ✅ "Event Particulars" column: large width (widest column)
- ✅ "Citation" column: medium width
- ✅ "Document Reference" column: medium width
- ✅ No horizontal scrolling required on standard screens

**Pass Criteria:** Column widths are appropriate and content is readable ✅

---

## Test Category 2: Date Extraction Testing

### Test 2.1: Clear Dates Document Test

**Objective:** Validate extraction of obvious, well-formatted dates

**Test Document:** `tests/test_documents/clear_dates_document.html`

**Steps:**
1. Upload the clear dates test document
2. Process through the pipeline
3. Examine the Date column values
4. Count events with valid dates vs. "Date not available"

**Expected Results:**
- ✅ Most events (>80%) should have actual dates, not "Date not available"
- ✅ Dates should be in recognizable format (YYYY-MM-DD preferred)
- ✅ Sample expected dates from document:
  - 2024-01-15 (January 15, 2024)
  - 2024-02-01 (February 1, 2024)
  - 2024-03-10 (March 10, 2024)

**Validation Questions:**
- Are the extracted dates accurate to the source document? ✅/❌
- Do the dates correspond to the correct events? ✅/❌
- Are dates in a consistent format? ✅/❌

---

### Test 2.2: Mixed Date Formats Test

**Objective:** Test recognition of various date format patterns

**Test Document:** `tests/test_documents/mixed_date_formats_document.html`

**Steps:**
1. Upload the mixed date formats test document
2. Process and examine extracted dates
3. Verify handling of different input formats:
   - ISO format: "2024-01-15"
   - US format: "3/22/2024", "05/10/2024"
   - Dash format: "7-18-2024"
   - Alternative ISO: "2024/09/30"
   - Written format: "March 31, 2024"

**Expected Results:**
- ✅ System recognizes multiple date format patterns
- ✅ Consistent output format regardless of input format
- ✅ No valid dates should become "Date not available" due to format issues

**Manual Verification:**
Compare each extracted date with the source document to ensure accuracy.

---

### Test 2.3: Ambiguous Dates Handling

**Objective:** Test graceful handling of unclear date references

**Test Document:** `tests/test_documents/ambiguous_dates_document.html`

**Steps:**
1. Upload the ambiguous dates document
2. Process and examine results
3. Note how vague date references are handled:
   - "early 2023"
   - "approximately three months later"
   - "during the summer months"
   - "before the holiday season"

**Expected Results:**
- ✅ Processing completes without errors
- ✅ Ambiguous dates appropriately show "Date not available"
- ✅ System doesn't crash or produce invalid date values
- ✅ Events without dates still appear with other information intact

---

### Test 2.4: No Dates Document Test

**Objective:** Verify fallback behavior when no dates are present

**Test Document:** `tests/test_documents/no_dates_document.html`

**Steps:**
1. Upload the no dates document
2. Process through pipeline
3. Examine Date column values

**Expected Results:**
- ✅ Processing completes successfully
- ✅ All events show "Date not available" in Date column
- ✅ Other columns (Event Particulars, Citation) contain extracted information
- ✅ Table structure remains valid (5 columns)

---

## Test Category 3: Performance Testing

### Test 3.1: Multiple Documents Performance

**Objective:** Test processing speed with multiple documents

**Steps:**
1. Upload all test documents simultaneously:
   - clear_dates_document.html
   - mixed_date_formats_document.html
   - multiple_events_document.html
   - ambiguous_dates_document.html
   - no_dates_document.html
2. Start processing and measure time
3. Note total events extracted

**Expected Results:**
- ✅ Processing completes within 60 seconds
- ✅ All documents appear in "Document Reference" column
- ✅ No duplicate event numbering across documents
- ✅ Format validation passes

**Measurements to Record:**
- Total processing time: _____ seconds
- Total events extracted: _____ events
- Documents processed: _____ documents
- Any errors or warnings: _____

---

### Test 3.2: Large Document Test

**Objective:** Test performance with document containing many events

**Test Document:** `tests/test_documents/multiple_events_document.html`

**Steps:**
1. Upload the multiple events document
2. Process and time the operation
3. Count extracted events
4. Verify sequential numbering

**Expected Results:**
- ✅ Processing completes within 30 seconds
- ✅ Multiple events extracted (should be 20+ events)
- ✅ Sequential numbering in "No" column (1, 2, 3, ...)
- ✅ Each event has unique number
- ✅ Date extraction works for multiple events

---

## Test Category 4: Export Functionality

### Test 4.1: Excel Export Test

**Objective:** Verify Excel export maintains 5-column format

**Steps:**
1. Process any test document to generate events table
2. Use export functionality to download Excel file
3. Open downloaded file in Excel or LibreOffice
4. Verify structure and content

**Expected Results:**
- ✅ Excel file opens without errors
- ✅ Contains exactly 5 columns with correct headers
- ✅ All data accurately transferred
- ✅ Date values preserved correctly
- ✅ No formatting corruption

**Manual Verification Checklist:**
- [ ] Column A: "No" with sequential numbers
- [ ] Column B: "Date" with date values or "Date not available"
- [ ] Column C: "Event Particulars" with event descriptions
- [ ] Column D: "Citation" with legal references
- [ ] Column E: "Document Reference" with filenames

---

### Test 4.2: CSV Export Test

**Objective:** Verify CSV export format compliance

**Steps:**
1. Process test document
2. Export to CSV format
3. Open in text editor and spreadsheet application
4. Verify comma-separated format

**Expected Results:**
- ✅ CSV file contains proper header row
- ✅ All rows have exactly 5 comma-separated values
- ✅ Date values properly quoted if containing commas
- ✅ File imports correctly into Excel/Google Sheets

---

## Test Category 5: User Interface Testing

### Test 5.1: Table Display Responsiveness

**Objective:** Test UI responsiveness and layout

**Steps:**
1. Process document with 10+ events
2. Observe table rendering
3. Test scrolling and interaction
4. Try different browser window sizes

**Expected Results:**
- ✅ Table appears within 2 seconds of processing completion
- ✅ All columns visible without horizontal scrolling (standard screen)
- ✅ Table is interactive (sortable, scrollable)
- ✅ Text wrapping works appropriately

---

### Test 5.2: Summary Statistics Validation

**Objective:** Verify summary metrics accuracy

**Steps:**
1. Process test document with known event count
2. Check summary statistics below table:
   - Total Events
   - Documents Processed
   - Events with Citations
   - Avg Event Detail Length

**Expected Results:**
- ✅ "Total Events" matches actual row count
- ✅ "Documents Processed" shows correct number
- ✅ "Events with Citations" excludes "No citation available" entries
- ✅ "Avg Event Detail Length" shows reasonable character count

**Manual Count Verification:**
- Manually count table rows: _____
- Count events with real citations: _____
- Verify statistics match manual counts: ✅/❌

---

## Test Category 6: Error Handling

### Test 6.1: Empty File Upload

**Objective:** Test graceful handling of empty or invalid files

**Steps:**
1. Create empty text file or upload invalid document
2. Attempt processing
3. Observe system behavior

**Expected Results:**
- ✅ System doesn't crash
- ✅ Clear error message displayed
- ✅ Fallback table created if needed
- ✅ User can continue with other documents

---

### Test 6.2: Network Interruption Simulation

**Objective:** Test behavior during API failures

**Steps:**
1. Temporarily disconnect internet or use invalid API key
2. Attempt document processing
3. Observe error handling

**Expected Results:**
- ✅ Graceful error handling
- ✅ Clear error message about API connectivity
- ✅ System remains stable
- ✅ Fallback table created with appropriate messaging

---

## Test Category 7: Regression Testing

### Test 7.1: Existing Functionality Preservation

**Objective:** Ensure 5-column change doesn't break existing features

**Checklist of Features to Test:**
- [ ] Document upload functionality
- [ ] File format support (PDF, DOCX, HTML, etc.)
- [ ] Event particulars extraction accuracy
- [ ] Citation extraction
- [ ] Error handling for unsupported files
- [ ] Processing status indicators
- [ ] Download functionality

**Pass Criteria:** All existing features work identically to previous version ✅

---

## Test Execution Checklist

### Pre-Testing Setup
- [ ] Environment configured with API key
- [ ] All test documents available
- [ ] Streamlit application starts successfully
- [ ] Dependencies installed and working

### Core Testing Execution
- [ ] Test 1.1: Basic Table Structure ✅/❌
- [ ] Test 1.2: Column Width Layout ✅/❌
- [ ] Test 2.1: Clear Dates Extraction ✅/❌
- [ ] Test 2.2: Mixed Date Formats ✅/❌
- [ ] Test 2.3: Ambiguous Dates Handling ✅/❌
- [ ] Test 2.4: No Dates Document ✅/❌
- [ ] Test 3.1: Multiple Documents Performance ✅/❌
- [ ] Test 3.2: Large Document Performance ✅/❌
- [ ] Test 4.1: Excel Export ✅/❌
- [ ] Test 4.2: CSV Export ✅/❌
- [ ] Test 5.1: UI Responsiveness ✅/❌
- [ ] Test 5.2: Summary Statistics ✅/❌
- [ ] Test 6.1: Error Handling ✅/❌
- [ ] Test 7.1: Regression Testing ✅/❌

### Post-Testing Documentation
- [ ] Record any failures or issues
- [ ] Document performance measurements
- [ ] Note any unexpected behaviors
- [ ] Update test procedures based on findings

---

## Issue Reporting Template

**Test ID:** [e.g., Test 2.1]
**Issue Description:** [Detailed description of problem]
**Expected Behavior:** [What should happen]
**Actual Behavior:** [What actually happened]
**Steps to Reproduce:** [Step-by-step reproduction]
**Screenshot/Evidence:** [If applicable]
**Severity:** [Critical/High/Medium/Low]
**Environment:** [Browser, OS, API key status, etc.]

---

## Success Criteria Summary

**Overall Test Suite Passes If:**
- ✅ 95%+ of individual tests pass
- ✅ No critical functionality regressions
- ✅ Date extraction works for clear date documents (>80% accuracy)
- ✅ Export functionality produces valid files
- ✅ Performance meets acceptable thresholds
- ✅ UI displays correctly and responsively
- ✅ Error handling is graceful and informative

**Ready for Production If:**
- All manual tests pass ✅
- Automated test suite passes ✅
- Performance requirements met ✅
- No critical bugs identified ✅