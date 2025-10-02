#!/usr/bin/env python3
"""
STANDARDIZED Legal Events Extraction - Granite Guardrails Compliant
Unified Five-Column Table: Docling + LangExtract + Shared Utilities
"""

import streamlit as st
import os
from dotenv import load_dotenv
import logging

# Import refactored shared utilities for guard-railed five-column exports
from src.ui.streamlit_common import (
    get_pipeline,
    process_documents_with_spinner,
    display_legal_events_table,
    create_download_section
)
from src.utils.file_handler import FileHandler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reduce LangExtract AFC logging noise
logging.getLogger('langextract').setLevel(logging.WARNING)

# Page config
st.set_page_config(
    page_title="Paralegal Date Extraction Test - Docling + Langextract",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Minimal styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

.main-header {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 1.75rem;
    font-weight: 500;
    color: #222;
    text-align: center;
    margin-bottom: 1rem;
}
.main-caption {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 0.95rem;
    color: #555;
    text-align: center;
    margin-bottom: 2rem;
}
div[data-testid="stSidebar"] {
    font-size: 0.75rem;
}
.stMarkdown {
    font-size: 0.875rem;
}
</style>
""", unsafe_allow_html=True)


def create_file_upload_section():
    """Create the file upload section"""
    st.subheader("Document Upload")

    uploaded_files = st.file_uploader(
        "Choose files",
        type=['pdf', 'docx', 'txt', 'msg'],
        accept_multiple_files=True,
        help="Supported formats: PDF, DOCX, TXT, MSG"
    )

    if uploaded_files:
        st.subheader("File Summary")
        file_handler = FileHandler()

        # Create dataframe for file summary
        file_data = []
        for file in uploaded_files:
            file_info = file_handler.get_file_info(file)
            status = "Supported" if file_info['supported'] else "Unsupported"
            file_data.append({
                "File": file_info['name'],
                "Size MB": f"{file_info['size_mb']:.2f}",
                "Status": status
            })

        # Display as clean table
        import pandas as pd
        summary_df = pd.DataFrame(file_data)
        st.dataframe(summary_df, width='stretch', hide_index=True)

    return uploaded_files


def main():
    """Main Streamlit application"""

    # Header
    st.markdown('<h1 class="main-header">Legal Events Extraction</h1>', unsafe_allow_html=True)
    st.markdown('<p class="main-caption">Document processing using Docling + LangExtract</p>', unsafe_allow_html=True)

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_files = create_file_upload_section()

    with col2:
        st.subheader("Processing")

        # Provider selection control
        st.markdown("**Event Provider**")

        # Get default from environment or session state
        default_provider = os.getenv('EVENT_EXTRACTOR', 'langextract').lower()
        if 'selected_provider' not in st.session_state:
            st.session_state.selected_provider = default_provider

        # Provider options with descriptions
        provider_options = {
            'langextract': 'LangExtract (Google Gemini)',
            'openrouter': 'OpenRouter (Unified API)',
            'opencode_zen': 'OpenCode Zen (Legal AI)',
            'openai': 'OpenAI (GPT-4o/4-mini)'
        }

        # Radio group for provider selection
        selected_provider = st.radio(
            "Select event extraction provider:",
            options=list(provider_options.keys()),
            format_func=lambda x: provider_options[x],
            index=list(provider_options.keys()).index(st.session_state.selected_provider),
            help="Choose the AI provider for legal event extraction. Credentials required in .env file:\n"
                 "• LangExtract: GEMINI_API_KEY\n"
                 "• OpenRouter: OPENROUTER_API_KEY\n"
                 "• OpenCode Zen: OPENCODEZEN_API_KEY\n"
                 "• OpenAI: OPENAI_API_KEY",
            key="provider_selector"
        )

        # Update session state if changed
        if selected_provider != st.session_state.selected_provider:
            st.session_state.selected_provider = selected_provider
            # Clear previous results when provider changes
            if 'legal_events_df' in st.session_state:
                del st.session_state.legal_events_df
            st.info(f"🔄 Provider changed to {provider_options[selected_provider]}")

        st.divider()

        if uploaded_files:
            if st.button("Process Files", type="primary"):
                # Simple status container
                status_container = st.empty()

                with status_container:
                    st.text("Processing...")

                # Process using shared utilities with selected provider
                legal_events_df = process_documents_with_spinner(
                    uploaded_files,
                    show_subheader=False,
                    provider=st.session_state.selected_provider
                )

                if legal_events_df is not None:
                    # Store results in session state
                    st.session_state.legal_events_df = legal_events_df
                    status_container.text("Complete")
                else:
                    status_container.text("Failed")
        else:
            st.text("Upload files to begin processing")

    # Results section - Guardrailed Five-Column Table
    if 'legal_events_df' in st.session_state:
        st.divider()

        legal_events_df = st.session_state.legal_events_df

        # Display standardized five-column legal events table
        display_legal_events_table(legal_events_df)

        # Provide standardized downloads with provider context
        provider = st.session_state.get('selected_provider', default_provider)
        create_download_section(legal_events_df, provider=provider)

    # Footer
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            "<div style='text-align: center; color: #666; font-size: 0.85rem;'>"
            "Legal Events Extraction | Docling + LangExtract"
            "</div>",
            unsafe_allow_html=True
        )


if __name__ == "__main__":
    main()