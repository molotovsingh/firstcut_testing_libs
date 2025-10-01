"""
Table Formatter - Shared formatting logic for five-column legal events table
Ensures consistency between pipeline, UI, and downloads
"""

import pandas as pd
import logging
from typing import List, Dict, Any

from .constants import FIVE_COLUMN_HEADERS, INTERNAL_FIELDS, DEFAULT_NO_DATE

logger = logging.getLogger(__name__)


class TableFormatter:
    """
    Shared table formatting logic for legal events
    Ensures consistent five-column format across all components
    """

    @staticmethod
    def normalize_records_to_dataframe(records: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert internal record format to standardized DataFrame

        Args:
            records: List of records with internal field names

        Returns:
            DataFrame with standardized column headers
        """
        if not records:
            logger.warning("⚠️ No records provided - creating empty DataFrame")
            return pd.DataFrame(columns=FIVE_COLUMN_HEADERS)

        try:
            # Create DataFrame from records
            df = pd.DataFrame(records)

            # Ensure all required internal fields exist
            for field in INTERNAL_FIELDS:
                if field not in df.columns:
                    logger.warning(f"⚠️ Missing field {field} - adding default values")
                    if field == "number":
                        df[field] = range(1, len(df) + 1)
                    elif field == "date":
                        df[field] = DEFAULT_NO_DATE
                    elif field == "event_particulars":
                        df[field] = "Event details not available"
                    elif field == "citation":
                        df[field] = "No citation available"
                    elif field == "document_reference":
                        df[field] = "Unknown document"

            # Select and reorder columns to match internal field order
            df = df[INTERNAL_FIELDS]

            # Rename columns to display headers
            df.columns = FIVE_COLUMN_HEADERS

            # Sort by number column
            df = df.sort_values(FIVE_COLUMN_HEADERS[0]).reset_index(drop=True)

            # Validate final format
            if not TableFormatter.validate_dataframe_format(df):
                logger.error("❌ DataFrame validation failed after normalization")
                return TableFormatter.create_fallback_dataframe("DataFrame validation failed")

            logger.info(f"✅ Normalized {len(df)} records to standard format")
            return df

        except Exception as e:
            logger.error(f"❌ Failed to normalize records: {e}")
            return TableFormatter.create_fallback_dataframe(f"Normalization error: {str(e)}")

    @staticmethod
    def validate_dataframe_format(df: pd.DataFrame) -> bool:
        """
        Validate that DataFrame matches required five-column format

        Args:
            df: DataFrame to validate

        Returns:
            True if valid, False otherwise
        """
        if df is None or df.empty:
            return False

        # Check column names match exactly
        if list(df.columns) != FIVE_COLUMN_HEADERS:
            logger.error(f"❌ Column mismatch. Expected: {FIVE_COLUMN_HEADERS}, Got: {list(df.columns)}")
            return False

        # Check required columns have data
        for col in FIVE_COLUMN_HEADERS:
            if df[col].isnull().all():
                logger.error(f"❌ Column {col} has no data")
                return False

        # Check number column contains valid integers
        try:
            if not df[FIVE_COLUMN_HEADERS[0]].dtype.kind in 'iu':  # integer or unsigned int
                logger.error(f"❌ Number column contains non-integer values")
                return False
        except Exception as e:
            logger.error(f"❌ Error validating number column: {e}")
            return False

        return True

    @staticmethod
    def create_fallback_dataframe(reason: str = "Unknown error") -> pd.DataFrame:
        """
        Create a fallback DataFrame when normal processing fails
        Guarantees valid five-column format

        Args:
            reason: Reason for fallback

        Returns:
            Valid DataFrame with one fallback record
        """
        fallback_record = {
            FIVE_COLUMN_HEADERS[0]: 1,  # No
            FIVE_COLUMN_HEADERS[1]: DEFAULT_NO_DATE,  # Date
            FIVE_COLUMN_HEADERS[2]: f"Processing failed: {reason}",  # Event Particulars
            FIVE_COLUMN_HEADERS[3]: "No citation available (processing failed)",  # Citation
            FIVE_COLUMN_HEADERS[4]: "Unknown document"  # Document Reference
        }

        df = pd.DataFrame([fallback_record])
        logger.info(f"✅ Created fallback DataFrame: {reason}")
        return df

    @staticmethod
    def prepare_for_export(df: pd.DataFrame, format_type: str = "xlsx") -> bytes:
        """
        Prepare DataFrame for export in specified format

        Args:
            df: DataFrame to export
            format_type: Export format ('xlsx', 'csv', 'json')

        Returns:
            Exported data as bytes
        """
        if not TableFormatter.validate_dataframe_format(df):
            logger.error("❌ Cannot export invalid DataFrame format")
            df = TableFormatter.create_fallback_dataframe("Invalid format for export")

        try:
            if format_type.lower() == "xlsx":
                import io
                buffer = io.BytesIO()
                df.to_excel(buffer, index=False)
                return buffer.getvalue()

            elif format_type.lower() == "csv":
                return df.to_csv(index=False).encode('utf-8')

            elif format_type.lower() == "json":
                return df.to_json(orient='records', indent=2).encode('utf-8')

            else:
                raise ValueError(f"Unsupported export format: {format_type}")

        except Exception as e:
            logger.error(f"❌ Export failed: {e}")
            # Return fallback CSV as bytes
            fallback_df = TableFormatter.create_fallback_dataframe(f"Export error: {str(e)}")
            return fallback_df.to_csv(index=False).encode('utf-8')

    @staticmethod
    def get_table_summary(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate summary statistics for the legal events table

        Args:
            df: DataFrame to summarize

        Returns:
            Dictionary with summary statistics
        """
        if not TableFormatter.validate_dataframe_format(df):
            return {
                "total_events": 0,
                "unique_documents": 0,
                "events_with_citations": 0,
                "avg_particulars_length": 0
            }

        try:
            # Calculate statistics
            total_events = len(df)
            unique_docs = df[FIVE_COLUMN_HEADERS[4]].nunique()  # Document Reference

            # Count events with real citations (not default)
            citation_col = FIVE_COLUMN_HEADERS[3]  # Citation
            events_with_citations = len(df[
                (~df[citation_col].str.contains("No citation available", na=False)) &
                (~df[citation_col].str.contains("processing failed", na=False))
            ])

            # Average length of event particulars
            particulars_col = FIVE_COLUMN_HEADERS[2]  # Event Particulars
            avg_length = df[particulars_col].str.len().mean()

            return {
                "total_events": total_events,
                "unique_documents": unique_docs,
                "events_with_citations": events_with_citations,
                "avg_particulars_length": round(avg_length, 1) if avg_length else 0
            }

        except Exception as e:
            logger.error(f"❌ Failed to generate table summary: {e}")
            return {
                "total_events": 0,
                "unique_documents": 0,
                "events_with_citations": 0,
                "avg_particulars_length": 0
            }