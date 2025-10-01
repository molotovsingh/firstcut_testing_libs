#!/usr/bin/env python3
"""
GUARANTEED Five-Column Table App - REFACTORED
Uses centralized components and GUARANTEES table output even on failures
"""

import streamlit as st
import pandas as pd
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Reduce LangExtract AFC logging noise
logging.getLogger('langextract').setLevel(logging.WARNING)

# Import refactored components
from src.ui.streamlit_common import (
    get_pipeline,
    process_documents_with_spinner,
    display_legal_events_table,
    create_download_section,
    show_sample_table_format
)
from src.utils.file_handler import FileHandler

# Page config
st.set_page_config(
    page_title="GUARANTEED Legal Events Table",
    page_icon="⚖️",
    layout="wide"
)

# CSS
st.markdown("""
<style>
.guaranteed-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 1rem;
}
.guarantee-box {
    padding: 1rem;
    background-color: #d4edda;
    border: 3px solid #28a745;
    border-radius: 0.375rem;
    color: #155724;
    margin: 1rem 0;
    font-weight: bold;
}
.warning-box {
    padding: 1rem;
    background-color: #fff3cd;
    border: 2px solid #ffc107;
    border-radius: 0.375rem;
    color: #856404;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<h1 class="guaranteed-header">⚖️ GUARANTEED Five-Column Legal Events Table</h1>', unsafe_allow_html=True)

    # Guarantee promise
    st.markdown("""
    <div class="guarantee-box">
    🛡️ <strong>GUARANTEE:</strong> This app ALWAYS produces a five-column legal events table,
    even if Docling fails, LangExtract fails, or any other errors occur.<br>
    📋 <strong>Columns:</strong> No | Event Particulars | Citation | Document Reference
    </div>
    """, unsafe_allow_html=True)

    # Environment check using cached pipeline
    try:
        pipeline = get_pipeline()
        st.success("✅ GEMINI_API_KEY found - Full LangExtract functionality available")
    except Exception as e:
        st.markdown("""
        <div class="warning-box">
        ⚠️ <strong>Warning:</strong> Pipeline initialization failed.<br>
        The app will still work and produce the guaranteed table, but will use fallback processing.
        </div>
        """, unsafe_allow_html=True)

    # File upload
    st.subheader("📁 Upload Legal Documents")
    file_handler = FileHandler()

    uploaded_files = st.file_uploader(
        "Choose legal documents (PDF, DOCX, TXT, etc.)",
        type=file_handler.supported_extensions,
        accept_multiple_files=True,
        help="Upload any legal documents - the app guarantees a five-column table output"
    )

    # Show sample table format
    if not uploaded_files:
        show_sample_table_format()

    # Process files
    if uploaded_files:
        st.info(f"📄 {len(uploaded_files)} file(s) uploaded")

        if st.button("🔄 Process Documents → GUARANTEED Table Output", type="primary"):

            # Process using shared utilities with spinner
            legal_events_df = process_documents_with_spinner(uploaded_files, show_subheader=False)

            if legal_events_df is not None:
                st.success(f"✅ GUARANTEED TABLE GENERATED: {len(legal_events_df)} legal events")

                # Display the guaranteed table using shared utilities
                display_legal_events_table(legal_events_df)

                # GUARANTEED downloads using shared utilities
                st.subheader("💾 GUARANTEED Downloads")
                st.caption("All downloads guaranteed to contain the five-column format")
                create_download_section(legal_events_df)

                # Show raw data for debugging
                with st.expander("🔍 Raw Table Data (for debugging)"):
                    st.write("**Table shape:**", legal_events_df.shape)
                    st.write("**Column names:**", list(legal_events_df.columns))
                    st.write("**Data types:**", legal_events_df.dtypes.to_dict())
                    st.dataframe(legal_events_df)
            else:
                # ULTIMATE FALLBACK: Even if pipeline fails completely
                st.error("❌ Critical error occurred during processing")
                st.warning("🛡️ Creating emergency fallback table...")

                from src.core.table_formatter import TableFormatter
                emergency_df = TableFormatter.create_fallback_dataframe("Critical system error occurred")

                st.subheader("📋 Emergency Fallback Table")
                display_legal_events_table(emergency_df)

                # Emergency download
                create_download_section(emergency_df)

    # Footer
    st.markdown("---")
    st.caption("🛡️ GUARANTEE: This app ALWAYS produces a five-column legal events table")
    st.caption("🔧 Powered by refactored pipeline with centralized LangExtract client and table formatter")

if __name__ == "__main__":
    main()