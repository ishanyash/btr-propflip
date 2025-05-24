import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import sys
import logging
import json
import requests
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def display_btr_report_generator():
    """Main BTR Report Generator interface"""
    st.title("🏘️ BTR Investment Report Generator")
    st.write("Generate comprehensive Buy-to-Rent investment analysis reports for UK properties using AI-powered property analysis")
    
    # Input section - simplified
    st.header("Property Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        address_input = st.text_input(
            "Property Address",
            placeholder="Enter full UK address (e.g., '10 Downing Street, London SW1A 2AA')",
            help="Enter the complete property address for analysis"
        )
        
        investment_strategy = st.selectbox(
            "Investment Strategy",
            ["Buy and Hold", "Light Refurbishment", "Heavy Refurbishment", "HMO Conversion", "Flip"],
            help="Select your intended investment strategy"
        )
    
    with col2:
        st.info("""
        **What we'll analyze:**
        • Property details from AI analysis
        • Local rental market rates
        • Investment potential scoring
        • Renovation scenarios
        • Market commentary
        """)
    
    # Generate report button
    if st.button("Generate Professional BTR Report", type="primary"):
        if address_input.strip():
            generate_comprehensive_btr_report(address_input, investment_strategy)
        else:
            st.error("Please enter a property address")

def generate_comprehensive_btr_report(address, strategy):
    """Generate comprehensive BTR report with AI analysis"""
    
    with st.spinner("🔍 Analyzing property with AI... This may take 30-60 seconds"):
        try:
            # Step 1: Get property details from OpenAI
            property_details = get_property_details_from_ai(address)
            
            if not property_details:
                st.error("Could not analyze this property. Please check the address and try again.")
                return
            
            # Step 2: Get rental market data
            rental_data = get_rental_market_data(property_details)
            
            # Step 3: Calculate investment metrics
            investment_analysis = calculate_investment_metrics(property_details, rental_data, strategy)
            
            # Step 4: Generate BTR score
            btr_score = calculate_btr_score(property_details, rental_data, investment_analysis)
            
            # Step 5: Display results
            display_comprehensive_results(property_details, rental_data, investment_analysis, btr_score, strategy)
            
            # Step 6: Offer PDF download
            offer_pdf_download(property_details, rental_data, investment_analysis, btr_score, strategy)
            
        except Exception as e:
            st.error(f"Error generating report: {str(e)}")
            logger.error(f"Report generation error: {e}")

def get_property_details_from_ai(address):
    """Use OpenAI to get property details from address"""
    
    try:
        from openai import OpenAI
        
        api_key = os.environ.get('OPENAI_API_KEY')
        
        if not api_key:
            st.warning("OpenAI API key not found. Using mock data for demonstration.")
            return get_mock_property_details(address)
        
        client = OpenAI(api_key=api_key)
        
        prompt = f"""
        Analyze this UK property address and provide detailed information in JSON format: "{address}"
        
        Please provide:
        {{
            "address": "Full formatted address",
            "postcode": "UK postcode",
            "property_type": "House/Flat/Bungalow/Maisonette",
            "bedrooms": number,
            "bathrooms": number,
            "reception_rooms": number,
            "square_feet": estimated_square_feet,
            "estimated_value": estimated_current_market_value_in_GBP,
            "year_built": estimated_year_built_or_null,
            "location_quality": "Excellent/Good/Average/Poor",
            "transport_links": "Description of transport links",
            "local_amenities": "Description of local amenities",
            "area_description": "Brief description of the area",
            "investment_notes": "Key investment considerations for this property"
        }}
        
        Provide realistic UK property estimates. For property values, use current UK market rates per square foot for the area.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a UK property expert. Provide accurate, realistic property analysis in valid JSON format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        # Parse JSON response
        content = response.choices[0].message.content
        
        # Clean up the response to ensure valid JSON
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        
        property_data = json.loads(content)
        
        # Validate required fields
        required_fields = ['address', 'property_type', 'bedrooms', 'square_feet', 'estimated_value']
        for field in required_fields:
            if field not in property_data:
                raise ValueError(f"Missing required field: {field}")
        
        return property_data
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        st.warning("Using estimated property data due to API limitations")
        return get_mock_property_details(address)

def get_mock_property_details(address):
    """Generate realistic mock property details when API unavailable"""
    
    # Determine property type and size based on address characteristics
    address_lower = address.lower()
    
    if any(word in address_lower for word in ['flat', 'apartment', 'maisonette']):
        property_type = "Flat"
        bedrooms = np.random.choice([1, 2, 3], p=[0.3, 0.5, 0.2])
        square_feet = np.random.randint(450, 900)
    elif any(word in address_lower for word in ['house', 'road', 'street', 'avenue']):
        property_type = "House"
        bedrooms = np.random.choice([2, 3, 4, 5], p=[0.2, 0.4, 0.3, 0.1])
        square_feet = np.random.randint(800, 2000)
    else:
        property_type = "House"
        bedrooms = 3
        square_feet = 1200
    
    # Estimate value based on location
    london_areas = ['london', 'sw1', 'sw2', 'nw1', 'se1', 'e1', 'w1', 'ec1']
    major_cities = ['manchester', 'birmingham', 'leeds', 'liverpool', 'bristol', 'sheffield']
    
    if any(area in address_lower for area in london_areas):
        price_per_sqft = np.random.randint(600, 1200)
        location_quality = "Excellent"
    elif any(city in address_lower for city in major_cities):
        price_per_sqft = np.random.randint(200, 400)
        location_quality = "Good"
    else:
        price_per_sqft = np.random.randint(150, 300)
        location_quality = "Average"
    
    estimated_value = int(square_feet * price_per_sqft)
    
    return {
        "address": address,
        "postcode": extract_postcode(address),
        "property_type": property_type,
        "bedrooms": bedrooms,
        "bathrooms": max(1, bedrooms - 1),
        "reception_rooms": max(1, bedrooms - 1),
        "square_feet": square_feet,
        "estimated_value": estimated_value,
        "year_built": np.random.randint(1950, 2020),
        "location_quality": location_quality,
        "transport_links": "Good transport connections" if location_quality == "Excellent" else "Adequate transport links",
        "local_amenities": "Excellent local amenities including shops, restaurants, and services",
        "area_description": f"Well-established residential area with {location_quality.lower()} investment potential",
        "investment_notes": f"Suitable for {property_type.lower()} BTR investment with good rental demand"
    }

def extract_postcode(address):
    """Extract postcode from address"""
    import re
    # UK postcode pattern
    postcode_pattern = r'[A-Z]{1,2}[0-9][A-Z0-9]?\s?[0-9][A-Z]{2}'
    match = re.search(postcode_pattern, address.upper())
    return match.group(0) if match else "Unknown"

def get_rental_market_data(property_details):
    """Get rental market data based on property details"""
    
    # Base rental rates per bedroom per month (realistic UK rates)
    base_rates = {
        "London": {"1": 1800, "2": 2400, "3": 3200, "4": 4200, "5": 5500},
        "Manchester": {"1": 800, "2": 1100, "3": 1400, "4": 1800, "5": 2200},
        "Birmingham": {"1": 700, "2": 950, "3": 1250, "4": 1600, "5": 2000},
        "Other": {"1": 600, "2": 800, "3": 1100, "4": 1400, "5": 1800}
    }
    
    address_lower = property_details['address'].lower()
    
    # Determine market
    if any(area in address_lower for area in ['london', 'sw1', 'sw2', 'nw1', 'se1', 'e1', 'w1', 'ec1']):
        market = "London"
    elif 'manchester' in address_lower:
        market = "Manchester"
    elif 'birmingham' in address_lower:
        market = "Birmingham"
    else:
        market = "Other"
    
    bedrooms = str(min(property_details['bedrooms'], 5))
    base_rent = base_rates[market][bedrooms]
    
    # Adjust for property type
    if property_details['property_type'] == 'House':
        monthly_rent = base_rent * 1.1  # Houses command premium
    else:
        monthly_rent = base_rent * 0.95  # Flats slightly lower
    
    # Adjust for location quality
    quality_multipliers = {"Excellent": 1.2, "Good": 1.05, "Average": 1.0, "Poor": 0.85}
    monthly_rent *= quality_multipliers.get(property_details['location_quality'], 1.0)
    
    return {
        "monthly_rent": int(monthly_rent),
        "annual_rent": int(monthly_rent * 12),
        "market": market,
        "rental_growth_rate": 0.045,  # 4.5% annual growth
        "yield_benchmark": 0.055,  # 5.5% benchmark yield
        "demand_level": "Strong" if market in ["London", "Manchester"] else "Moderate"
    }

def calculate_investment_metrics(property_details, rental_data, strategy):
    """Calculate comprehensive investment metrics"""
    
    purchase_price = property_details['estimated_value']
    annual_rent = rental_data['annual_rent']
    
    # Calculate gross yield
    gross_yield = (annual_rent / purchase_price) * 100
    
    # Calculate expenses (realistic UK BTR expenses)
    expenses = {
        "management": annual_rent * 0.10,  # 10% management fee
        "maintenance": annual_rent * 0.08,  # 8% maintenance
        "insurance": purchase_price * 0.002,  # 0.2% of property value
        "void_periods": annual_rent * 0.04,  # 4% for void periods
        "letting_fees": annual_rent * 0.03,  # 3% letting fees
        "accountancy": 500,  # Annual accountancy
        "landlord_license": 100 if property_details['property_type'] == 'House' else 0
    }
    
    total_expenses = sum(expenses.values())
    net_annual_income = annual_rent - total_expenses
    net_yield = (net_annual_income / purchase_price) * 100
    
    # Calculate financing (typical BTR mortgage)
    loan_to_value = 0.75  # 75% LTV typical for BTR
    loan_amount = purchase_price * loan_to_value
    deposit = purchase_price - loan_amount
    
    # Mortgage calculation (5% interest, 25 years)
    interest_rate = 0.05
    mortgage_years = 25
    monthly_rate = interest_rate / 12
    num_payments = mortgage_years * 12
    
    monthly_mortgage = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    annual_mortgage = monthly_mortgage * 12
    
    # Cash flow calculation
    net_cash_flow = net_annual_income - annual_mortgage
    
    # Purchase costs
    stamp_duty = calculate_stamp_duty(purchase_price, is_btr=True)
    other_costs = purchase_price * 0.03  # Legal, survey, etc.
    total_purchase_costs = stamp_duty + other_costs
    
    # Total cash required
    total_cash_required = deposit + total_purchase_costs
    
    # Cash-on-cash return
    cash_on_cash = (net_cash_flow / total_cash_required) * 100 if total_cash_required > 0 else 0
    
    return {
        "purchase_price": purchase_price,
        "gross_yield": gross_yield,
        "net_yield": net_yield,
        "annual_rent": annual_rent,
        "monthly_rent": rental_data['monthly_rent'],
        "total_expenses": total_expenses,
        "expense_breakdown": expenses,
        "net_annual_income": net_annual_income,
        "loan_amount": loan_amount,
        "deposit": deposit,
        "monthly_mortgage": monthly_mortgage,
        "annual_mortgage": annual_mortgage,
        "net_cash_flow": net_cash_flow,
        "stamp_duty": stamp_duty,
        "other_costs": other_costs,
        "total_cash_required": total_cash_required,
        "cash_on_cash": cash_on_cash
    }

def calculate_stamp_duty(purchase_price, is_btr=True):
    """Calculate UK stamp duty including BTR surcharge"""
    
    # Standard rates
    bands = [(125000, 0.02), (250000, 0.05), (925000, 0.10), (1500000, 0.12)]
    
    stamp_duty = 0
    remaining = purchase_price
    previous_threshold = 0
    
    for threshold, rate in bands:
        if remaining <= 0:
            break
        
        taxable = min(remaining, threshold - previous_threshold)
        stamp_duty += taxable * rate
        remaining -= taxable
        previous_threshold = threshold
    
    # Any amount above highest threshold
    if remaining > 0:
        stamp_duty += remaining * 0.12
    
    # Add 3% surcharge for BTR/second homes
    if is_btr:
        stamp_duty += purchase_price * 0.03
    
    return int(stamp_duty)

def calculate_btr_score(property_details, rental_data, investment_analysis):
    """Calculate comprehensive BTR score out of 100"""
    
    score_components = {}
    
    # Yield scoring (30 points)
    gross_yield = investment_analysis['gross_yield']
    if gross_yield >= 8:
        yield_score = 30
    elif gross_yield >= 6:
        yield_score = 25
    elif gross_yield >= 4:
        yield_score = 15
    else:
        yield_score = 5
    
    score_components['yield'] = yield_score
    
    # Cash flow scoring (25 points)
    cash_on_cash = investment_analysis['cash_on_cash']
    if cash_on_cash >= 10:
        cash_flow_score = 25
    elif cash_on_cash >= 5:
        cash_flow_score = 20
    elif cash_on_cash >= 0:
        cash_flow_score = 10
    else:
        cash_flow_score = 0
    
    score_components['cash_flow'] = cash_flow_score
    
    # Location scoring (20 points)
    location_quality = property_details['location_quality']
    location_scores = {"Excellent": 20, "Good": 15, "Average": 10, "Poor": 5}
    location_score = location_scores.get(location_quality, 10)
    
    score_components['location'] = location_score
    
    # Market demand scoring (15 points)
    demand_level = rental_data['demand_level']
    demand_scores = {"Strong": 15, "Moderate": 10, "Weak": 5}
    demand_score = demand_scores.get(demand_level, 10)
    
    score_components['demand'] = demand_score
    
    # Property type scoring (10 points)
    property_type = property_details['property_type']
    if property_type == 'House':
        property_score = 10
    elif property_type == 'Flat':
        property_score = 8
    else:
        property_score = 6
    
    score_components['property_type'] = property_score
    
    total_score = sum(score_components.values())
    
    # Determine rating
    if total_score >= 80:
        rating = "Excellent"
    elif total_score >= 65:
        rating = "Good"
    elif total_score >= 50:
        rating = "Average"
    elif total_score >= 35:
        rating = "Below Average"
    else:
        rating = "Poor"
    
    return {
        "total_score": total_score,
        "rating": rating,
        "components": score_components
    }

def display_comprehensive_results(property_details, rental_data, investment_analysis, btr_score, strategy):
    """Display comprehensive analysis results"""
    
    st.success("✅ BTR Investment Report Generated Successfully!")
    
    # Header with property info
    st.header(f"📍 {property_details['address']}")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "BTR Score", 
            f"{btr_score['total_score']}/100",
            delta=btr_score['rating']
        )
    
    with col2:
        st.metric(
            "Gross Yield", 
            f"{investment_analysis['gross_yield']:.1f}%"
        )
    
    with col3:
        st.metric(
            "Monthly Rent", 
            f"£{investment_analysis['monthly_rent']:,}"
        )
    
    with col4:
        st.metric(
            "Cash on Cash", 
            f"{investment_analysis['cash_on_cash']:.1f}%"
        )
    
    # Property Summary
    st.subheader("🏠 Property Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Property Details:**")
        st.write(f"• Type: {property_details['property_type']}")
        st.write(f"• Bedrooms: {property_details['bedrooms']}")
        st.write(f"• Size: {property_details['square_feet']:,} sq ft")
        st.write(f"• Estimated Value: £{property_details['estimated_value']:,}")
        st.write(f"• Price per sq ft: £{property_details['estimated_value']/property_details['square_feet']:.0f}")
    
    with col2:
        st.write("**Investment Metrics:**")
        st.write(f"• Monthly Rent: £{investment_analysis['monthly_rent']:,}")
        st.write(f"• Annual Rent: £{investment_analysis['annual_rent']:,}")
        st.write(f"• Gross Yield: {investment_analysis['gross_yield']:.1f}%")
        st.write(f"• Net Yield: {investment_analysis['net_yield']:.1f}%")
        st.write(f"• Cash Required: £{investment_analysis['total_cash_required']:,}")
    
    # Investment Analysis Chart
    st.subheader("📊 Financial Breakdown")
    
    # Create income vs expenses chart
    categories = ['Annual Rent', 'Operating Expenses', 'Mortgage Payments', 'Net Cash Flow']
    values = [
        investment_analysis['annual_rent'],
        investment_analysis['total_expenses'],
        investment_analysis['annual_mortgage'],
        investment_analysis['net_cash_flow']
    ]
    colors = ['green', 'red', 'orange', 'blue']
    
    fig = go.Figure(data=[go.Bar(x=categories, y=values, marker_color=colors)])
    fig.update_layout(
        title="Annual Cash Flow Analysis",
        yaxis_title="Amount (£)",
        showlegend=False,
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed Analysis
    with st.expander("💰 Detailed Financial Analysis"):
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Purchase Costs:**")
            st.write(f"• Property Price: £{investment_analysis['purchase_price']:,}")
            st.write(f"• Stamp Duty: £{investment_analysis['stamp_duty']:,}")
            st.write(f"• Legal/Survey: £{investment_analysis['other_costs']:,}")
            st.write(f"• Deposit (25%): £{investment_analysis['deposit']:,}")
            st.write(f"**Total Cash Required: £{investment_analysis['total_cash_required']:,}**")
        
        with col2:
            st.write("**Annual Expenses:**")
            for expense, amount in investment_analysis['expense_breakdown'].items():
                st.write(f"• {expense.replace('_', ' ').title()}: £{amount:,}")
            st.write(f"**Total Expenses: £{investment_analysis['total_expenses']:,}**")
    
    # Location Analysis
    st.subheader("📍 Location Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Location Quality:** {property_details['location_quality']}")
        st.write(f"**Transport Links:** {property_details['transport_links']}")
        st.write(f"**Area Description:** {property_details['area_description']}")
    
    with col2:
        st.write(f"**Rental Market:** {rental_data['market']}")
        st.write(f"**Demand Level:** {rental_data['demand_level']}")
        st.write(f"**Growth Rate:** {rental_data['rental_growth_rate']*100:.1f}% annually")

def offer_pdf_download(property_details, rental_data, investment_analysis, btr_score, strategy):
    """Generate and offer PDF download"""
    
    st.subheader("📄 Download Report")
    
    if st.button("Generate PDF Report"):
        with st.spinner("Generating PDF report..."):
            try:
                pdf_buffer = generate_pdf_report(property_details, rental_data, investment_analysis, btr_score, strategy)
                
                st.download_button(
                    label="Download BTR Investment Report (PDF)",
                    data=pdf_buffer.getvalue(),
                    file_name=f"BTR_Report_{property_details['postcode'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )
                
                st.success("✅ PDF report generated successfully!")
                
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")

def generate_pdf_report(property_details, rental_data, investment_analysis, btr_score, strategy):
    """Generate comprehensive PDF report"""
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.darkgreen
    )
    
    # Title
    story.append(Paragraph("BTR INVESTMENT ANALYSIS REPORT", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Property Summary
    story.append(Paragraph("PROPERTY SUMMARY", heading_style))
    
    property_data = [
        ["Address", property_details['address']],
        ["Property Type", f"{property_details['property_type']} ({property_details['bedrooms']} bed, {property_details['bathrooms']} bath)"],
        ["Size", f"{property_details['square_feet']:,} sq ft"],
        ["Estimated Value", f"£{property_details['estimated_value']:,}"],
        ["Price per sq ft", f"£{property_details['estimated_value']/property_details['square_feet']:.0f}"]
    ]
    
    property_table = Table(property_data, colWidths=[2*inch, 4*inch])
    property_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(property_table)
    story.append(Spacer(1, 20))
    
    # BTR Score
    story.append(Paragraph("BTR INVESTMENT SCORE", heading_style))
    
    score_text = f"""
    <b>Overall Score: {btr_score['total_score']}/100 ({btr_score['rating']})</b><br/>
    <br/>
    This property has <b>{btr_score['rating'].lower()}</b> BTR investment potential based on comprehensive analysis 
    of yield, cash flow, location quality, and market demand factors.
    """
    
    story.append(Paragraph(score_text, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Investment Metrics
    story.append(Paragraph("INVESTMENT ANALYSIS", heading_style))
    
    metrics_data = [
        ["Metric", "Value"],
        ["Monthly Rent", f"£{investment_analysis['monthly_rent']:,}"],
        ["Annual Rent", f"£{investment_analysis['annual_rent']:,}"],
        ["Gross Yield", f"{investment_analysis['gross_yield']:.1f}%"],
        ["Net Yield", f"{investment_analysis['net_yield']:.1f}%"],
        ["Cash on Cash Return", f"{investment_analysis['cash_on_cash']:.1f}%"],
        ["Total Cash Required", f"£{investment_analysis['total_cash_required']:,}"],
        ["Annual Cash Flow", f"£{investment_analysis['net_cash_flow']:,}"]
    ]
    
    metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(metrics_table)
    story.append(Spacer(1, 20))
    
    # Investment Advice
    story.append(Paragraph("INVESTMENT ADVICE", heading_style))
    
    if btr_score['total_score'] >= 65:
        advice = "This property shows strong BTR investment potential with good yields and positive cash flow characteristics."
    elif btr_score['total_score'] >= 50:
        advice = "This property has moderate BTR potential. Consider negotiating on price or exploring value-add opportunities."
    else:
        advice = "This property may not be suitable for BTR investment in its current state. Consider alternative strategies or properties."
    
    story.append(Paragraph(advice, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Disclaimer
    story.append(Paragraph("DISCLAIMER", heading_style))
    disclaimer_text = """
    This report is generated for educational purposes based on available data and estimates. 
    Property values, rental rates, and investment returns are estimates and may not reflect actual market conditions. 
    Always conduct thorough due diligence and seek professional advice before making investment decisions. 
    All figures are estimates based on current market data and may vary significantly.
    """
    
    story.append(Paragraph(disclaimer_text, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer