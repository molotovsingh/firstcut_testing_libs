"""
Chart Generation Module - Plotly Visualizations for Test Results
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ChartGenerator:
    """Generates Plotly charts for docling + langextract test results"""

    def __init__(self):
        self.color_schemes = {
            'success': ['#28a745', '#ffc107', '#dc3545'],  # Green, Yellow, Red
            'docling': 'RdYlGn',
            'dates': 'lightblue',
            'language': 'viridis'
        }

    def create_docling_success_chart(self, df: pd.DataFrame) -> Optional[go.Figure]:
        """Create Docling success rate chart by file type"""
        if df is None or df.empty or 'docling_success' not in df.columns:
            return None

        try:
            success_by_type = df.groupby('file_type')['docling_success'].agg(['sum', 'count']).reset_index()
            success_by_type['success_rate'] = (success_by_type['sum'] / success_by_type['count'] * 100).round(1)

            fig = px.bar(
                success_by_type,
                x='file_type',
                y='success_rate',
                title='🧪 Docling Success Rate by File Type',
                labels={'success_rate': 'Success Rate (%)', 'file_type': 'File Type'},
                color='success_rate',
                color_continuous_scale=self.color_schemes['docling']
            )
            fig.update_layout(showlegend=False)
            return fig

        except Exception as e:
            logger.error(f"Failed to create Docling success chart: {e}")
            return None

    def create_date_extraction_chart(self, df: pd.DataFrame) -> Optional[go.Figure]:
        """Create date extraction results histogram"""
        if df is None or df.empty or 'dates_found' not in df.columns:
            return None

        try:
            # Fix the numpy/plotly type issue
            max_dates = df['dates_found'].max()
            nbins = int(max(max_dates, 1) if max_dates > 0 else 1)

            fig = px.histogram(
                df,
                x='dates_found',
                title='📅 Date Extraction Results (Business Use Case)',
                labels={'dates_found': 'Number of Dates Found', 'count': 'Number of Documents'},
                nbins=nbins
            )
            fig.update_traces(marker_color=self.color_schemes['dates'])
            return fig

        except Exception as e:
            logger.error(f"Failed to create date extraction chart: {e}")
            return None

    def create_pipeline_success_chart(self, df: pd.DataFrame) -> Optional[go.Figure]:
        """Create pipeline success breakdown pie chart"""
        if df is None or df.empty or 'pipeline_success' not in df.columns or 'docling_success' not in df.columns:
            return None

        try:
            # Create success breakdown data
            breakdown_data = []
            for _, row in df.iterrows():
                if row['docling_success'] and row['pipeline_success']:
                    breakdown_data.append({'Status': 'Full Success', 'File': row['filename']})
                elif row['docling_success'] and not row['pipeline_success']:
                    breakdown_data.append({'Status': 'Docling Success, No Dates', 'File': row['filename']})
                else:
                    breakdown_data.append({'Status': 'Docling Failed', 'File': row['filename']})

            breakdown_df = pd.DataFrame(breakdown_data)
            status_counts = breakdown_df['Status'].value_counts()

            color_map = {
                'Full Success': self.color_schemes['success'][0],
                'Docling Success, No Dates': self.color_schemes['success'][1],
                'Docling Failed': self.color_schemes['success'][2]
            }

            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title='🔬 Pipeline Test Results',
                color_discrete_map=color_map
            )
            return fig

        except Exception as e:
            logger.error(f"Failed to create pipeline success chart: {e}")
            return None

    def create_language_detection_chart(self, df: pd.DataFrame) -> Optional[go.Figure]:
        """Create language detection results chart"""
        if df is None or df.empty or 'language' not in df.columns:
            return None

        try:
            lang_counts = df['language'].value_counts()

            fig = px.bar(
                x=lang_counts.index,
                y=lang_counts.values,
                title='🌍 Language Detection Results',
                labels={'x': 'Detected Language', 'y': 'Number of Documents'},
                color=lang_counts.values,
                color_continuous_scale=self.color_schemes['language']
            )
            return fig

        except Exception as e:
            logger.error(f"Failed to create language detection chart: {e}")
            return None

    def create_all_charts(self, df: pd.DataFrame) -> Tuple[Optional[go.Figure], ...]:
        """
        Create all charts at once

        Returns:
            Tuple of (docling_chart, dates_chart, pipeline_chart, language_chart)
        """
        if df is None or df.empty:
            return None, None, None, None

        return (
            self.create_docling_success_chart(df),
            self.create_date_extraction_chart(df),
            self.create_pipeline_success_chart(df),
            self.create_language_detection_chart(df)
        )