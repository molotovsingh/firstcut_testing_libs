#!/usr/bin/env python3
"""
SIMPLE Legal Events Processing App
Upload → Process → See Five-Column Table → Download
"""

import streamlit as st
import pandas as pd
import os
import io
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Reduce LangExtract AFC logging noise
logging.getLogger('langextract').setLevel(logging.WARNING)

# Import components
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
    page_title="Simple Legal Events Processor",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Legal Events Processor")
st.caption("Upload documents → Process through Docling + LangExtract → See five-column table")

# STEP 1: Environment Check using cached pipeline
try:
    pipeline = get_pipeline()
    st.success("✅ GEMINI_API_KEY found - Ready to process")
except Exception as e:
    st.error(f"🚨 Pipeline initialization failed: {e}")
    st.stop()

# STEP 2: File Upload
st.subheader("📁 Upload Legal Documents")
file_handler = FileHandler()

uploaded_files = st.file_uploader(
    "Choose legal documents (PDF, DOCX, TXT, etc.)",
    type=file_handler.supported_extensions,
    accept_multiple_files=True
)

if uploaded_files:
    st.info(f"📄 {len(uploaded_files)} file(s) uploaded")

    # STEP 3: Process Button
    if st.button("🔄 Process Documents → Extract Legal Events", type="primary"):
        # Process using shared utilities
        legal_events_df = process_documents_with_spinner(uploaded_files)

        if legal_events_df is not None:
            # STEP 4: SUCCESS! Show the five-column table using shared utilities
            display_legal_events_table(legal_events_df)

            # STEP 5: Download Options using shared utilities
            create_download_section(legal_events_df)

            # Optional: Auto-download hint
            st.info("💡 Click any download button above to save the five-column legal events table")
        else:
            st.error("❌ Processing failed - no legal events could be extracted")

else:
    # Show sample format using shared utilities
    show_sample_table_format()

# Footer
st.markdown("---")
st.caption("🔒 STRICT: Docling → LangExtract → Five-Column Table per assistant guardrails")