import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import sys
import logging
import requests
import json

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.append(project_root)

# Import components
try:
    from src.utils.data_processor import (
        load_land_registry_data, load_ons_rental_data, 
        load_amenities_data, load_epc_data, load_planning_data
    )
    from src.components.location_score_algorithm import calculate_location_score
    from src.components.investment_calculator import BTRInvestmentCalculator
except ImportError as e:
    st.error(f"Import error: {e}")
    st.info("Some advanced features may not be available.")

# Set up logging
logger = logging.getLogger('btr_report_generator')

def display_btr_report_generator():
    """Main BTR Report Generator interface"""
    st.title("🏘️ BTR Investment Report Generator")
    st.write("Generate comprehensive Buy-to-Rent investment analysis reports using real UK data")
    
    # Create tabs for different report types
    tab1, tab2, tab3 = st.tabs(["Location Analysis", "Property Analysis", "Batch Analysis"])
    
    with tab1:
        display_location_analysis()
    
    with tab2:
        display_property_analysis()
    
    with tab3:
        display_batch_analysis()

def display_location_analysis():
    """Location-based BTR analysis"""
    st.header("Location Analysis")
    st.write("Analyze BTR investment potential for specific UK locations")
    
    # Location input
    col1, col2 = st.columns([2, 1])
    
    with col1:
        location_input = st.text_input(
            "Enter UK address or postcode",
            placeholder="e.g., London SW1A 1AA, Birmingham B1 1AA",
            help="Enter a UK postcode, address, or area name"
        )
    
    with col2:
        analysis_type = st.selectbox(
            "Analysis Type",
            ["Quick Analysis", "Detailed Report", "Investment Comparison"]
        )
    
    # Advanced options
    with st.expander("Advanced Options"):
        include_amenities = st.checkbox("Include amenities analysis", value=True)
        include_rental_data = st.checkbox("Include rental market data", value=True)
        include_property_prices = st.checkbox("Include property price analysis", value=True)
        include_planning = st.checkbox("Include planning applications", value=True)
        include_epc = st.checkbox("Include energy efficiency data", value=True)
    
    # Generate report button
    if st.button("Generate Location Report", type="primary"):
        if location_input:
            with st.spinner("Analyzing location..."):
                generate_location_report(
                    location_input, 
                    analysis_type,
                    include_amenities,
                    include_rental_data,
                    include_property_prices,
                    include_planning,
                    include_epc
                )
        else:
            st.error("Please enter a location to analyze")

def display_property_analysis():
    """Individual property BTR analysis"""
    st.header("Property Analysis")
    st.write("Analyze specific properties for BTR investment potential")
    
    # Property details input
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Property Details")
        property_address = st.text_input("Property Address")
        property_price = st.number_input("Purchase Price (£)", min_value=0, value=250000, step=5000)
        property_type = st.selectbox("Property Type", ["House", "Flat", "Other"])
        bedrooms = st.number_input("Number of Bedrooms", min_value=1, max_value=10, value=3)
    
    with col2:
        st.subheader("Investment Parameters")
        investment_strategy = st.selectbox(
            "Investment Strategy",
            ["Buy & Hold", "Light Refurbishment", "Full Renovation", "HMO Conversion"]
        )
        target_yield = st.slider("Target Rental Yield (%)", min_value=3.0, max_value=15.0, value=7.0, step=0.5)
        investment_timeline = st.selectbox("Investment Timeline", ["6 months", "1 year", "2 years", "5+ years"])
    
    # Generate property report
    if st.button("Generate Property Report", type="primary"):
        if property_address and property_price > 0:
            with st.spinner("Analyzing property..."):
                generate_property_report(
                    property_address, property_price, property_type, 
                    bedrooms, investment_strategy, target_yield, investment_timeline
                )
        else:
            st.error("Please enter property details")

def display_batch_analysis():
    """Batch analysis for multiple properties or locations"""
    st.header("Batch Analysis")
    st.write("Analyze multiple locations or properties simultaneously")
    
    # Upload CSV option
    st.subheader("Upload Property List")
    uploaded_file = st.file_uploader(
        "Upload CSV file with property/location data",
        type=['csv'],
        help="CSV should include columns: address, price (optional), property_type (optional)"
    )
    
    if uploaded_file is not None:
        # Process uploaded file
        try:
            df = pd.read_csv(uploaded_file)
            st.write(f"Loaded {len(df)} properties/locations")
            st.dataframe(df.head())
            
            if st.button("Analyze All Properties", type="primary"):
                with st.spinner("Processing batch analysis..."):
                    generate_batch_report(df)
        except Exception as e:
            st.error(f"Error processing file: {e}")
    
    # Manual entry option
    st.subheader("Manual Entry")
    st.write("Enter multiple locations separated by commas:")
    
    manual_locations = st.text_area(
        "Locations",
        placeholder="London SW1A 1AA, Birmingham B1 1AA, Manchester M1 1AA",
        height=100
    )
    
    if manual_locations and st.button("Analyze Manual Locations"):
        locations = [loc.strip() for loc in manual_locations.split(',') if loc.strip()]
        if locations:
            with st.spinner(f"Analyzing {len(locations)} locations..."):
                df_manual = pd.DataFrame({'address': locations})
                generate_batch_report(df_manual)

def generate_location_report(location, analysis_type, include_amenities, include_rental, include_prices, include_planning, include_epc):
    """Generate comprehensive location analysis report"""
    
    # Geocode location first
    location_data = geocode_location(location)
    
    if not location_data:
        st.error("Could not find location. Please check the address/postcode.")
        return
    
    # Display basic location info
    st.success(f"✅ Location found: {location_data.get('formatted_address', location)}")
    
    # Create main results container
    results = {}
    
    # Initialize score components
    score_components = {}
    
    # Load and analyze data sources
    st.subheader("📊 Data Analysis")
    
    # Load available datasets
    datasets = load_all_datasets()
    
    # 1. Amenities Analysis
    if include_amenities and datasets.get('amenities') is not None:
        with st.expander("🏪 Amenities Analysis", expanded=True):
            amenities_score = analyze_amenities(location, location_data, datasets['amenities'])
            score_components['amenities'] = amenities_score
            results['amenities'] = amenities_score
    
    # 2. Rental Market Analysis
    if include_rental and datasets.get('rentals') is not None:
        with st.expander("🏠 Rental Market Analysis", expanded=True):
            rental_score = analyze_rental_market(location, location_data, datasets['rentals'])
            score_components['rental'] = rental_score
            results['rental'] = rental_score
    
    # 3. Property Price Analysis
    if include_prices and datasets.get('land_registry') is not None:
        with st.expander("💰 Property Price Analysis", expanded=True):
            price_score = analyze_property_prices(location, location_data, datasets['land_registry'])
            score_components['property_value'] = price_score
            results['property_prices'] = price_score
    
    # 4. Planning Applications
    if include_planning and datasets.get('planning') is not None:
        with st.expander("🏗️ Planning & Development", expanded=True):
            planning_score = analyze_planning_data(location, location_data, datasets['planning'])
            score_components['growth'] = planning_score
            results['planning'] = planning_score
    
    # 5. Energy Efficiency
    if include_epc and datasets.get('epc') is not None:
        with st.expander("⚡ Energy Efficiency", expanded=True):
            epc_score = analyze_epc_data(location, location_data, datasets['epc'])
            score_components['efficiency'] = epc_score
            results['epc'] = epc_score
    
    # Calculate overall BTR score
    st.subheader("🎯 BTR Investment Score")
    overall_score = calculate_overall_btr_score(score_components)
    
    # Display score with nice visualization
    display_btr_score(overall_score, score_components)
    
    # Investment recommendations
    st.subheader("💡 Investment Recommendations")
    display_investment_recommendations(overall_score, results, location_data)
    
    # Generate PDF report option
    if st.button("📄 Generate PDF Report"):
        generate_pdf_report(location, overall_score, results, location_data)

def geocode_location(location):
    """Geocode location using free services"""
    
    # Import the free geocoding service
    from scripts.free_geocoding_service import geocode_location as free_geocode
    
    try:
        result = free_geocode(location)
        if result:
            return result
        else:
            st.warning(f"Could not geocode location: {location}")
            return None
    except Exception as e:
        st.warning(f"Geocoding error: {e}")
        return None

def extract_postcode_from_result(geocoding_result):
    """Extract postcode from Google Geocoding result"""
    for component in geocoding_result.get('address_components', []):
        if 'postal_code' in component.get('types', []):
            return component['short_name']
    return None

def load_all_datasets():
    """Load all available datasets"""
    datasets = {}
    
    try:
        datasets['amenities'] = load_amenities_data()
    except Exception as e:
        logger.warning(f"Could not load amenities data: {e}")
        datasets['amenities'] = None
    
    try:
        datasets['rentals'] = load_ons_rental_data()
    except Exception as e:
        logger.warning(f"Could not load rental data: {e}")
        datasets['rentals'] = None
    
    try:
        datasets['land_registry'] = load_land_registry_data()
    except Exception as e:
        logger.warning(f"Could not load land registry data: {e}")
        datasets['land_registry'] = None
    
    try:
        datasets['planning'] = load_planning_data()
    except Exception as e:
        logger.warning(f"Could not load planning data: {e}")
        datasets['planning'] = None
    
    try:
        datasets['epc'] = load_epc_data()
    except Exception as e:
        logger.warning(f"Could not load EPC data: {e}")
        datasets['epc'] = None
    
    return datasets

def analyze_amenities(location, location_data, amenities_df):
    """Analyze amenities for the location"""
    
    if amenities_df is None or len(amenities_df) == 0:
        st.info("No amenities data available")
        return 50  # Default score
    
    # Find nearby amenities based on location name or coordinates
    relevant_amenities = None
    
    # Try to match by location name first
    if 'location' in amenities_df.columns:
        location_matches = amenities_df[
            amenities_df['location'].str.contains(location, case=False, na=False)
        ]
        
        if len(location_matches) > 0:
            relevant_amenities = location_matches
        else:
            # Try partial matches
            postcode = location_data.get('postcode', '')
            if postcode:
                postcode_matches = amenities_df[
                    amenities_df['location'].str.contains(postcode, case=False, na=False)
                ]
                if len(postcode_matches) > 0:
                    relevant_amenities = postcode_matches
    
    if relevant_amenities is None or len(relevant_amenities) == 0:
        st.warning("No specific amenities data found for this location")
        # Return a default analysis
        st.write("**Amenities Analysis (Estimated)**")
        st.write("- Transport: Good connectivity expected for major UK location")
        st.write("- Shopping: Standard retail amenities available")
        st.write("- Healthcare: NHS services accessible")
        st.write("- Education: Local schools and colleges present")
        return 65  # Default good score
    
    # Analyze amenities
    st.write(f"**Found {len(relevant_amenities)} amenities in the area**")
    
    # Category breakdown
    if 'category' in relevant_amenities.columns:
        category_counts = relevant_amenities['category'].value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Amenity Categories:**")
            for category, count in category_counts.items():
                st.write(f"• {category.title()}: {count}")
        
        with col2:
            # Create pie chart
            fig = px.pie(
                values=category_counts.values,
                names=category_counts.index,
                title="Amenities by Category"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Calculate amenity score
    score = 50  # Base score
    
    # Add points for each category
    category_scores = {
        'transport': 15,
        'food': 10,
        'shopping': 10,
        'healthcare': 10,
        'education': 8,
        'leisure': 7
    }
    
    if 'category' in relevant_amenities.columns:
        for category in relevant_amenities['category'].unique():
            if category in category_scores:
                count = len(relevant_amenities[relevant_amenities['category'] == category])
                # Score based on count (more amenities = better, but with diminishing returns)
                category_score = min(count * 2, category_scores[category])
                score += category_score
    
    # Cap at 100
    score = min(score, 100)
    
    st.metric("Amenities Score", f"{score}/100")
    
    return score

def analyze_rental_market(location, location_data, rentals_df):
    """Analyze rental market for the location"""
    
    if rentals_df is None or len(rentals_df) == 0:
        st.info("No rental market data available")
        return 50
    
    st.write("**Rental Market Analysis**")
    
    # Try to find relevant rental data
    relevant_rentals = None
    postcode = location_data.get('postcode', '')
    
    if 'region' in rentals_df.columns:
        # Try exact matches first
        for region in rentals_df['region'].unique():
            if (location.lower() in str(region).lower() or 
                str(region).lower() in location.lower() or
                (postcode and postcode.lower() in str(region).lower())):
                relevant_rentals = rentals_df[rentals_df['region'] == region]
                break
    
    if relevant_rentals is None or len(relevant_rentals) == 0:
        st.warning("No specific rental data found for this location")
        st.write("**Estimated Rental Market Metrics:**")
        st.write("- Average rent levels: Market rate expected")
        st.write("- Rental demand: Stable for UK location")
        st.write("- Growth trend: Following national average")
        return 60  # Default score
    
    # Analyze rental data
    st.write(f"**Rental data found for region: {relevant_rentals['region'].iloc[0]}**")
    
    # Calculate metrics
    if 'value' in relevant_rentals.columns:
        avg_rent = relevant_rentals['value'].mean()
        st.metric("Average Monthly Rent", f"£{avg_rent:,.0f}")
        
        # Compare to national average
        national_avg = rentals_df['value'].mean()
        ratio = avg_rent / national_avg
        
        if ratio > 1:
            st.write(f"📈 {((ratio - 1) * 100):.1f}% above national average")
        else:
            st.write(f"📉 {((1 - ratio) * 100):.1f}% below national average")
    
    # Growth analysis
    if 'yoy_growth' in relevant_rentals.columns:
        avg_growth = relevant_rentals['yoy_growth'].mean()
        if not pd.isna(avg_growth):
            st.metric("Annual Growth Rate", f"{avg_growth:.1f}%")
    
    # Calculate rental score
    score = 50  # Base score
    
    if 'value' in relevant_rentals.columns:
        # Higher rents generally better for BTR (within reason)
        national_avg = rentals_df['value'].mean()
        avg_rent = relevant_rentals['value'].mean()
        ratio = avg_rent / national_avg
        
        if 0.8 <= ratio <= 1.5:  # Sweet spot
            score += 20
        elif 0.6 <= ratio < 0.8:  # Below average
            score += 10
        elif ratio > 1.5:  # Too expensive
            score += 5
    
    if 'yoy_growth' in relevant_rentals.columns:
        avg_growth = relevant_rentals['yoy_growth'].mean()
        if not pd.isna(avg_growth) and avg_growth > 0:
            # Positive growth adds to score
            score += min(avg_growth * 2, 30)  # Cap at 30 points
    
    score = min(score, 100)
    st.metric("Rental Market Score", f"{score}/100")
    
    return score

def analyze_property_prices(location, location_data, land_registry_df):
    """Analyze property prices for the location"""
    
    if land_registry_df is None or len(land_registry_df) == 0:
        st.info("No property price data available")
        return 50
    
    st.write("**Property Price Analysis**")
    
    # Extract postcode area for filtering
    postcode = location_data.get('postcode', '')
    postcode_area = postcode.split(' ')[0] if postcode and ' ' in postcode else postcode
    
    # Filter properties
    relevant_properties = None
    
    if 'postcode' in land_registry_df.columns and postcode_area:
        relevant_properties = land_registry_df[
            land_registry_df['postcode'].str.startswith(postcode_area, na=False)
        ]
    
    if relevant_properties is None or len(relevant_properties) == 0:
        # Try broader search
        if 'town_city' in land_registry_df.columns:
            relevant_properties = land_registry_df[
                land_registry_df['town_city'].str.contains(location, case=False, na=False)
            ]
    
    if relevant_properties is None or len(relevant_properties) == 0:
        st.warning("No specific property price data found for this location")
        st.write("**Estimated Property Market:**")
        st.write("- Price levels: Market rate for area")
        st.write("- Property types: Mixed housing available")
        st.write("- Market activity: Normal transaction volumes")
        return 55
    
    # Analyze property data
    st.write(f"**Found {len(relevant_properties)} property transactions**")
    
    # Price statistics
    if 'price' in relevant_properties.columns:
        avg_price = relevant_properties['price'].mean()
        median_price = relevant_properties['price'].median()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Average Price", f"£{avg_price:,.0f}")
        with col2:
            st.metric("Median Price", f"£{median_price:,.0f}")
        
        # Price distribution
        fig = px.histogram(
            relevant_properties, 
            x='price', 
            nbins=20,
            title="Property Price Distribution",
            labels={'price': 'Price (£)', 'count': 'Number of Properties'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Property types
    if 'property_type' in relevant_properties.columns:
        type_counts = relevant_properties['property_type'].value_counts()
        
        # Map property codes to names
        type_names = {
            'D': 'Detached', 'S': 'Semi-detached', 'T': 'Terraced', 
            'F': 'Flat/Maisonette', 'O': 'Other'
        }
        
        type_display = {type_names.get(k, k): v for k, v in type_counts.items()}
        
        fig = px.pie(
            values=list(type_display.values()),
            names=list(type_display.keys()),
            title="Property Types"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Calculate property score
    score = 50  # Base score
    
    if 'price' in relevant_properties.columns:
        # Compare to national average
        national_avg = land_registry_df['price'].mean()
        avg_price = relevant_properties['price'].mean()
        ratio = avg_price / national_avg
        
        # Score based on price ratio (moderate prices better for BTR)
        if 0.7 <= ratio <= 1.3:  # Reasonable price range
            score += 25
        elif 0.5 <= ratio < 0.7:  # Below average (good value)
            score += 30
        elif 1.3 < ratio <= 2.0:  # Above average (still workable)
            score += 15
        else:  # Too expensive or too cheap
            score += 5
    
    # Property type diversity bonus
    if 'property_type' in relevant_properties.columns:
        unique_types = relevant_properties['property_type'].nunique()
        score += min(unique_types * 5, 20)  # Max 20 points for diversity
    
    score = min(score, 100)
    st.metric("Property Price Score", f"{score}/100")
    
    return score

def analyze_planning_data(location, location_data, planning_df):
    """Analyze planning applications for the location"""
    
    if planning_df is None or len(planning_df) == 0:
        st.info("No planning data available")
        return 50
    
    st.write("**Planning & Development Analysis**")
    
    # Filter planning applications
    postcode = location_data.get('postcode', '')
    relevant_planning = None
    
    if 'address' in planning_df.columns:
        # Try postcode match
        if postcode:
            relevant_planning = planning_df[
                planning_df['address'].str.contains(postcode, case=False, na=False)
            ]
        
        # If no postcode match, try location name
        if relevant_planning is None or len(relevant_planning) == 0:
            relevant_planning = planning_df[
                planning_df['address'].str.contains(location, case=False, na=False)
            ]
    
    if relevant_planning is None or len(relevant_planning) == 0:
        st.warning("No specific planning data found for this location")
        st.write("**Development Activity (Estimated):**")
        st.write("- Planning applications: Normal activity levels")
        st.write("- Development pipeline: Standard for area")
        st.write("- Growth potential: Moderate")
        return 55
    
    # Analyze planning data
    st.write(f"**Found {len(relevant_planning)} planning applications**")
    
    # Application status breakdown
    if 'status' in relevant_planning.columns:
        status_counts = relevant_planning['status'].value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Application Status:**")
            for status, count in status_counts.items():
                st.write(f"• {status}: {count}")
        
        with col2:
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Planning Application Status"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Residential vs commercial
    if 'is_residential' in relevant_planning.columns:
        residential_count = relevant_planning['is_residential'].sum()
        total_count = len(relevant_planning)
        residential_pct = (residential_count / total_count) * 100
        
        st.write(f"**{residential_pct:.1f}% of applications are residential**")
    
    # Calculate planning score
    score = 50  # Base score
    
    # More applications generally indicate growth
    app_count = len(relevant_planning)
    if app_count > 50:
        score += 20
    elif app_count > 20:
        score += 15
    elif app_count > 10:
        score += 10
    else:
        score += 5
    
    # Approval rate matters
    if 'status' in relevant_planning.columns:
        approved = relevant_planning['status'].str.contains('Approved', case=False, na=False).sum()
        total = len(relevant_planning)
        approval_rate = approved / total if total > 0 else 0
        
        score += min(approval_rate * 30, 25)  # Max 25 points for approval rate
    
    # Residential development bonus
    if 'is_residential' in relevant_planning.columns:
        residential_pct = relevant_planning['is_residential'].mean()
        score += min(residential_pct * 15, 15)  # Max 15 points
    
    score = min(score, 100)
    st.metric("Planning & Development Score", f"{score}/100")
    
    return score

def analyze_epc_data(location, location_data, epc_df):
    """Analyze EPC data for the location"""
    
    if epc_df is None or len(epc_df) == 0:
        st.info("No EPC data available")
        return 50
    
    st.write("**Energy Efficiency Analysis**")
    
    # Filter EPC data
    postcode = location_data.get('postcode', '')
    postcode_area = postcode.split(' ')[0] if postcode and ' ' in postcode else postcode
    
    relevant_epc = None
    
    if 'postcode' in epc_df.columns and postcode_area:
        relevant_epc = epc_df[
            epc_df['postcode'].str.startswith(postcode_area, na=False)
        ]
    
    if relevant_epc is None or len(relevant_epc) == 0:
        st.warning("No specific EPC data found for this location")
        st.write("**Energy Efficiency (Estimated):**")
        st.write("- Property efficiency: Average for UK housing stock")
        st.write("- Improvement potential: Standard renovation opportunities")
        st.write("- Investment impact: Moderate energy upgrade benefits")
        return 60
    
    # Analyze EPC data
    st.write(f"**Found {len(relevant_epc)} EPC certificates**")
    
    # Current energy ratings
    if 'current_energy_rating' in relevant_epc.columns:
        rating_counts = relevant_epc['current_energy_rating'].value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Energy Ratings:**")
            for rating, count in rating_counts.items():
                st.write(f"• Rating {rating}: {count}")
        
        with col2:
            # Create bar chart with color coding
            colors = ['green', 'lightgreen', 'yellow', 'orange', 'darkorange', 'red', 'darkred']
            rating_order = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
            
            fig = go.Figure(data=[
                go.Bar(
                    x=[rating for rating in rating_order if rating in rating_counts.index],
                    y=[rating_counts.get(rating, 0) for rating in rating_order if rating in rating_counts.index],
                    marker_color=[colors[rating_order.index(rating)] for rating in rating_order if rating in rating_counts.index]
                )
            ])
            fig.update_layout(title="EPC Rating Distribution", xaxis_title="Rating", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)
    
    # Efficiency improvement potential
    if 'efficiency_improvement' in relevant_epc.columns:
        avg_improvement = relevant_epc['efficiency_improvement'].mean()
        if not pd.isna(avg_improvement):
            st.metric("Average Improvement Potential", f"{avg_improvement:.1f} points")
    
    # Calculate EPC score
    score = 50  # Base score
    
    if 'current_energy_rating' in relevant_epc.columns:
        # Score based on current ratings (better ratings = higher score)
        rating_scores = {'A': 25, 'B': 20, 'C': 15, 'D': 10, 'E': 5, 'F': 2, 'G': 0}
        
        total_rating_score = 0
        total_properties = 0
        
        for rating, count in relevant_epc['current_energy_rating'].value_counts().items():
            if rating in rating_scores:
                total_rating_score += rating_scores[rating] * count
                total_properties += count
        
        if total_properties > 0:
            avg_rating_score = total_rating_score / total_properties
            score += avg_rating_score
    
    # Improvement potential bonus
    if 'efficiency_improvement' in relevant_epc.columns:
        avg_improvement = relevant_epc['efficiency_improvement'].mean()
        if not pd.isna(avg_improvement) and avg_improvement > 0:
            # Higher improvement potential = better investment opportunity
            improvement_score = min(avg_improvement / 2, 25)  # Max 25 points
            score += improvement_score
    
    score = min(score, 100)
    st.metric("Energy Efficiency Score", f"{score}/100")
    
    return score

def calculate_overall_btr_score(score_components):
    """Calculate overall BTR score from components"""
    
    # Default weights
    weights = {
        'amenities': 0.20,
        'rental': 0.25,
        'property_value': 0.20,
        'growth': 0.20,
        'efficiency': 0.15
    }
    
    # Calculate weighted score
    total_score = 0
    total_weight = 0
    
    for component, score in score_components.items():
        if component in weights and score is not None:
            total_score += score * weights[component]
            total_weight += weights[component]
    
    # Add base score if no components available
    if total_weight == 0:
        return 50
    
    # Normalize to account for missing components
    final_score = total_score / total_weight
    
    return min(max(int(final_score), 0), 100)

def display_btr_score(overall_score, score_components):
    """Display BTR score with visualization"""
    
    # Score color coding
    if overall_score >= 80:
        color = "green"
        category = "Excellent"
    elif overall_score >= 70:
        color = "lightgreen"
        category = "Good"
    elif overall_score >= 60:
        color = "yellow"
        category = "Above Average"
    elif overall_score >= 50:
        color = "orange"
        category = "Average"
    else:
        color = "red"
        category = "Below Average"
    
    # Display main score
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; border: 3px solid {color}; border-radius: 10px; background-color: {color}20;">
            <h1 style="margin: 0; color: {color};">{overall_score}/100</h1>
            <h3 style="margin: 0;">{category}</h3>
            <p style="margin: 5px 0;">BTR Investment Score</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("")  # Spacing
    
    # Component scores breakdown
    if score_components:
        st.write("**Score Breakdown:**")
        
        # Create radar chart
        categories = []
        scores = []
        
        for component, score in score_components.items():
            if score is not None:
                categories.append(component.replace('_', ' ').title())
                scores.append(score)
        
        if categories:
            fig = go.Figure()
            
            fig.add_trace(go.Scatterpolar(
                r=scores,
                theta=categories,
                fill='toself',
                name='BTR Score Components'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )),
                showlegend=False,
                title="BTR Score Components"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Score table
        score_df = pd.DataFrame([
            {
                'Component': component.replace('_', ' ').title(),
                'Score': f"{score}/100" if score is not None else "N/A",
                'Rating': get_score_rating(score) if score is not None else "N/A"
            }
            for component, score in score_components.items()
        ])
        
        st.dataframe(score_df, use_container_width=True)

def get_score_rating(score):
    """Get rating category for a score"""
    if score >= 80:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 60:
        return "Above Average"
    elif score >= 50:
        return "Average"
    else:
        return "Below Average"

def display_investment_recommendations(overall_score, results, location_data):
    """Display investment recommendations based on analysis"""
    
    recommendations = []
    
    # Score-based recommendations
    if overall_score >= 80:
        recommendations.append("🟢 **Strong BTR opportunity** - This location shows excellent potential for buy-to-rent investment.")
        recommendations.append("💰 Consider acquiring multiple properties in this area")
        recommendations.append("📈 Expect strong rental demand and capital appreciation")
    elif overall_score >= 70:
        recommendations.append("🟡 **Good BTR opportunity** - This location has solid fundamentals for rental investment.")
        recommendations.append("🔍 Conduct detailed due diligence on specific properties")
        recommendations.append("💡 Look for value-add opportunities through renovation")
    elif overall_score >= 60:
        recommendations.append("🟠 **Moderate opportunity** - Some positive factors but also areas of concern.")
        recommendations.append("⚠️ Exercise caution and seek below-market pricing")
        recommendations.append("🏠 Focus on properties with unique advantages")
    else:
        recommendations.append("🔴 **High risk** - Multiple factors suggest challenging BTR conditions.")
        recommendations.append("❌ Consider alternative locations unless you have specific local knowledge")
        recommendations.append("🔄 Re-evaluate in 6-12 months for market changes")
    
    # Component-specific recommendations
    if 'amenities' in results and results['amenities'] < 60:
        recommendations.append("🏪 Low amenities score - Consider impact on tenant appeal")
    
    if 'rental' in results and results['rental'] > 75:
        recommendations.append("🏠 Strong rental market - Good tenant demand expected")
    
    if 'property_prices' in results and results['property_prices'] < 50:
        recommendations.append("💰 Challenging price levels - Negotiate aggressively")
    
    if 'planning' in results and results['planning'] > 70:
        recommendations.append("🏗️ Active development pipeline - Future growth potential")
    
    if 'epc' in results and results['epc'] < 60:
        recommendations.append("⚡ Energy efficiency concerns - Factor renovation costs")
    
    # Display recommendations
    st.write("**Key Recommendations:**")
    for rec in recommendations:
        st.write(rec)
    
    # Investment strategy suggestions
    st.write("**Suggested Investment Strategies:**")
    
    if overall_score >= 75:
        st.write("• **Buy & Hold**: Acquire and rent immediately")
        st.write("• **Portfolio Building**: Consider multiple acquisitions")
        st.write("• **Premium Positioning**: Target higher-end rental market")
    elif overall_score >= 60:
        st.write("• **Value Add**: Light refurbishment before renting")
        st.write("• **Selective Acquisition**: Choose properties carefully")
        st.write("• **Market Timing**: Consider seasonal factors")
    else:
        st.write("• **Deep Value**: Only if significantly below market price")
        st.write("• **Alternative Uses**: Consider other property strategies")
        st.write("• **Wait & Watch**: Monitor market developments")

def generate_property_report(address, price, prop_type, bedrooms, strategy, target_yield, timeline):
    """Generate property-specific BTR analysis"""
    
    st.success(f"✅ Analyzing property: {address}")
    
    # Initialize calculator
    try:
        calculator = BTRInvestmentCalculator()
        
        # Property info
        property_info = {
            'purchase_price': price,
            'square_feet': estimate_square_feet(prop_type, bedrooms),
            'property_type': prop_type.lower(),
            'rooms': bedrooms,
            'is_leasehold': prop_type.lower() == 'flat'
        }
        
        # Investment analysis
        st.subheader("💰 Investment Analysis")
        
        # Map strategy to scenario
        scenario_map = {
            'Buy & Hold': 'cosmetic_refurb',
            'Light Refurbishment': 'light_refurb',
            'Full Renovation': 'full_refurb',
            'HMO Conversion': 'full_refurb'  # Approximate
        }
        
        scenario = scenario_map.get(strategy, 'light_refurb')
        
        # Run calculations
        purchase_costs = calculator.calculate_purchase_costs(price)
        refurb_costs = calculator.calculate_refurb_costs(property_info, scenario)
        gdv_result = calculator.calculate_gdv(property_info, refurb_costs)
        
        # Display key metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Purchase Price", f"£{price:,.0f}")
            st.metric("Refurb Cost", f"£{refurb_costs['total_refurb_cost']:,.0f}")
        
        with col2:
            st.metric("Total Investment", f"£{purchase_costs['total_purchase_costs'] + refurb_costs['total_refurb_cost']:,.0f}")
            st.metric("GDV", f"£{gdv_result['gdv']:,.0f}")
        
        # Rental analysis
        rental_result = calculator.calculate_rental_income(property_info, gdv_result)
        
        with col3:
            st.metric("Monthly Rent", f"£{rental_result['monthly_rent']:,.0f}")
            st.metric("Net Yield", f"{rental_result['net_yield']*100:.2f}%")
        
        # Yield comparison
        actual_yield = rental_result['net_yield'] * 100
        yield_status = "✅ Target Met" if actual_yield >= target_yield else "❌ Below Target"
        
        st.write(f"**Yield Analysis**: {yield_status}")
        st.write(f"Target: {target_yield}% | Projected: {actual_yield:.2f}%")
        
        # Investment timeline
        st.subheader("📅 Investment Timeline")
        
        timeline_map = {
            '6 months': 6,
            '1 year': 12,
            '2 years': 24,
            '5+ years': 60
        }
        
        months = timeline_map.get(timeline, 12)
        
        # Calculate returns over timeline
        annual_rent = rental_result['net_annual_rent']
        total_investment = purchase_costs['total_purchase_costs'] + refurb_costs['total_refurb_cost']
        
        timeline_return = (annual_rent * (months / 12)) / total_investment * 100
        
        st.write(f"**Projected return over {timeline}**: {timeline_return:.1f}%")
        
        # Risk factors
        st.subheader("⚠️ Risk Assessment")
        
        risks = []
        
        if actual_yield < target_yield:
            risks.append("Rental yield below target")
        
        if refurb_costs['total_refurb_cost'] > price * 0.3:
            risks.append("High refurbishment costs relative to purchase price")
        
        if property_info['is_leasehold']:
            risks.append("Leasehold property - additional ongoing costs")
        
        if months < 12:
            risks.append("Short investment timeline increases risk")
        
        if risks:
            for risk in risks:
                st.write(f"• {risk}")
        else:
            st.write("✅ No major risk factors identified")
    
    except Exception as e:
        st.error(f"Error in property analysis: {e}")
        st.info("Showing simplified analysis")
        
        # Simplified analysis
        estimated_rent = price * 0.005  # 0.5% of value per month
        gross_yield = (estimated_rent * 12) / price * 100
        
        st.write(f"**Estimated monthly rent**: £{estimated_rent:,.0f}")
        st.write(f"**Estimated gross yield**: {gross_yield:.2f}%")

def estimate_square_feet(prop_type, bedrooms):
    """Estimate property square footage"""
    base_sizes = {
        'flat': 600,
        'house': 900,
        'other': 750
    }
    
    base = base_sizes.get(prop_type.lower(), 750)
    return base + (bedrooms - 2) * 150  # Adjust for bedroom count

def generate_batch_report(df):
    """Generate batch analysis for multiple properties/locations"""
    
    st.success(f"Processing {len(df)} locations...")
    
    results = []
    progress_bar = st.progress(0)
    
    for i, row in df.iterrows():
        # Update progress
        progress = (i + 1) / len(df)
        progress_bar.progress(progress)
        
        # Get location
        location = row.get('address', row.get('location', ''))
        if not location:
            continue
        
        # Quick analysis for each location
        try:
            location_data = geocode_location(location)
            if location_data:
                # Simplified scoring
                base_score = 50
                
                # Add location-based adjustments
                major_cities = ['london', 'birmingham', 'manchester', 'leeds', 'liverpool']
                for city in major_cities:
                    if city in location.lower():
                        base_score += 20
                        break
                
                results.append({
                    'Location': location,
                    'BTR Score': base_score,
                    'Category': get_score_rating(base_score),
                    'Coordinates': f"{location_data['lat']:.4f}, {location_data['lng']:.4f}"
                })
        except Exception as e:
            st.warning(f"Could not analyze {location}: {e}")
    
    progress_bar.empty()
    
    if results:
        # Display results table
        st.subheader("📊 Batch Analysis Results")
        
        results_df = pd.DataFrame(results)
        st.dataframe(results_df, use_container_width=True)
        
        # Summary statistics
        st.subheader("📈 Summary Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_score = results_df['BTR Score'].mean()
            st.metric("Average Score", f"{avg_score:.1f}")
        
        with col2:
            top_score = results_df['BTR Score'].max()
            st.metric("Highest Score", f"{top_score}")
        
        with col3:
            excellent_count = len(results_df[results_df['BTR Score'] >= 80])
            st.metric("Excellent Locations", f"{excellent_count}")
        
        # Score distribution
        fig = px.histogram(
            results_df, 
            x='BTR Score', 
            nbins=10,
            title="BTR Score Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Top recommendations
        top_locations = results_df.nlargest(5, 'BTR Score')
        
        st.subheader("🏆 Top 5 Recommended Locations")
        st.dataframe(top_locations, use_container_width=True)
        
        # Download results
        csv = results_df.to_csv(index=False)
        st.download_button(
            "📥 Download Results CSV",
            csv,
            file_name=f"btr_batch_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.error("No valid results generated from batch analysis")

def generate_pdf_report(location, overall_score, results, location_data):
    """Generate PDF report (placeholder for now)"""
    
    st.info("📄 PDF Report Generation")
    st.write("PDF report functionality will be implemented in the next update.")
    
    # For now, show what would be included
    st.write("**Report would include:**")
    st.write("• Executive summary with BTR score")
    st.write("• Detailed component analysis")
    st.write("• Investment recommendations")
    st.write("• Risk assessment")
    st.write("• Market comparisons")
    st.write("• Charts and visualizations")
    
    # Generate text summary that could be saved
    report_text = f"""
BTR INVESTMENT ANALYSIS REPORT
Location: {location}
Analysis Date: {datetime.now().strftime('%B %d, %Y')}

EXECUTIVE SUMMARY
Overall BTR Score: {overall_score}/100
Investment Category: {get_score_rating(overall_score)}

COMPONENT ANALYSIS
"""
    
    for component, score in results.items():
        if isinstance(score, (int, float)):
            report_text += f"{component.title()}: {score}/100\n"
    
    report_text += f"""

COORDINATES
Latitude: {location_data.get('lat', 'N/A')}
Longitude: {location_data.get('lng', 'N/A')}

Generated by BTR Investment Platform
"""
    
    # Allow download of text report
    st.download_button(
        "📥 Download Text Report",
        report_text,
        file_name=f"btr_report_{location.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain"
    )