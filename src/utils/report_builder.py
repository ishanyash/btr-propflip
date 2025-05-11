import logging
from datetime import datetime
from .data_processor import (
    find_property_data, 
    find_rental_data, 
    find_area_data, 
    calculate_btr_score,
    calculate_renovation_scenarios,
    predict_rental_growth
)
from .llm_client import LLMClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('btr_utils.report_builder')

def generate_investment_advice(property_data, rental_data, btr_score):
    """Generate investment advice based on property data and BTR score"""
    
    score = btr_score.get('overall_score', 50)
    category = btr_score.get('category', 'average')
    property_type = property_data.get('property_type_name', 'property').lower()
    
    if score >= 80:
        return (f"This {property_type} presents an excellent BTR investment opportunity with strong rental yield "
                f"potential of {(rental_data.get('gross_yield', 0) * 100):.1f}%. The high scores across all metrics "
                f"indicate this could be a reliable long-term investment with minimal risk.")
    
    elif score >= 70:
        return (f"This {property_type} offers a good BTR investment opportunity with attractive rental yield "
                f"potential. Consider implementing minor improvements to maximize the return on investment. "
                f"The property's strong location and growth potential make it a solid addition to a BTR portfolio.")
    
    elif score >= 60:
        return (f"This {property_type} presents an above-average BTR opportunity. While not exceptional in "
                f"all areas, the property has promising aspects that could be enhanced through targeted "
                f"improvements. Focus on maximizing the strongest aspects highlighted in the score breakdown.")
    
    elif score >= 50:
        return (f"This {property_type} offers an average BTR investment potential. Consider implementing moderate "
                f"renovations to improve rental yields and capital appreciation potential. Carefully evaluate the "
                f"individual score components to identify areas for improvement.")
    
    elif score >= 40:
        return (f"This {property_type} has below-average BTR potential in its current state. Significant improvements "
                f"would be needed to make this a strong BTR investment. Consider negotiating a lower purchase price "
                f"to improve potential returns or exploring other properties.")
    
    else:
        return (f"This {property_type} may not be an ideal BTR investment in its current state. Consider focusing on "
                f"properties with better scores for rental yield and growth potential, or implementing significant "
                f"improvements before investing.")

def generate_market_commentary(property_data, rental_data, area_data):
    """Generate market commentary based on property location and data"""
    
    postcode = property_data.get('postcode', '').split(' ')[0] if property_data.get('postcode') else 'the area'
    property_type = property_data.get('property_type_name', 'property').lower()
    
    # Determine rental demand description
    rental_demand = rental_data.get('rental_demand', 'Medium')
    demand_desc = "high" if rental_demand == "High" else "moderate" if rental_demand == "Medium" else "modest"
    
    # Determine location quality
    transport_rating = area_data.get('transport_links', 'Average')
    transport_desc = (
        "excellent" if transport_rating == "Excellent" else
        "good" if transport_rating == "Good" else
        "adequate" if transport_rating == "Average" else
        "limited"
    )
    
    # Generate commentary
    commentary = (
        f"{postcode} benefits from {transport_desc} transport links, which is a key driver for rental demand. "
        f"Rental growth in {postcode} is stable at around {rental_data.get('growth_rate', 4.0):.1f}% annually, "
        f"in line with UK averages. Properties in {postcode} have shown {demand_desc} demand from renters, "
        f"particularly for {property_type} properties."
    )
    
    return commentary

def generate_renovation_advice(property_data, renovation_scenarios):
    """Generate renovation advice based on property type and renovation scenarios"""
    
    property_type = property_data.get('property_type_name', 'property').lower()
    
    # Find best scenario by ROI
    best_scenario = None
    for scenario in renovation_scenarios:
        if best_scenario is None or scenario.get('roi', 0) > best_scenario.get('roi', 0):
            best_scenario = scenario
    
    if best_scenario:
        advice = (
            f"A {best_scenario.get('name', '').lower()} focusing on quality finishes in the kitchen and bathroom "
            f"would likely yield the best returns. For this {property_type}, emphasize modern styling to attract "
            f"premium tenants."
        )
    else:
        advice = (
            f"Focus on modern, neutral décor and high-quality fixtures in the kitchen and bathroom to maximize "
            f"rental appeal. Energy efficiency improvements will help attract and retain quality tenants while "
            f"meeting upcoming EPC regulations."
        )
    
    return advice

def build_btr_report(address, postcode=None):
    """
    Build a complete BTR investment report
    
    Args:
        address: Property address
        postcode: Optional postcode (will be extracted from address if not provided)
    
    Returns:
        dict: Complete report data
    """
    logger.info(f"Building BTR report for: {address}")
    
    try:
        # 1. Get property data
        property_data = find_property_data(address, postcode)
        
        if not property_data:
            return {
                'error': 'Property data not found',
                'address': address
            }
        
        # 2. Use LLM to curate property valuation
        llm_client = LLMClient()
        llm_result = llm_client.curate_property_valuation(
            address, 
            property_data.get('estimated_value', 0),
            property_data.get('property_type_name', '')
        )
        
        # Update property value if curated
        if llm_result.get('curated', False):
            property_data['estimated_value'] = llm_result.get('curated_value')
            property_data['value_explanation'] = llm_result.get('explanation', '')
        
        # 3. Calculate price per sqft if estimate changed
        property_data['price_per_sqft'] = property_data['estimated_value'] / property_data['sq_ft']
        
        # 4. Get rental data
        rental_data = find_rental_data(
            postcode=property_data.get('postcode'),
            property_type=property_data.get('property_type'),
            bedrooms=property_data.get('bedrooms'),
            estimated_value=property_data.get('estimated_value')
        )
        
        # 5. Get area data
        area_data = find_area_data(postcode=property_data.get('postcode'))
        
        # 6. Calculate BTR score
        btr_score = calculate_btr_score(property_data, rental_data, area_data)
        
        # 7. Generate renovation scenarios
        renovation_scenarios = calculate_renovation_scenarios(property_data)
        
        # 8. Predict rental growth
        rental_forecast = predict_rental_growth(rental_data)
        
        # 9. Generate advice and commentary
        investment_advice = generate_investment_advice(property_data, rental_data, btr_score)
        market_commentary = generate_market_commentary(property_data, rental_data, area_data)
        renovation_advice = generate_renovation_advice(property_data, renovation_scenarios)
        
        # 10. Build complete report
        report = {
            'address': address,
            'property_data': property_data,
            'rental_data': rental_data,
            'area_data': area_data,
            'btr_score': btr_score,
            'renovation_scenarios': renovation_scenarios,
            'rental_forecast': rental_forecast,
            'investment_advice': investment_advice,
            'market_commentary': market_commentary,
            'renovation_advice': renovation_advice,
            'report_date': datetime.now().strftime('%b %d, %Y').upper(),
            'data_disclaimer': "This report is generated based on available Land Registry, EPC ratings, and OpenStreetMap amenities data only. Rental estimates are based on typical yield calculations from property values, not actual rental statistics. Planning application data is not available, so growth potential is estimated from historical price trends."
        }
        
        logger.info(f"Successfully built BTR report for: {address}")
        return report
        
    except Exception as e:
        logger.error(f"Error building BTR report: {e}", exc_info=True)
        return {
            'error': f"Failed to generate report: {str(e)}",
            'address': address
        }

def build_report_markdown(report_data):
    """
    Convert report data to markdown format for display in Streamlit
    
    Args:
        report_data: Report data dictionary
    
    Returns:
        str: Markdown formatted report
    """
    if 'error' in report_data:
        return f"# Error Generating Report\n\n{report_data.get('error')}"
    
    # Extract data for easier access
    property_data = report_data.get('property_data', {})
    rental_data = report_data.get('rental_data', {})
    area_data = report_data.get('area_data', {})
    btr_score = report_data.get('btr_score', {})
    
    # Build markdown
    md = f"# BTR REPORT GENERATED {report_data.get('report_date', '')}\n\n"
    
    # Property header
    md += f"## The BTR Potential of\n{report_data.get('address', '')} is "
    md += f"{btr_score.get('category', 'average').replace('_', ' ')}.\n\n"
    
    # Data disclaimer
    if report_data.get('data_disclaimer'):
        md += f"**Data Disclaimer:** {report_data.get('data_disclaimer')}\n\n"
    
    # Current specs and value
    md += "### Current Specs | Estimated Value\n"
    md += f"- {property_data.get('bedrooms', '?')} Bed / {property_data.get('bathrooms', '?')} Bath\n"
    md += f"- {property_data.get('sq_ft', '?')} sqft\n"
    md += f"- £{property_data.get('price_per_sqft', 0):.0f} per sqft\n"
    md += f"- £{property_data.get('estimated_value', 0):,.0f}\n\n"
    
    # BTR Score
    md += "### BTR SCORE\n"
    
    # Add score components info
    components = btr_score.get('component_scores', {})
    
    # Check if any components are unavailable/default values
    defaults = []
    if components.get('yield') == 10:
        defaults.append("rental")
    if components.get('growth') == 10:
        defaults.append("growth")
    if components.get('renovation') == 7.5:
        defaults.append("efficiency")
    
    if defaults:
        defaults_str = ", ".join([f"{d} (default)" for d in defaults])
        md += f"Note: Some scores are based on base (default), {defaults_str}.\n"
    
    # Score description
    score_desc = f"This {property_data.get('sq_ft', '?')} sqft {property_data.get('property_type_name', '?').lower()} property has {btr_score.get('category', 'average').replace('_', ' ')} BTR potential. "
    score_desc += f"The estimated value is £{property_data.get('estimated_value', 0):,.0f} with a potential monthly rental income of £{rental_data.get('monthly_rent', 0):,.0f}, "
    score_desc += f"giving a gross yield of {(rental_data.get('gross_yield', 0) * 100):.1f}%."
    
    md += score_desc + "\n\n"
    
    # Investment advice
    md += "### Investment Advice\n"
    md += report_data.get('investment_advice', '') + "\n\n"
    
    # Market commentary
    md += "### Market Commentary\n"
    md += report_data.get('market_commentary', '') + "\n\n"
    
    # Renovation scenarios
    md += "### RENOVATION SCENARIOS\n"
    md += "Explore renovation scenarios that could increase the value of this property:\n\n"
    
    # Add each scenario
    for scenario in report_data.get('renovation_scenarios', []):
        md += f"#### {scenario.get('name', '')}\n"
        md += f"- Cost: £{scenario.get('cost', 0):,.0f}\n"
        md += f"- New Value: £{scenario.get('new_value', 0):,.0f}\n"
        md += f"- Description: {scenario.get('description', '')}\n"
        md += f"- Value uplift: £{scenario.get('value_uplift', 0):,.0f} ({scenario.get('value_uplift_pct', 0):.1f}%)\n"
        md += f"- ROI: {scenario.get('roi', 0):.1f}%\n\n"
    
    # Renovation advice
    md += "### Renovation Advice\n"
    md += report_data.get('renovation_advice', '') + "\n\n"
    
    # Rental forecast
    md += "### RENTAL FORECAST\n"
    
    if report_data.get('data_disclaimer'):
        md += "Note: Rental values are estimated based on property value and UK rental averages.\n"
    
    # Create table header
    md += "| Year | Monthly Rent | Annual Rent | Growth |\n"
    md += "|------|-------------|-------------|--------|\n"
    
    # Current year
    md += f"| Current | £{rental_data.get('monthly_rent', 0):,.0f} | £{rental_data.get('annual_rent', 0):,.0f} | - |\n"
    
    # Future years
    for year in report_data.get('rental_forecast', []):
        md += f"| Year {year.get('year', '?')} | £{year.get('monthly_rent', 0):,.0f} | £{year.get('annual_rent', 0):,.0f} | {year.get('growth_rate', 0):.1f}% |\n"
    
    md += "\n"
    
    # Area overview
    md += "### AREA OVERVIEW\n"
    md += f"- Crime Rate: {area_data.get('crime_rate', 'Medium')}\n"
    md += f"- School Rating: {area_data.get('school_rating', 'Good')}\n"
    md += f"- Transport Links: {area_data.get('transport_links', 'Good')}\n\n"
    
    # Disclaimer
    disclaimer = "The accuracy of this BTR report and its applicability to your circumstances are not guaranteed. "
    disclaimer += "This report is offered for educational purposes only, and is not a substitute for professional advice. "
    disclaimer += "All figures provided are estimates based on available data and may not reflect actual results."
    
    if report_data.get('data_disclaimer'):
        disclaimer += " " + report_data.get('data_disclaimer')
    
    md += disclaimer
    
    return md