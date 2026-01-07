"""
PDF Renderer for reports.
Uses ReportLab for PDF generation with styled tables and charts.
Adapted from REPORTING_MODULE_REPLICATION_GUIDE.md
"""
from io import BytesIO
from .base import BaseRenderer

# ReportLab imports - handle gracefully if not installed
REPORTLAB_AVAILABLE = False
colors = None
letter = None
inch = None
SimpleDocTemplate = None
Paragraph = None
Spacer = None
Table = None
TableStyle = None
getSampleStyleSheet = None
ParagraphStyle = None

try:
    from reportlab.lib import colors as _colors
    from reportlab.lib.pagesizes import letter as _letter
    from reportlab.lib.styles import getSampleStyleSheet as _getSampleStyleSheet
    from reportlab.lib.styles import ParagraphStyle as _ParagraphStyle
    from reportlab.lib.units import inch as _inch
    from reportlab.platypus import (
        SimpleDocTemplate as _SimpleDocTemplate,
        Paragraph as _Paragraph,
        Spacer as _Spacer,
        Table as _Table,
        TableStyle as _TableStyle,
    )
    # Assign to module-level names
    colors = _colors
    letter = _letter
    inch = _inch
    SimpleDocTemplate = _SimpleDocTemplate
    Paragraph = _Paragraph
    Spacer = _Spacer
    Table = _Table
    TableStyle = _TableStyle
    getSampleStyleSheet = _getSampleStyleSheet
    ParagraphStyle = _ParagraphStyle
    REPORTLAB_AVAILABLE = True
except ImportError:
    pass


class PDFRenderer(BaseRenderer):
    """
    Renders reports as PDF documents with styled tables and charts.
    Uses ReportLab library for professional-quality output.
    """

    @property
    def content_type(self) -> str:
        return 'application/pdf'

    @property
    def file_extension(self) -> str:
        return '.pdf'

    def _get_colors(self):
        """Get color constants - must be called after checking REPORTLAB_AVAILABLE."""
        return {
            'header_bg': colors.HexColor('#1e3a5f'),  # Navy blue
            'header_text': colors.white,
            'row_alt_bg': colors.HexColor('#f5f7fa'),  # Light gray
            'accent': colors.HexColor('#2563eb'),  # Blue accent
            'gray': colors.gray,
        }

    def render(self) -> BytesIO:
        """Render report data as PDF."""
        if not REPORTLAB_AVAILABLE:
            raise ImportError(
                "reportlab is required for PDF rendering. "
                "Install it with: pip install reportlab"
            )

        # Get colors now that we know reportlab is available
        clrs = self._get_colors()

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch
        )

        # Build the PDF content
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=12,
            textColor=clrs['header_bg']
        )

        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=clrs['gray'],
            spaceAfter=20
        )

        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=8,
            textColor=clrs['header_bg']
        )

        # Title
        report_title = self.metadata.get('report_title', self.report_name)
        story.append(Paragraph(report_title, title_style))

        # Subtitle with generation info
        generated_at = self.metadata.get('generated_at', 'N/A')
        org_name = self.metadata.get('organization', 'N/A')
        period = f"{self.metadata.get('period_start', 'N/A')} to {self.metadata.get('period_end', 'N/A')}"
        subtitle_text = f"Organization: {org_name} | Period: {period} | Generated: {generated_at}"
        story.append(Paragraph(subtitle_text, subtitle_style))

        # Add sections based on report type
        self._add_overview_section(story, section_style, styles, clrs)
        self._add_data_tables(story, section_style, styles, clrs)
        self._add_recommendations_section(story, section_style, styles, clrs)

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    def _add_overview_section(self, story, section_style, styles, clrs):
        """Add overview/summary section."""
        overview = self.report_data.get('overview', {})
        if not overview:
            # Try alternative keys
            overview = self.report_data.get('summary', {})
            if not overview:
                overview = self.report_data.get('kpis', {})

        if overview:
            story.append(Paragraph("Overview", section_style))

            # Create KPI table
            kpi_data = [['Metric', 'Value']]
            for key, value in overview.items():
                label = key.replace('_', ' ').title()
                if 'spend' in key.lower() or 'amount' in key.lower() or 'savings' in key.lower():
                    formatted_value = self.format_currency(value)
                elif 'percentage' in key.lower() or 'rate' in key.lower():
                    formatted_value = self.format_percentage(value)
                elif isinstance(value, (int, float)):
                    formatted_value = self.format_number(value)
                else:
                    formatted_value = str(value)
                kpi_data.append([label, formatted_value])

            if len(kpi_data) > 1:
                table = self._create_styled_table(kpi_data, clrs)
                story.append(table)
                story.append(Spacer(1, 12))

    def _add_data_tables(self, story, section_style, styles, clrs):
        """Add data tables for various report sections."""
        # Map of common data keys to section titles
        data_sections = {
            'spend_by_category': 'Spend by Category',
            'spend_by_supplier': 'Spend by Supplier',
            'top_suppliers': 'Top Suppliers',
            'top_categories': 'Top Categories',
            'monthly_trend': 'Monthly Trend',
            'pareto_data': 'Pareto Analysis',
            'tail_suppliers': 'Tail Spend Suppliers',
            'consolidation_opportunities': 'Consolidation Opportunities',
            'category_opportunities': 'Category Opportunities',
            'stratification': 'Spend Stratification',
            'compliance_summary': 'Compliance Summary',
            'violations': 'Policy Violations',
        }

        for key, title in data_sections.items():
            data = self.report_data.get(key, [])
            if data and isinstance(data, list) and len(data) > 0:
                story.append(Paragraph(title, section_style))
                table = self._create_data_table(data, clrs)
                if table:
                    story.append(table)
                    story.append(Spacer(1, 12))

    def _add_recommendations_section(self, story, section_style, styles, clrs):
        """Add recommendations/action plan section."""
        action_plan = self.report_data.get('action_plan', [])
        recommendations = self.report_data.get('recommendations', [])
        items = action_plan or recommendations

        if items:
            story.append(Paragraph("Recommendations", section_style))

            for i, item in enumerate(items, 1):
                if isinstance(item, dict):
                    action = item.get('action', item.get('recommendation', ''))
                    description = item.get('description', '')
                    text = f"<b>{i}. {action}</b>"
                    if description:
                        text += f": {description}"
                else:
                    text = f"<b>{i}.</b> {item}"

                story.append(Paragraph(text, styles['Normal']))
                story.append(Spacer(1, 4))

    def _create_styled_table(self, data, clrs, col_widths=None):
        """
        Create a styled table with navy blue headers.
        Adapted from reference guide's _create_styled_table().
        """
        table = Table(data, colWidths=col_widths)

        style = TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), clrs['header_bg']),
            ('TEXTCOLOR', (0, 0), (-1, 0), clrs['header_text']),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),

            # Data row styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),

            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, clrs['gray']),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])

        # Alternating row colors
        for i in range(1, len(data)):
            if i % 2 == 0:
                style.add('BACKGROUND', (0, i), (-1, i), clrs['row_alt_bg'])

        table.setStyle(style)
        return table

    def _create_data_table(self, data, clrs):
        """Create a table from a list of dictionaries."""
        if not data or not isinstance(data[0], dict):
            return None

        # Get headers from first item
        headers = list(data[0].keys())
        table_data = [[h.replace('_', ' ').title() for h in headers]]

        # Add rows
        for item in data[:20]:  # Limit to 20 rows for PDF
            row = []
            for header in headers:
                value = item.get(header, '')
                # Format based on header name
                if 'amount' in header.lower() or 'spend' in header.lower() or 'savings' in header.lower():
                    row.append(self.format_currency(value))
                elif 'percentage' in header.lower() or 'rate' in header.lower():
                    row.append(self.format_percentage(value))
                elif isinstance(value, (int, float)):
                    row.append(self.format_number(value, 2 if isinstance(value, float) else 0))
                else:
                    # Truncate long text
                    str_value = str(value)
                    row.append(str_value[:50] + '...' if len(str_value) > 50 else str_value)
            table_data.append(row)

        return self._create_styled_table(table_data, clrs)
