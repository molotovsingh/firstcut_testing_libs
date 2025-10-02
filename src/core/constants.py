"""
Core Constants - Shared values across the legal events pipeline
"""

# Five-column headers for legal events table - Date added as column 2
FIVE_COLUMN_HEADERS = ["No", "Date", "Event Particulars", "Citation", "Document Reference"]

# Internal field names used in processing (matching column order)
INTERNAL_FIELDS = ["number", "date", "event_particulars", "citation", "document_reference"]

# Default values for failed extractions
DEFAULT_NO_CITATION = "No citation available"
DEFAULT_NO_REFERENCE = "Unknown document"
DEFAULT_NO_PARTICULARS = "Event details not available"
DEFAULT_NO_DATE = "Date not available"

# LangExtract prompt contract - standardized prompt for consistent extractions
# Enhanced for GPT-5 integration: requires 2-8 sentences for comprehensive legal context
LEGAL_EVENTS_PROMPT = """Extract legal events from this document. For each event, you must return exactly four JSON keys:

1. "event_particulars" - REQUIRED: Provide a complete description (2-8 sentences as appropriate) of what happened, including relevant context, parties involved, procedural background, implications, and any important details. Use verbatim or paraphrased text from the document. NEVER leave this field empty.
2. "citation" - Exact legal authority cited in the event (statute, rule, case, docket, etc.). Copy the verbatim reference from the document. Use empty string "" when no explicit legal citation appears.
3. "document_reference" - Leave as empty string "" (will be filled automatically with source filename)
4. "date" - Specific date mentioned (use empty string "" if no date is found)

CRITICAL REQUIREMENTS:
- "event_particulars" must ALWAYS contain meaningful, comprehensive text - provide a full description with sufficient context for legal analysis
- Use 2-8 sentences as appropriate to capture the complete legal significance and context of each event
- Include relevant background, procedural details, party information, and implications when available in the document
- Use empty strings ("") for missing values EXCEPT for "event_particulars" which must never be empty
- The "citation" field should only contain actual legal references mentioned in the text
- Always use empty string "" for "document_reference" - the system will populate it with the correct filename
- Return all four keys for every extraction

PROHIBITION: Never return an extraction with blank or empty "event_particulars" - every event must have a comprehensive, contextual description.

Extract all legally significant events, proceedings, filings, agreements, and deadlines."""

# API configuration
REQUIRED_ENV_VARS = ["GEMINI_API_KEY"]
DEFAULT_MODEL = "gemini-2.0-flash"
