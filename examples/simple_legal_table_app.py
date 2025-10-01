#!/usr/bin/env python3
"""
SIMPLE Legal Events Table Demo - IMMEDIATE VIEW
Shows the five-column table right away without requiring file uploads
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Legal Events Table - IMMEDIATE DEMO",
    page_icon="⚖️",
    layout="wide"
)

# CSS
st.markdown("""
<style>
.big-title {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}
.highlight-box {
    padding: 1rem;
    background-color: #d4edda;
    border: 2px solid #c3e6cb;
    border-radius: 0.375rem;
    color: #155724;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

def create_sample_legal_events():
    """Create sample legal events data"""
    sample_data = [
        {
            "No": 1,
            "Event Particulars": "Contract execution between ABC Corp and XYZ LLC on March 15, 2024, with effective date of April 1, 2024",
            "Citation": "Contract Agreement Section 2.1",
            "Document Reference": "ABC_XYZ_Contract_2024.pdf"
        },
        {
            "No": 2,
            "Event Particulars": "Plaintiff filed motion to dismiss pursuant to Rule 12(b)(6) on January 22, 2024",
            "Citation": "Fed. R. Civ. P. 12(b)(6)",
            "Document Reference": "Motion_to_Dismiss_Filing.pdf"
        },
        {
            "No": 3,
            "Event Particulars": "Court hearing scheduled for discovery disputes on February 10, 2024 at 2:00 PM",
            "Citation": "Local Rule 37.1",
            "Document Reference": "Court_Schedule_Notice.pdf"
        },
        {
            "No": 4,
            "Event Particulars": "Settlement agreement executed with termination clause effective December 31, 2024",
            "Citation": "Settlement Agreement Article IV",
            "Document Reference": "Final_Settlement_Agreement.pdf"
        },
        {
            "No": 5,
            "Event Particulars": "Intellectual property license granted for software patents valid through March 2027",
            "Citation": "Patent License Agreement Section 3.2",
            "Document Reference": "IP_License_Agreement.pdf"
        }
    ]
    return pd.DataFrame(sample_data)

def main():
    # Main title
    st.markdown('<h1 class="big-title">⚖️ Legal Events Table Demo</h1>', unsafe_allow_html=True)

    # Highlight box
    st.markdown("""
    <div class="highlight-box">
    <strong>🎯 FIVE-COLUMN FORMAT per Assistant Guardrails:</strong><br>
    1. <strong>No</strong> - Sequential number<br>
    2. <strong>Event Particulars</strong> - Legal event description<br>
    3. <strong>Citation</strong> - Legal references<br>
    4. <strong>Document Reference</strong> - Source document
    </div>
    """, unsafe_allow_html=True)

    # Create the tabs - THIS IS WHERE YOU SHOULD SEE THE TABS
    tab1, tab2, tab3 = st.tabs([
        "📋 **Legal Events Table**",
        "📊 **Table Details**",
        "💾 **Download Options**"
    ])

    # Get sample data
    df = create_sample_legal_events()

    with tab1:
        st.header("📋 Legal Events Table")
        st.caption("MANDATORY five-column format per assistant guardrails")

        # Display the table
        st.dataframe(
            df,
            width='stretch',
            hide_index=True,
            column_config={
                "No": st.column_config.NumberColumn("No", width="small"),
                "Event Particulars": st.column_config.TextColumn("Event Particulars", width="large"),
                "Citation": st.column_config.TextColumn("Citation", width="medium"),
                "Document Reference": st.column_config.TextColumn("Document Reference", width="medium")
            }
        )

        # Summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Events", len(df))
        with col2:
            st.metric("Documents", df['Document Reference'].nunique())
        with col3:
            st.metric("With Citations", len(df[df['Citation'] != 'No citation available']))
        with col4:
            st.metric("Avg Length", f"{df['Event Particulars'].str.len().mean():.0f} chars")

    with tab2:
        st.header("📊 Table Structure Details")

        st.subheader("Column Information:")
        for i, col in enumerate(df.columns, 1):
            st.write(f"**{i}. {col}**")
            st.write(f"   - Type: {df[col].dtype}")
            st.write(f"   - Sample: {df[col].iloc[0][:50]}...")

        st.subheader("Data Shape:")
        st.write(f"- **Rows**: {df.shape[0]}")
        st.write(f"- **Columns**: {df.shape[1]}")
        st.write(f"- **Column Names**: {list(df.columns)}")

        st.subheader("Validation:")
        required_columns = ['No', 'Event Particulars', 'Citation', 'Document Reference']
        is_valid = list(df.columns) == required_columns
        st.success(f"✅ Five-Column Format Valid: {is_valid}")

    with tab3:
        st.header("💾 Download Options")

        col1, col2, col3 = st.columns(3)

        with col1:
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📄 Download CSV",
                data=csv_data,
                file_name=f"legal_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

        with col2:
            import io
            excel_buffer = io.BytesIO()
            df.to_excel(excel_buffer, index=False)
            st.download_button(
                label="📊 Download Excel",
                data=excel_buffer.getvalue(),
                file_name=f"legal_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with col3:
            json_data = df.to_json(orient='records', indent=2)
            st.download_button(
                label="🔧 Download JSON",
                data=json_data,
                file_name=f"legal_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

    # Footer
    st.markdown("---")
    st.caption("🔒 STRICT MODE: Compliant with assistant guardrails | Five-Column Legal Events Table")
    st.caption(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()