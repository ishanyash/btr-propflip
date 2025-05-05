from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io
import datetime

def create_pdf(report_content, address):
    """Create a PDF from the report content"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=16,
        spaceAfter=12
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=6
    )
    
    subheading_style = ParagraphStyle(
        'Subheading',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=6
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    # Content elements
    elements = []
    
    # Report header
    report_date = datetime.datetime.now().strftime('%b %d, %Y').upper()
    elements.append(Paragraph(f"BTR REPORT GENERATED {report_date}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Process the report content - split into sections
    lines = report_content.strip().split('\n')
    current_section = []
    
    for line in lines:
        if line.startswith('# '):
            # New main heading - process previous section
            if current_section:
                elements.append(Paragraph('\n'.join(current_section), normal_style))
                current_section = []
            # Add the new heading
            elements.append(Paragraph(line[2:], heading_style))
        elif line.startswith('## '):
            # New subheading - process previous section
            if current_section:
                elements.append(Paragraph('\n'.join(current_section), normal_style))
                current_section = []
            # Add the new subheading
            elements.append(Paragraph(line[3:], subheading_style))
        else:
            # Add to current section
            current_section.append(line)
    
    # Add any remaining content
    if current_section:
        elements.append(Paragraph('\n'.join(current_section), normal_style))
    
    # Disclaimer
    elements.append(Spacer(1, 20))
    disclaimer_text = "The accuracy of this BTR report and its applicability to your circumstances are not guaranteed. "
    disclaimer_text += "This report is offered for educational purposes only, and is not a substitute for professional advice. "
    disclaimer_text += "All figures provided are estimates only and may not reflect actual results."
    
    elements.append(Paragraph(disclaimer_text, ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.gray
    )))
    
    # Build the PDF
    doc.build(elements)
    
    # Get the PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data