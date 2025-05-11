import pandas as pd
import numpy as np
import os
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('btr_utils.data_processor')

def get_latest_file(directory, prefix):
    """Get the most recent data file with the given prefix"""
    if not os.path.exists(directory):
        logger.warning(f"Directory {directory} does not exist")
        return None
        
    files = [f for f in os.listdir(directory) if f.startswith(prefix) and f.endswith('.csv')]
    if not files:
        logger.warning(f"No files with prefix {prefix} found in {directory}")
        return None
    
    # Sort by date in filename (assuming format prefix_YYYYMMDD.csv)
    latest_file = sorted(files)[-1]
    return os.path.join(directory, latest_file)

def load_land_registry_data():
    """Load the most recent Land Registry data"""
    filename = get_latest_file('data/processed', 'land_registry_')
    if not filename:
        logger.warning("No Land Registry data found. Consider running data collection script.")
        return None
    
    try:
        df = pd.read_csv(filename)
        logger.info(f"Loaded Land Registry data with {len(df)} records")
        return df
    except Exception as e:
        logger.error(f"Error loading Land Registry data: {e}")
        return None

def load_epc_data():
    """Load the most recent EPC ratings data"""
    filename = get_latest_file('data/processed', 'epc_ratings_')
    if not filename:
        logger.warning("No EPC data found. Consider running data collection script.")
        return None
    
    try:
        df = pd.read_csv(filename)
        logger.info(f"Loaded EPC data with {len(df)} records")
        return df
    except Exception as e:
        logger.error(f"Error loading EPC data: {e}")
        return None

def load_amenities_data():
    """Load the most recent OSM amenities data"""
    filename = get_latest_file('data/processed', 'osm_amenities_')
    if not filename:
        logger.warning("No amenities data found. Consider running data collection script.")
        return None
    
    try:
        df = pd.read_csv(filename)
        logger.info(f"Loaded amenities data with {len(df)} records")
        return df
    except Exception as e:
        logger.error(f"Error loading amenities data: {e}")
        return None

def postcode_to_area(postcode):
    """Extract area from a UK postcode"""
    if not isinstance(postcode, str):
        return None
    
    # UK postcodes typically have format: AA9A 9AA or A9A 9AA
    # The first part before the space is the outward code
    postcode = postcode.strip().upper()
    parts = postcode.split(' ')
    if len(parts) > 0:
        return parts[0]
    return None

def find_property_data(address=None, postcode=None):
    """
    Find property data from available datasets using address or postcode
    
    Returns a dictionary with property details
    """
    if not address and not postcode:
        logger.error("Both address and postcode cannot be None")
        return None
    
    # Default property data
    property_data = {
        'estimated_value': None,
        'property_type': None,
        'property_type_name': None,
        'bedrooms': None,
        'bathrooms': None,
        'sq_ft': None,
        'price_history': [],
        'postcode': postcode,
        'address': address
    }
    
    # Extract postcode from address if not provided
    if not postcode and address:
        # Simple regex-based approach - can be improved
        import re
        postcode_pattern = r'([A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2})'
        match = re.search(postcode_pattern, address.upper())
        if match:
            postcode = match.group(0)
            property_data['postcode'] = postcode
    
    # Try to find property in Land Registry data
    land_registry_data = load_land_registry_data()
    
    if land_registry_data is not None and postcode is not None:
        # Filter for this postcode
        properties = land_registry_data[land_registry_data['postcode'] == postcode]
        
        if len(properties) > 0:
            # Use most recent transaction
            latest_property = properties.sort_values('date_of_transfer', ascending=False).iloc[0]
            
            property_data['estimated_value'] = latest_property['price']
            property_data['property_type'] = latest_property['property_type']
            
            # Map property type code to name
            property_type_map = {
                'D': 'Detached',
                'S': 'Semi-detached',
                'T': 'Terraced',
                'F': 'Flat/Maisonette',
                'O': 'Other'
            }
            property_data['property_type_name'] = property_type_map.get(latest_property['property_type'], 'Unknown')
            
            # Add to price history
            for _, row in properties.iterrows():
                property_data['price_history'].append({
                    'date': row['date_of_transfer'],
                    'price': row['price']
                })
    
    # If we still don't have an estimated value, try to infer from similar postcodes
    if property_data['estimated_value'] is None and land_registry_data is not None and postcode is not None:
        postcode_area = postcode_to_area(postcode)
        if postcode_area:
            area_properties = land_registry_data[land_registry_data['postcode'].str.startswith(postcode_area)]
            if len(area_properties) > 0:
                property_data['estimated_value'] = area_properties['price'].median()
                
                # Infer property type if possible
                if property_data['property_type'] is None:
                    most_common_type = area_properties['property_type'].mode()[0]
                    property_data['property_type'] = most_common_type
                    property_data['property_type_name'] = property_type_map.get(most_common_type, 'Unknown')
    
    # Try to get EPC data
    epc_data = load_epc_data()
    if epc_data is not None and postcode is not None:
        # Filter for this postcode
        property_epc = epc_data[epc_data['postcode'] == postcode]
        
        if len(property_epc) > 0:
            # Try to get floor area from EPC
            if 'total_floor_area' in property_epc.columns:
                property_data['sq_ft'] = property_epc['total_floor_area'].mean() * 10.764  # Convert m² to ft²
            
            # Set EPC rating data
            property_data['epc_rating'] = property_epc['current_energy_rating'].iloc[0] if 'current_energy_rating' in property_epc.columns else None
            property_data['epc_efficiency'] = property_epc['current_energy_efficiency'].iloc[0] if 'current_energy_efficiency' in property_epc.columns else None
            property_data['potential_epc_rating'] = property_epc['potential_energy_rating'].iloc[0] if 'potential_energy_rating' in property_epc.columns else None
            property_data['potential_epc_efficiency'] = property_epc['potential_energy_efficiency'].iloc[0] if 'potential_energy_efficiency' in property_epc.columns else None
    
    # Set reasonable defaults for missing data
    if property_data['property_type'] is None:
        if address and ('flat' in address.lower() or 'apartment' in address.lower()):
            property_data['property_type'] = 'F'
            property_data['property_type_name'] = 'Flat/Maisonette'
        else:
            property_data['property_type'] = 'T'  # Default to terraced
            property_data['property_type_name'] = 'Terraced'
    
    if property_data['bedrooms'] is None:
        if property_data['property_type'] == 'F':
            property_data['bedrooms'] = 2
        else:
            property_data['bedrooms'] = 3
    
    if property_data['bathrooms'] is None:
        if property_data['property_type'] == 'F':
            property_data['bathrooms'] = 1
        else:
            property_data['bathrooms'] = 1.5
    
    if property_data['sq_ft'] is None:
        if property_data['property_type'] == 'F':
            property_data['sq_ft'] = 700
        elif property_data['property_type'] == 'T':
            property_data['sq_ft'] = 950
        elif property_data['property_type'] == 'S':
            property_data['sq_ft'] = 1100
        elif property_data['property_type'] == 'D':
            property_data['sq_ft'] = 1400
        else:
            property_data['sq_ft'] = 950
    
    # Calculate price per sq ft
    if property_data['estimated_value'] and property_data['sq_ft']:
        property_data['price_per_sqft'] = property_data['estimated_value'] / property_data['sq_ft']
    else:
        # Use average price per sqft based on property type and location (London vs non-London)
        is_london = postcode and postcode_to_area(postcode) and postcode_to_area(postcode).startswith(("E", "EC", "N", "NW", "SE", "SW", "W", "WC"))
        if property_data['property_type'] == 'F':
            property_data['price_per_sqft'] = 750 if is_london else 350
        elif property_data['property_type'] == 'T':
            property_data['price_per_sqft'] = 800 if is_london else 300
        elif property_data['property_type'] == 'S':
            property_data['price_per_sqft'] = 700 if is_london else 280
        elif property_data['property_type'] == 'D':
            property_data['price_per_sqft'] = 650 if is_london else 250
        else:
            property_data['price_per_sqft'] = 700 if is_london else 300
        
        # Calculate estimated value if not found
        if not property_data['estimated_value']:
            property_data['estimated_value'] = property_data['price_per_sqft'] * property_data['sq_ft']
    
    return property_data

def find_rental_data(postcode=None, property_type=None, bedrooms=None, estimated_value=None):
    """
    Estimate rental data for a property
    
    Returns rental data dictionary
    """
    rental_data = {
        'monthly_rent': None,
        'annual_rent': None,
        'gross_yield': None,
        'growth_rate': 4.0,  # Default annual growth rate
        'rental_demand': 'Medium',
        'void_periods': '2 weeks per year'
    }
    
    # Default rental yields by property type
    yields = {
        'F': 0.045,  # Flat
        'T': 0.042,  # Terraced
        'S': 0.038,  # Semi-detached
        'D': 0.035,  # Detached
        'O': 0.040   # Other
    }
    
    # Adjust yield by location
    if postcode:
        postcode_area = postcode_to_area(postcode)
        is_london = postcode_area and postcode_area.startswith(("E", "EC", "N", "NW", "SE", "SW", "W", "WC"))
        
        # London has lower yields
        if is_london:
            for k in yields:
                yields[k] *= 0.8
    
    # Calculate rental income based on property value and yield
    if estimated_value and property_type:
        gross_yield = yields.get(property_type, 0.04)
        annual_rent = estimated_value * gross_yield
        monthly_rent = annual_rent / 12
        
        # Adjust for bedrooms if provided
        if bedrooms:
            bedrooms_factor = (bedrooms / 2.5)  # Normalize against 2.5 bedrooms
            monthly_rent *= bedrooms_factor
            annual_rent = monthly_rent * 12
            
        rental_data['monthly_rent'] = monthly_rent
        rental_data['annual_rent'] = annual_rent
        rental_data['gross_yield'] = annual_rent / estimated_value
    
    # Determine rental demand based on yield
    if rental_data['gross_yield']:
        if rental_data['gross_yield'] >= 0.05:
            rental_data['rental_demand'] = 'High'
        elif rental_data['gross_yield'] <= 0.03:
            rental_data['rental_demand'] = 'Low'
    
    return rental_data

def find_area_data(postcode=None, lat=None, lon=None):
    """
    Find area data from amenities dataset and other sources
    
    Returns area data dictionary
    """
    area_data = {
        'amenities': {
            'schools': [],
            'transport': [],
            'healthcare': [],
            'shops': [],
            'leisure': []
        },
        'crime_rate': 'Medium',
        'school_rating': 'Good',
        'transport_links': 'Good',
        'area_score': 0,
        'area_metrics': {}
    }
    
    # Get amenities data
    amenities_data = load_amenities_data()
    if amenities_data is not None:
        postcode_area = postcode_to_area(postcode) if postcode else None
        
        # Try to match by location name (city)
        if postcode_area:
            # Get closest match - simplified approach
            for location in amenities_data['location'].unique():
                if postcode_area[:2] in location:
                    area_data['area_metrics'] = amenities_data[amenities_data['location'] == location].iloc[0].to_dict()
                    break
        
        # If no area found, use generic defaults
        if not area_data['area_metrics']:
            # Default amenity scores - medium values
            area_data['area_metrics'] = {
                'total_amenities': 100,
                'food_score': 25,
                'shopping_score': 20,
                'transport_score': 25,
                'healthcare_score': 15,
                'amenity_score': 50
            }
    
    # Set area score from amenity score or default
    area_data['area_score'] = area_data['area_metrics'].get('amenity_score', 50)
    
    # Determine ratings based on area score
    if area_data['area_score'] >= 75:
        area_data['transport_links'] = 'Excellent'
        area_data['school_rating'] = 'Outstanding'
        area_data['crime_rate'] = 'Low'
    elif area_data['area_score'] >= 50:
        area_data['transport_links'] = 'Good'
        area_data['school_rating'] = 'Good'
        area_data['crime_rate'] = 'Medium'
    else:
        area_data['transport_links'] = 'Average'
        area_data['school_rating'] = 'Requires Improvement'
        area_data['crime_rate'] = 'High'
        
    # Add sample amenities based on area metrics
    if area_data['area_metrics'].get('food_score', 0) > 20:
        area_data['amenities']['shops'].append('Supermarket (0.3 miles)')
        area_data['amenities']['shops'].append('Shopping Center (1.2 miles)')
    
    if area_data['area_metrics'].get('transport_score', 0) > 20:
        area_data['amenities']['transport'].append('Bus Stop (0.1 miles)')
        area_data['amenities']['transport'].append('Train Station (0.7 miles)')
    
    if area_data['area_metrics'].get('healthcare_score', 0) > 10:
        area_data['amenities']['healthcare'].append('GP Surgery (0.4 miles)')
        area_data['amenities']['healthcare'].append('Hospital (2.1 miles)')
    
    area_data['amenities']['schools'].append('Primary School (0.3 miles)')
    area_data['amenities']['schools'].append('Secondary School (0.8 miles)')
    area_data['amenities']['leisure'].append('Park (0.2 miles)')
    area_data['amenities']['leisure'].append('Gym (0.5 miles)')
    
    return area_data

def calculate_btr_score(property_data, rental_data, area_data):
    """
    Calculate BTR investment score (0-100)
    
    Returns score dictionary with component scores
    """
    scores = {}
    
    # 1. Rental Yield Score (0-25)
    if property_data['estimated_value'] > 0 and rental_data['annual_rent'] > 0:
        gross_yield = rental_data['annual_rent'] / property_data['estimated_value']
        # Scale yield score: 3% = 5 points, 5% = 15 points, 7%+ = 25 points
        yield_score = min(25, max(0, (gross_yield - 0.03) * 1250))
        scores['yield'] = yield_score
    else:
        scores['yield'] = 10  # Default
    
    # 2. Property Type Score (0-20)
    property_type_scores = {
        'D': 20,  # Detached
        'S': 18,  # Semi-detached
        'T': 15,  # Terraced
        'F': 10,  # Flat/Maisonette
        'O': 5    # Other
    }
    scores['property_type'] = property_type_scores.get(property_data.get('property_type'), 10)
    
    # 3. Area Quality Score (0-20)
    # Based on amenities, school ratings, transport links
    area_score = area_data['area_score'] * 0.2  # Scale 0-100 to 0-20
    scores['area'] = min(20, area_score)
    
    # 4. Growth Potential Score (0-20)
    growth_score = 10  # Default
    
    # Adjust based on recent price history if available
    if property_data['price_history'] and len(property_data['price_history']) > 1:
        # Calculate growth from oldest to newest
        oldest = property_data['price_history'][0]['price']
        newest = property_data['price_history'][-1]['price']
        years_diff = 1  # Assume at least 1 year for simplicity
        annual_growth = (newest / oldest) ** (1 / years_diff) - 1
        
        # Scale: 0% = 0 points, 5% = 10 points, 10%+ = 20 points
        growth_points = min(20, max(0, annual_growth * 200))
        growth_score = (growth_score + growth_points) / 2
    
    scores['growth'] = min(20, growth_score)
    
    # 5. Renovation Potential Score (0-15)
    # Based on EPC ratings and potential improvements
    renovation_score = 7.5  # Default
    
    # Adjust based on EPC improvements if available
    if ('epc_efficiency' in property_data and property_data['epc_efficiency'] is not None and
        'potential_epc_efficiency' in property_data and property_data['potential_epc_efficiency'] is not None):
        improvement = property_data['potential_epc_efficiency'] - property_data['epc_efficiency']
        # Scale improvement: 0 = 0 points, 30+ = 15 points
        renovation_score = min(15, improvement / 2)
    
    # Adjust for property type (houses have more potential than flats)
    if property_data['property_type'] in ['D', 'S', 'T']:
        renovation_score = min(15, renovation_score + 2.5)
    
    scores['renovation'] = min(15, renovation_score)
    
    # Calculate total score
    total_score = sum(scores.values())
    
    # Map to 0-100 scale
    max_possible = 25 + 20 + 20 + 20 + 15  # Sum of all max scores
    normalized_score = int(round(total_score / max_possible * 100))
    
    # Get score category
    if normalized_score >= 80:
        category = "excellent"
    elif normalized_score >= 70:
        category = "good"
    elif normalized_score >= 60:
        category = "above_average"
    elif normalized_score >= 50:
        category = "average"
    elif normalized_score >= 40:
        category = "below_average"
    elif normalized_score >= 30:
        category = "poor"
    else:
        category = "very_poor"
    
    return {
        'overall_score': normalized_score,
        'category': category,
        'component_scores': scores
    }

def calculate_renovation_scenarios(property_data):
    """
    Calculate renovation scenarios and their impact on value
    
    Returns list of scenario dictionaries
    """
    scenarios = []
    
    # Cost benchmarks
    cost_benchmarks = {
        'light_refurb_psf': 75,
        'medium_refurb_psf': 120,
        'conversion_psf': 180,
        'new_build_psf': 225,
        'kitchen': 15000,
        'bathroom': 7500,
        'rewiring': 5000,
        'replumbing': 6000,
        'painting_decorating_psf': 12,
        'flooring_psf': 25,
        'new_boiler': 3500,
    }
    
    # 1. Cosmetic Refurbishment
    cosmetic_cost = property_data['sq_ft'] * cost_benchmarks['painting_decorating_psf'] * 0.75
    cosmetic_value_uplift = property_data['estimated_value'] * 0.10  # 10% value uplift
    cosmetic_new_value = property_data['estimated_value'] + cosmetic_value_uplift
    
    scenarios.append({
        'name': 'Cosmetic Refurbishment',
        'description': 'Painting, decorating, minor works',
        'cost': cosmetic_cost,
        'value_uplift': cosmetic_value_uplift,
        'value_uplift_pct': 10.0,
        'new_value': cosmetic_new_value,
        'roi': (cosmetic_value_uplift / cosmetic_cost - 1) * 100
    })
    
    # 2. Light Refurbishment
    light_cost = property_data['sq_ft'] * cost_benchmarks['light_refurb_psf']
    light_value_uplift = property_data['estimated_value'] * 0.15  # 15% value uplift
    light_new_value = property_data['estimated_value'] + light_value_uplift
    
    scenarios.append({
        'name': 'Light Refurbishment',
        'description': 'New kitchen, bathroom, and cosmetic work',
        'cost': light_cost,
        'value_uplift': light_value_uplift,
        'value_uplift_pct': 15.0,
        'new_value': light_new_value,
        'roi': (light_value_uplift / light_cost - 1) * 100
    })
    
    # 3. Extension (if applicable to property type)
    if property_data['property_type'] in ['D', 'S', 'T']:
        # Assume extension of 20% of current sq ft
        extension_size = property_data['sq_ft'] * 0.2
        extension_cost = extension_size * 200  # £200/sqft extension cost
        extension_value = extension_size * 400  # £400/sqft value add
        extension_value_uplift = extension_value
        extension_new_value = property_data['estimated_value'] + extension_value_uplift
        extension_uplift_pct = (extension_value_uplift / property_data['estimated_value']) * 100
        
        scenarios.append({
            'name': 'Extension',
            'description': f'Add {int(extension_size)} sq ft extension',
            'cost': extension_cost,
            'value_uplift': extension_value_uplift,
            'value_uplift_pct': extension_uplift_pct,
            'new_value': extension_new_value,
            'roi': (extension_value_uplift / extension_cost - 1) * 100
        })
    
    return scenarios

def predict_rental_growth(rental_data, years=5):
    """
    Predict future rental growth 
    
    Returns list of yearly forecasts
    """
    forecast = []
    current_rent = rental_data['monthly_rent']
    annual_rent = rental_data['annual_rent']
    growth_rate = rental_data.get('growth_rate', 4.0) / 100  # Convert percentage to decimal
    
    for year in range(1, years+1):
        forecast.append({
            'year': year,
            'monthly_rent': current_rent * (1 + growth_rate) ** year,
            'annual_rent': annual_rent * (1 + growth_rate) ** year,
            'growth_rate': growth_rate * 100
        })
    
    return forecast