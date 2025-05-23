import os
import pandas as pd
import requests
import json
from datetime import datetime
import logging
import time

# Set up logging
logger = logging.getLogger('btr_data_collection.osm')

def fetch_osm_amenities(locations=None, output_dir='data/raw'):
    """
    Fetch amenity data from OpenStreetMap using Overpass API and process it
    
    Args:
        locations: List of dictionaries with name, lat, lon and radius (meters)
        output_dir: Directory to save the output
    """
    if locations is None:
        # Default to major UK cities with proper coordinates
        locations = [
            {"name": "London-Central", "lat": 51.5074, "lon": -0.1278, "radius": 3000},
            {"name": "Manchester", "lat": 53.4808, "lon": -2.2426, "radius": 2500},
            {"name": "Birmingham", "lat": 52.4862, "lon": -1.8904, "radius": 2500},
            {"name": "Leeds", "lat": 53.8008, "lon": -1.5491, "radius": 2000},
            {"name": "Liverpool", "lat": 53.4084, "lon": -2.9916, "radius": 2000},
            {"name": "Bristol", "lat": 51.4545, "lon": -2.5879, "radius": 2000},
            {"name": "Sheffield", "lat": 53.3811, "lon": -1.4701, "radius": 2000},
            {"name": "Edinburgh", "lat": 55.9533, "lon": -3.1883, "radius": 2000},
            {"name": "Glasgow", "lat": 55.8642, "lon": -4.2518, "radius": 2000},
            {"name": "Cardiff", "lat": 51.4816, "lon": -3.1791, "radius": 2000}
        ]
    
    # Create directories
    os.makedirs(output_dir, exist_ok=True)
    processed_dir = output_dir.replace('raw', 'processed')
    os.makedirs(processed_dir, exist_ok=True)
    
    # Filename with date
    today = datetime.now().strftime('%Y%m%d')
    raw_filename = f"{output_dir}/osm_amenities_{today}.csv"
    processed_filename = f"{processed_dir}/osm_amenities_{today}.csv"
    
    logger.info(f"Fetching amenities for {len(locations)} locations...")
    
    all_amenities = []
    
    # Key amenity types for BTR assessment
    amenity_categories = {
        'transport': ['bus_stop', 'subway_entrance', 'train_station', 'tram_stop'],
        'food': ['restaurant', 'cafe', 'pub', 'bar', 'fast_food'],
        'shopping': ['supermarket', 'convenience', 'mall', 'department_store', 'clothes'],
        'healthcare': ['hospital', 'doctors', 'clinic', 'pharmacy', 'dentist'],
        'education': ['school', 'college', 'university', 'kindergarten'],
        'leisure': ['cinema', 'theatre', 'gym', 'fitness_centre', 'park', 'playground'],
        'services': ['bank', 'atm', 'post_office', 'library'],
        'accommodation': ['hotel', 'guest_house', 'hostel']
    }
    
    for location in locations:
        logger.info(f"Fetching amenities for {location['name']}...")
        
        try:
            # Build comprehensive Overpass query
            query = build_overpass_query(location, amenity_categories)
            
            # Make request to Overpass API
            amenities = query_overpass_api(query)
            
            if amenities:
                # Process and categorize amenities
                processed_amenities = process_location_amenities(
                    amenities, location, amenity_categories
                )
                all_amenities.extend(processed_amenities)
                
                logger.info(f"Collected {len(processed_amenities)} amenities for {location['name']}")
            else:
                logger.warning(f"No amenities found for {location['name']}")
            
            # Rate limiting - be respectful to Overpass API
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error fetching data for {location['name']}: {e}")
            continue
    
    if all_amenities:
        # Create DataFrame
        df = pd.DataFrame(all_amenities)
        
        # Save raw data
        df.to_csv(raw_filename, index=False)
        logger.info(f"Raw amenities data saved to {raw_filename}")
        
        # Process the data for analysis
        processed_df = process_amenities_data(df)
        
        # Save processed data
        processed_df.to_csv(processed_filename, index=False)
        logger.info(f"Processed amenities data saved to {processed_filename}")
        
        return processed_df
    else:
        logger.error("No amenities data collected")
        return None

def build_overpass_query(location, amenity_categories):
    """Build comprehensive Overpass API query"""
    lat, lon, radius = location['lat'], location['lon'], location['radius']
    
    # Start query
    query_parts = ['[out:json][timeout:60];', '(']
    
    # Add node queries for each amenity type
    all_amenity_types = []
    for category, types in amenity_categories.items():
        all_amenity_types.extend(types)
    
    # Query nodes with amenity tags
    for amenity_type in all_amenity_types:
        query_parts.append(
            f'node["amenity"="{amenity_type}"](around:{radius},{lat},{lon});'
        )
    
    # Query leisure facilities
    leisure_types = ['fitness_centre', 'sports_centre', 'park', 'playground', 'pitch']
    for leisure_type in leisure_types:
        query_parts.append(
            f'node["leisure"="{leisure_type}"](around:{radius},{lat},{lon});'
        )
    
    # Query shops
    shop_types = ['supermarket', 'convenience', 'clothes', 'electronics', 'furniture']
    for shop_type in shop_types:
        query_parts.append(
            f'node["shop"="{shop_type}"](around:{radius},{lat},{lon});'
        )
    
    # Query public transport
    public_transport_types = ['station', 'stop_position', 'platform']
    for pt_type in public_transport_types:
        query_parts.append(
            f'node["public_transport"="{pt_type}"](around:{radius},{lat},{lon});'
        )
    
    # Close query
    query_parts.extend([');', 'out body;'])
    
    return ''.join(query_parts)

def query_overpass_api(query):
    """Query the Overpass API"""
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # Try multiple Overpass API servers
    overpass_servers = [
        "http://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.openstreetmap.ru/api/interpreter"
    ]
    
    for server in overpass_servers:
        try:
            logger.debug(f"Trying Overpass server: {server}")
            
            response = requests.post(
                server, 
                data={"data": query},
                timeout=120,
                headers={'User-Agent': 'BTR-Investment-Platform/1.0'}
            )
            
            response.raise_for_status()
            data = response.json()
            
            if 'elements' in data:
                logger.debug(f"Successfully got {len(data['elements'])} elements")
                return data['elements']
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout for server {server}")
            continue
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error with server {server}: {e}")
            continue
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON from server {server}: {e}")
            continue
    
    logger.error("All Overpass servers failed")
    return None

def process_location_amenities(amenities, location, amenity_categories):
    """Process amenities for a specific location"""
    processed_amenities = []
    
    for element in amenities:
        if element['type'] != 'node':
            continue
            
        tags = element.get('tags', {})
        
        # Determine amenity category and type
        amenity_info = categorize_amenity(tags, amenity_categories)
        
        if amenity_info:
            processed_amenity = {
                'location': location['name'],
                'lat': element['lat'],
                'lon': element['lon'],
                'category': amenity_info['category'],
                'type': amenity_info['type'],
                'name': tags.get('name', 'Unknown'),
                'osm_id': element['id'],
                'brand': tags.get('brand', ''),
                'website': tags.get('website', ''),
                'opening_hours': tags.get('opening_hours', ''),
                'phone': tags.get('phone', ''),
                'address': extract_address(tags),
                'collection_date': datetime.now().strftime('%Y%m%d')
            }
            processed_amenities.append(processed_amenity)
    
    return processed_amenities

def categorize_amenity(tags, amenity_categories):
    """Categorize an amenity based on its tags"""
    # Check amenity tag first
    if 'amenity' in tags:
        amenity_type = tags['amenity']
        for category, types in amenity_categories.items():
            if amenity_type in types:
                return {'category': category, 'type': amenity_type}
    
    # Check leisure tag
    if 'leisure' in tags:
        leisure_type = tags['leisure']
        if leisure_type in ['fitness_centre', 'sports_centre']:
            return {'category': 'leisure', 'type': leisure_type}
        elif leisure_type in ['park', 'playground']:
            return {'category': 'leisure', 'type': leisure_type}
    
    # Check shop tag
    if 'shop' in tags:
        shop_type = tags['shop']
        return {'category': 'shopping', 'type': shop_type}
    
    # Check public transport
    if 'public_transport' in tags:
        pt_type = tags['public_transport']
        return {'category': 'transport', 'type': pt_type}
    
    # Check railway
    if 'railway' in tags and tags['railway'] in ['station', 'halt']:
        return {'category': 'transport', 'type': 'train_station'}
    
    return None

def extract_address(tags):
    """Extract address from OSM tags"""
    address_parts = []
    
    address_keys = ['addr:housenumber', 'addr:street', 'addr:city', 'addr:postcode']
    for key in address_keys:
        if key in tags:
            address_parts.append(tags[key])
    
    return ', '.join(address_parts) if address_parts else ''

def process_amenities_data(df):
    """Process raw amenities data into scored format"""
    logger.info("Processing amenities data for BTR analysis...")
    
    # Group by location and calculate scores
    location_scores = []
    
    for location in df['location'].unique():
        location_data = df[df['location'] == location]
        
        # Calculate category scores
        category_counts = location_data['category'].value_counts()
        
        # Base location info
        location_score = {
            'location': location,
            'lat': location_data['lat'].mean(),
            'lon': location_data['lon'].mean(),
            'total_amenities': len(location_data)
        }
        
        # Calculate individual category scores
        categories = ['transport', 'food', 'shopping', 'healthcare', 'education', 'leisure', 'services']
        
        for category in categories:
            count = category_counts.get(category, 0)
            location_score[f'{category}_count'] = count
            
            # Score out of 20 for each category (capped)
            location_score[f'{category}_score'] = min(count * 2, 20)
        
        # Calculate overall amenity score (0-100)
        # Weighted average of category scores
        weights = {
            'transport': 0.25,  # Most important for BTR
            'food': 0.20,
            'shopping': 0.15,
            'healthcare': 0.10,
            'education': 0.10,
            'leisure': 0.10,
            'services': 0.10
        }
        
        overall_score = 0
        for category, weight in weights.items():
            score_key = f'{category}_score'
            if score_key in location_score:
                overall_score += location_score[score_key] * weight
        
        location_score['amenity_score'] = min(int(overall_score), 100)
        
        # Add quality indicators
        location_score['data_quality'] = 'osm_processed'
        location_score['collection_date'] = datetime.now().strftime('%Y%m%d')
        
        location_scores.append(location_score)
    
    # Create processed DataFrame
    processed_df = pd.DataFrame(location_scores)
    
    logger.info(f"Processed amenity scores for {len(processed_df)} locations")
    
    # Log summary statistics
    if len(processed_df) > 0:
        avg_score = processed_df['amenity_score'].mean()
        logger.info(f"Average amenity score: {avg_score:.1f}")
        
        top_location = processed_df.loc[processed_df['amenity_score'].idxmax()]
        logger.info(f"Top location: {top_location['location']} (score: {top_location['amenity_score']})")
    
    return processed_df

def test_overpass_api():
    """Test Overpass API connectivity"""
    logger.info("Testing Overpass API connectivity...")
    
    # Simple test query
    test_query = """
    [out:json][timeout:25];
    (
      node["amenity"="pub"](around:1000,51.5074,-0.1278);
    );
    out body;
    """
    
    try:
        response = requests.post(
            "http://overpass-api.de/api/interpreter",
            data={"data": test_query},
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        
        if 'elements' in data and len(data['elements']) > 0:
            logger.info(f"✅ Overpass API test successful - found {len(data['elements'])} test amenities")
            return True
        else:
            logger.warning("⚠️ Overpass API responded but returned no data")
            return False
            
    except Exception as e:
        logger.error(f"❌ Overpass API test failed: {e}")
        return False

if __name__ == "__main__":
    # Set up console logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    # Test Overpass API first
    if test_overpass_api():
        # Run the main function with a smaller sample for testing
        test_locations = [
            {"name": "London-Test", "lat": 51.5074, "lon": -0.1278, "radius": 1000},
            {"name": "Manchester-Test", "lat": 53.4808, "lon": -2.2426, "radius": 1000}
        ]
        
        result = fetch_osm_amenities(locations=test_locations)
        
        if result is not None:
            print(f"✅ Successfully collected amenity data for {len(result)} locations")
            print(f"Columns: {list(result.columns)}")
            if len(result) > 0:
                print(f"Sample data:\n{result.head()}")
        else:
            print("❌ Failed to collect OSM amenities data")
    else:
        print("❌ Overpass API test failed. Check internet connection.")