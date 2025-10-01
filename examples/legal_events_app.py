#!/usr/bin/env python3
"""
STRICT Legal Events Pipeline per Assistant Guardrails
Implements exact sequence: .env → Docling → LangExtract → Five-Column Table → Export
"""

import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime
from dotenv import load_dotenv
import logging

# Load environment variables FIRST per guardrails
load_dotenv()

# Import refactored pipeline components
from src.ui.streamlit_common import (
    get_pipeline,
    process_documents_with_spinner,
    display_legal_events_table,
    create_download_section
)
from src.utils.file_handler import FileHandler
from src.core.constants import FIVE_COLUMN_HEADERS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reduce LangExtract AFC logging noise
logging.getLogger('langextract').setLevel(logging.WARNING)

# Page config
st.set_page_config(
    page_title="Legal Events Extraction - STRICT Docling + LangExtract Pipeline",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for legal events table
st.markdown("""
<style>
.legal-events-header {
    font-size: 2rem;
    font-weight: bold;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}
.critical-error {
    padding: 1rem;
    background-color: #f8d7da;
    border: 2px solid #dc3545;
    border-radius: 0.375rem;
    color: #721c24;
    font-weight: bold;
}
.success-box {
    padding: 1rem;
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    border-radius: 0.375rem;
    color: #155724;
}
.legal-table {
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)


def strict_environment_check():
    """STEP 1: Load .env and refuse to continue if GEMINI_API_KEY is missing per guardrails"""
    st.markdown('<h1 class="legal-events-header">Legal Events Extraction Pipeline</h1>', unsafe_allow_html=True)

    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')

    if not api_key:
        st.markdown("""
        <div class="critical-error">
        🚨 CRITICAL ERROR: GEMINI_API_KEY is missing from .env file<br>
        🛑 APPLICATION HALTED per assistant guardrails<br>
        📝 Please add GEMINI_API_KEY to your .env file to continue
        </div>
        """, unsafe_allow_html=True)
        st.stop()  # HALT EXECUTION IMMEDIATELY per guardrails

    st.markdown("""
    <div class="success-box">
    ✅ GEMINI_API_KEY validated - Legal Events Pipeline enabled<br>
    🔒 STRICT MODE: Docling → LangExtract → Five-Column Table
    </div>
    """, unsafe_allow_html=True)

    return True


def create_file_upload_section():
    """File upload section for legal documents"""
    st.subheader("📁 Legal Document Upload")
    st.info("Upload legal documents for events extraction (PDF, DOCX, TXT, etc.)")

    file_handler = FileHandler()

    uploaded_files = st.file_uploader(
        "Upload legal documents",
        type=file_handler.supported_extensions,
        accept_multiple_files=True,
        help="STRICT: Uses Docling for text extraction, LangExtract for events identification"
    )

    if uploaded_files:
        st.success(f"📄 {len(uploaded_files)} document(s) uploaded for legal events extraction")

        with st.expander("View uploaded documents"):
            for file in uploaded_files:
                file_info = file_handler.get_file_info(file)
                status = "✅" if file_info['supported'] else "❌"
                st.write(f"{status} **{file.name}** - {file_info['size_mb']:.2f} MB ({file_info['type']})")

    return uploaded_files


def process_documents_and_display_table(uploaded_files):
    """STRICT pipeline processing per guardrails - uses shared utilities"""
    return process_documents_with_spinner(uploaded_files, show_subheader=True)


# All display and processing functions now use shared utilities from streamlit_common


def main():
    """Main application following STRICT guardrails sequence"""

    # STEP 1: STRICT environment validation (halts if GEMINI_API_KEY missing)
    strict_environment_check()

    # Create tabs with mandatory "Legal Events Table" tab per guardrails
    tab1, tab2 = st.tabs(["📁 Document Processing", "📋 Legal Events Table"])

    with tab1:
        # File upload and processing
        uploaded_files = create_file_upload_section()

        if uploaded_files:
            # Process through STRICT pipeline
            legal_events_df = process_documents_and_display_table(uploaded_files)

            # Store results in session state
            if legal_events_df is not None:
                st.session_state['legal_events_df'] = legal_events_df
                st.success("✅ Legal events extracted - view in 'Legal Events Table' tab")

    with tab2:
        # MANDATORY: Legal Events Table display per guardrails
        if 'legal_events_df' in st.session_state:
            legal_events_df = st.session_state['legal_events_df']

            # Display the mandatory five-column table using shared utilities
            display_legal_events_table(legal_events_df)

            # Download functionality using shared utilities
            create_download_section(legal_events_df)

        else:
            st.info("📄 No legal events extracted yet. Please process documents in the 'Document Processing' tab first.")

    # Footer with guardrails compliance
    st.markdown("---")
    st.caption("🔒 STRICT MODE: Compliant with assistant guardrails | Docling → LangExtract → Five-Column Table")


if __name__ == "__main__":
    main()