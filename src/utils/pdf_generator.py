from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
import datetime
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('btr_utils.pdf_generator')

def generate_btr_report_pdf(report_data):
    """
    Generate a PDF report from the BTR report data
    
    Args:
        report_data: Dictionary containing all report data
    
    Returns:
        bytes: PDF file content
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                          leftMargin=0.5*inch, rightMargin=0.5*inch,
                          topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.black
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=10,
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=6,
        textColor=colors.black
    )
    
    subheading_style = ParagraphStyle(
        'Subheading',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=6,
        textColor=colors.black
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    highlight_style = ParagraphStyle(
        'Highlight',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#4CAF50'),
        spaceAfter=6
    )
    
    category_style_map = {
        'excellent': ParagraphStyle(
            'Excellent',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#1a9850'),
            spaceAfter=6
        ),
        'good': ParagraphStyle(
            'Good',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#91cf60'),
            spaceAfter=6
        ),
        'above_average': ParagraphStyle(
            'AboveAverage',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#d9ef8b'),
            spaceAfter=6
        ),
        'average': ParagraphStyle(
            'Average',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#ffffbf'),
            spaceAfter=6
        ),
        'below_average': ParagraphStyle(
            'BelowAverage',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#fee08b'),
            spaceAfter=6
        ),
        'poor': ParagraphStyle(
            'Poor',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#fc8d59'),
            spaceAfter=6
        ),
        'very_poor': ParagraphStyle(
            'VeryPoor',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#d73027'),
            spaceAfter=6
        )
    }
    
    # Content elements
    elements = []
    
    # Report header
    report_date = datetime.datetime.now().strftime('%b %d, %Y').upper()
    elements.append(Paragraph(f"BTR REPORT GENERATED {report_date}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Property header
    elements.append(Paragraph("The BTR Potential of", title_style))
    
    address = report_data.get('address', 'Unknown Address')
    elements.append(Paragraph(f"{address} is", title_style))
    
    category = report_data.get('btr_score', {}).get('category', 'average')
    category_display = category.replace('_', ' ')
    elements.append(Paragraph(category_display, category_style_map.get(category, category_style_map['average'])))
    elements.append(Spacer(1, 12))
    
    # Property details and value
    property_data = report_data.get('property_data', {})
    
    # Create a table for property specs and estimated value
    specs_data = [
        ["Current Specs", "Estimated Value"],
        [
            f"{property_data.get('bedrooms', 'Unknown')} Bed / {property_data.get('bathrooms', 'Unknown')} Bath\n" +
            f"{property_data.get('sq_ft', 'Unknown')} sqft\n" +
            f"£{property_data.get('price_per_sqft', 0):.0f} per sqft",
            
            f"£{property_data.get('estimated_value', 0):,.0f}"
        ]
    ]
    
    specs_table = Table(specs_data, colWidths=[doc.width/2.0]*2)
    specs_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (1, 0), 12),
        ('BACKGROUND', (0, 1), (1, 1), colors.white),
        ('TEXTCOLOR', (0, 1), (1, 1), colors.black),
        ('ALIGN', (1, 1), (1, 1), 'RIGHT'),
        ('ALIGN', (0, 1), (0, 1), 'LEFT'),
        ('FONTNAME', (0, 1), (1, 1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (1, 1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('LINEBELOW', (0, 0), (1, 0), 1, colors.black),
        ('LINEAFTER', (0, 0), (0, 1), 1, colors.black),
    ]))
    
    elements.append(specs_table)
    elements.append(Spacer(1, 12))
    
    # BTR Score section
    elements.append(Paragraph("BTR SCORE", heading_style))
    
    # Description of the score
    btr_score = report_data.get('btr_score', {})
    overall_score = btr_score.get('overall_score', 50)
    components = btr_score.get('component_scores', {})
    
    score_desc = f"This {property_data.get('sq_ft', '?')} sqft {property_data.get('property_type_name', '?').lower()} property has {category_display} BTR potential. "
    rental_data = report_data.get('rental_data', {})
    
    monthly_rent = rental_data.get('monthly_rent', 0)
    annual_rent = rental_data.get('annual_rent', 0)
    property_value = property_data.get('estimated_value', 1)  # Avoid division by zero
    gross_yield = (annual_rent / property_value) * 100 if property_value else 0
    
    score_desc += f"The estimated value is £{property_value:,.0f} with a potential monthly rental income of £{monthly_rent:,.0f}, "
    score_desc += f"giving a gross yield of {gross_yield:.1f}%."
    
    elements.append(Paragraph(score_desc, normal_style))
    
    # Create a table for component scores
    score_data = [
        ["Component", "Score"],
        ["Rental yield", f"{components.get('yield', 0):.1f}/25"],
        ["Property type", f"{components.get('property_type', 0):.1f}/20"],
        ["Area quality", f"{components.get('area', 0):.1f}/20"],
        ["Growth potential", f"{components.get('growth', 0):.1f}/20"],
        ["Renovation potential", f"{components.get('renovation', 0):.1f}/15"],
        ["OVERALL SCORE", f"{overall_score}/100"]
    ]
    
    score_table = Table(score_data, colWidths=[doc.width*0.7, doc.width*0.3])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (1, 0), 8),
        ('BACKGROUND', (0, 1), (1, -2), colors.white),
        ('BACKGROUND', (0, -1), (1, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 1), (1, -1), colors.black),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (1, -2), 'Helvetica'),
        ('FONTNAME', (0, -1), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('LINEBELOW', (0, 0), (1, 0), 1, colors.black),
        ('LINEBELOW', (0, -2), (1, -2), 1, colors.lightgrey),
    ]))
    
    elements.append(Spacer(1, 6))
    elements.append(score_table)
    elements.append(Spacer(1, 12))
    
    # Investment advice
    elements.append(Paragraph("Investment Advice", subheading_style))
    elements.append(Paragraph(report_data.get('investment_advice', ''), normal_style))
    elements.append(Spacer(1, 6))
    
    # Market commentary
    elements.append(Paragraph("Market Commentary", subheading_style))
    elements.append(Paragraph(report_data.get('market_commentary', ''), normal_style))
    elements.append(Spacer(1, 12))
    
    # Renovation scenarios
    elements.append(Paragraph("RENOVATION SCENARIOS", heading_style))
    elements.append(Paragraph("Explore renovation scenarios that could increase the value of this property:", normal_style))
    elements.append(Spacer(1, 6))
    
    # Add renovation scenarios
    scenarios = report_data.get('renovation_scenarios', [])
    for scenario in scenarios:
        # Scenario header
        elements.append(Paragraph(scenario.get('name', 'Renovation'), subheading_style))
        
        # Scenario details
        scenario_data = [
            [f"Cost: £{scenario.get('cost', 0):,.0f}", f"New Value: £{scenario.get('new_value', 0):,.0f}"],
            [f"Description: {scenario.get('description', '')}", f"Value uplift: £{scenario.get('value_uplift', 0):,.0f} ({scenario.get('value_uplift_pct', 0):.1f}%)"],
            [f"ROI: {scenario.get('roi', 0):.1f}%", ""]
        ]
        
        scenario_table = Table(scenario_data, colWidths=[doc.width/2.0]*2)
        scenario_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 1, colors.lightgrey),
        ]))
        
        elements.append(scenario_table)
        elements.append(Spacer(1, 6))
    
    # Renovation advice
    elements.append(Paragraph("Renovation Advice", subheading_style))
    elements.append(Paragraph(report_data.get('renovation_advice', ''), normal_style))
    elements.append(Spacer(1, 12))
    
    # Rental forecast
    elements.append(Paragraph("RENTAL FORECAST", heading_style))
    elements.append(Spacer(1, 6))
    
    # Create rental forecast table
    forecast_data = [["Year", "Monthly Rent", "Annual Rent", "Growth"]]
    
    # Current year (year 0)
    forecast_data.append([
        "Current",
        f"£{rental_data.get('monthly_rent', 0):,.0f}",
        f"£{rental_data.get('annual_rent', 0):,.0f}",
        "-"
    ])
    
    # Future years
    forecast = report_data.get('rental_forecast', [])
    for forecast_year in forecast:
        forecast_data.append([
            f"Year {forecast_year.get('year', '?')}",
            f"£{forecast_year.get('monthly_rent', 0):,.0f}",
            f"£{forecast_year.get('annual_rent', 0):,.0f}",
            f"{forecast_year.get('growth_rate', 0):.1f}%"
        ])
    
    forecast_table = Table(forecast_data, colWidths=[doc.width/4.0]*4)
    forecast_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ('TOPPADDING', (0, 1), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        ('LINEAFTER', (0, 0), (2, -1), 0.5, colors.lightgrey),
    ]))
    
    elements.append(forecast_table)
    elements.append(Spacer(1, 12))
    
    # Area information
    elements.append(Paragraph("AREA OVERVIEW", heading_style))
    
    area_data = report_data.get('area_data', {})
    
    # Area ratings
    area_ratings = [
        ["Crime Rate:", area_data.get('crime_rate', 'Medium')],
        ["School Rating:", area_data.get('school_rating', 'Good')],
        ["Transport Links:", area_data.get('transport_links', 'Good')]
    ]
    
    area_table = Table(area_ratings, colWidths=[doc.width*0.3, doc.width*0.7])
    area_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(area_table)
    elements.append(Spacer(1, 6))
    
    # Create a table for area amenities
    amenities_data = []
    amenities = area_data.get('amenities', {})
    for category, items in amenities.items():
        if items:
            amenities_data.append([f"{category.title()}:", ", ".join(items[:3])])
    
    if amenities_data:
        amenities_table = Table(amenities_data, colWidths=[doc.width*0.3, doc.width*0.7])
        amenities_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(amenities_table)
        elements.append(Spacer(1, 12))
    
    # Disclaimer
    disclaimer_text = "The accuracy of this BTR report and its applicability to your circumstances are not guaranteed. "
    disclaimer_text += "This report is offered for educational purposes only, and is not a substitute for professional advice. "
    disclaimer_text += "All figures provided are estimates only and may not reflect actual results."
    
    if report_data.get('data_disclaimer'):
        disclaimer_text += " " + report_data.get('data_disclaimer')
    
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