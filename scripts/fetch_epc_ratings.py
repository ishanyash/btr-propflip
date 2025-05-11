import os
import pandas as pd
import requests
import zipfile
from io import BytesIO
from datetime import datetime
import logging
import base64
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('data_collection.epc')

# Explicitly load the .env file
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

def fetch_epc_ratings(output_dir='data/raw', sample_size=None):
    """
    Fetch EPC (Energy Performance Certificate) data from the UK government
    
    Args:
        output_dir: Directory to save the output
        sample_size: Optional limit on number of records to process
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    processed_dir = output_dir.replace('raw', 'processed')
    os.makedirs(processed_dir, exist_ok=True)
    sample_dir = os.path.join(project_root, 'data', 'sample')
    os.makedirs(sample_dir, exist_ok=True)
    
    # Filename with date
    today = datetime.now().strftime('%Y%m%d')
    filename = f"{output_dir}/epc_ratings_{today}.csv"
    processed_filename = f"{processed_dir}/epc_ratings_{today}.csv"
    
    logger.info("Fetching EPC ratings data...")
    
    try:
        # Get API credentials directly
        api_email = os.getenv('EPC_API_EMAIL')
        api_key = os.getenv('EPC_API_KEY')
        
        # Debug: Print masked credentials
        if api_email:
            masked_email = api_email[:4] + '...' + api_email[-4:] if len(api_email) > 8 else "***"
            logger.info(f"Found API email: {masked_email}")
        else:
            logger.warning("API email not found in environment variables")
            
        if api_key:
            masked_key = api_key[:4] + '...' + api_key[-4:] if len(api_key) > 8 else "***"
            logger.info(f"Found API key: {masked_key}")
        else:
            logger.warning("API key not found in environment variables")
        
        # First, try direct access to the info endpoint (no auth required)
        logger.info("Testing API connection with info endpoint...")
        info_url = "https://epc.opendatacommunities.org/api/v1/info"
        headers = {"Accept": "application/json"}
        
        try:
            response = requests.get(info_url, headers=headers, timeout=15)
            if response.status_code == 200:
                info_data = response.json()
                logger.info(f"API connection successful. Latest data: {info_data.get('latestDate', 'unknown')}")
            else:
                logger.warning(f"Info endpoint returned status {response.status_code}: {response.text}")
        except Exception as e:
            logger.warning(f"Could not connect to info endpoint: {e}")
        
        # Now try to access the domestic search API with authentication
        if api_email and api_key:
            logger.info("Attempting EPC domestic search API access...")
            url = "https://epc.opendatacommunities.org/api/v1/domestic/search"
            
            # Try Swagger-style authentication
            # Headers based on the documentation
            headers = {
                "Accept": "application/json"
            }
            
            # Add HTTP Basic Auth as request auth parameter
            auth = (api_email, api_key)
            
            # Parameters for the search
            params = {
                "size": min(sample_size, 100) if sample_size else 100,
                "from": 0,
                "postcode": "SW1"  # Westminster sample
            }
            
            try:
                logger.info(f"Sending request to {url} with Swagger-style auth")
                response = requests.get(url, auth=auth, headers=headers, params=params, timeout=30)
                
                # Log response details for debugging
                logger.info(f"API Response: Status {response.status_code}")
                
                # Check for specific error codes
                if response.status_code == 401:
                    logger.error("Authentication failed. Please check your API credentials.")
                    logger.error(f"Response text: {response.text[:200]}...")
                elif response.status_code != 200:
                    logger.error(f"API request failed with status {response.status_code}: {response.text[:200]}...")
                else:
                    data = response.json()
                    rows = data.get('rows', [])
                    
                    if rows:
                        df = pd.DataFrame(rows)
                        df.to_csv(filename, index=False)
                        logger.info(f"Successfully retrieved {len(df)} EPC records")
                        
                        # Process the data and return
                        return process_epc_data(df, processed_filename)
                    else:
                        logger.warning("API returned empty data set")
            
            except Exception as api_error:
                logger.error(f"Error accessing EPC API: {api_error}")
        else:
            logger.warning("Missing API credentials. Cannot access EPC data API.")
        
        # If API access failed, try to download directly
        logger.info("Attempting direct download of public EPC sample data...")
        
        # Try to download from the EPC open data communities sample (might not be available)
        sample_url = "https://epc.opendatacommunities.org/api/v1/display/search?size=100&from=0"
        
        try:
            response = requests.get(sample_url, timeout=15)
            if response.status_code == 200:
                # Try to parse the response
                data = response.json()
                if 'rows' in data and data['rows']:
                    df = pd.DataFrame(data['rows'])
                    df.to_csv(filename, index=False)
                    logger.info(f"Successfully retrieved {len(df)} EPC records from public sample")
                    return process_epc_data(df, processed_filename)
                else:
                    logger.warning("Public sample returned empty data")
            else:
                logger.warning(f"Public sample request failed: {response.status_code}")
        except Exception as e:
            logger.warning(f"Could not download public sample: {e}")
        
        # Check for existing sample file
        sample_file = os.path.join(sample_dir, 'epc_sample.csv')
        if os.path.exists(sample_file):
            logger.info(f"Using existing sample file: {sample_file}")
            df = pd.read_csv(sample_file)
        else:
            # Create synthetic data as last resort
            logger.warning("Creating synthetic EPC dataset as last resort")
            df = create_synthetic_epc_data(sample_size)
            
            # Save as sample for future use
            df.to_csv(sample_file, index=False)
            logger.info(f"Saved synthetic data as sample for future use: {sample_file}")
        
        # Save to output file
        df.to_csv(filename, index=False)
        logger.info(f"Saved {len(df)} records to {filename}")
        
        # Process the data
        return process_epc_data(df, processed_filename)
            
    except Exception as e:
        logger.error(f"Error fetching EPC data: {e}")
        return None

def create_synthetic_epc_data(sample_size=None):
    """Create synthetic EPC data for testing"""
    logger.info("Generating synthetic EPC data")
    
    postcodes = ["SW1A 1AA", "M1 1AA", "B1 1AA", "G1 1AA", "EH1 1AA", 
                "CF1 1AA", "LS1 1AA", "NE1 1AA", "BS1 1AA", "BT1 1AA"]
    
    ratings = ["A", "B", "C", "D", "E", "F", "G"]
    efficiencies = [92, 85, 75, 65, 55, 40, 25]
    
    # Create sample data
    data = []
    num_records = min(sample_size, 1000) if sample_size else 1000
    
    for i in range(num_records):
        postcode_idx = i % len(postcodes)
        rating_idx = i % len(ratings)
        
        data.append({
            'postcode': postcodes[postcode_idx],
            'current_energy_rating': ratings[rating_idx],
            'current_energy_efficiency': efficiencies[rating_idx],
            'potential_energy_rating': ratings[max(0, rating_idx-2)],
            'potential_energy_efficiency': efficiencies[max(0, rating_idx-2)],
            'property_type': ['Flat', 'House', 'Bungalow', 'Maisonette'][i % 4],
            'built_form': ['Detached', 'Semi-Detached', 'Terraced', 'End-Terrace'][i % 4],
            'construction_age_band': ['Pre 1900', '1900-1929', '1930-1949', '1950-1966', 
                                     '1967-1975', '1976-1982', '1983-1990', '1991-1995', 
                                     '1996-2002', '2003-2006', '2007-2011', '2012 onwards'][i % 12],
            'total_floor_area': [45, 60, 75, 90, 120, 150, 200, 250][i % 8]
        })
    
    return pd.DataFrame(data)

def process_epc_data(df, output_filename):
    """Process EPC data into standardized format"""
    logger.info("Processing EPC data...")
    
    try:
        # Common variations of column names in different EPC datasets
        column_mappings = {
            # API format
            'current-energy-rating': 'current_energy_rating',
            'potential-energy-rating': 'potential_energy_rating',
            'current-energy-efficiency': 'current_energy_efficiency',
            'potential-energy-efficiency': 'potential_energy_efficiency',
            'property-type': 'property_type',
            'built-form': 'built_form',
            'construction-age-band': 'construction_age_band',
            'total-floor-area': 'total_floor_area',
            
            # Variations from government data
            'CURRENT_ENERGY_RATING': 'current_energy_rating',
            'POTENTIAL_ENERGY_RATING': 'potential_energy_rating',
            'CURRENT_ENERGY_EFFICIENCY': 'current_energy_efficiency',
            'POTENTIAL_ENERGY_EFFICIENCY': 'potential_energy_efficiency',
            'PROPERTY_TYPE': 'property_type',
            'BUILT_FORM': 'built_form',
            'CONSTRUCTION_AGE_BAND': 'construction_age_band',
            'TOTAL_FLOOR_AREA': 'total_floor_area',
            
            'ENERGY_RATING_CURRENT': 'current_energy_rating',
            'ENERGY_RATING_POTENTIAL': 'potential_energy_rating',
            'ENERGY_EFFICIENCY_CURRENT': 'current_energy_efficiency',
            'ENERGY_EFFICIENCY_POTENTIAL': 'potential_energy_efficiency',
            
            # Lowercase variations
            'current energy rating': 'current_energy_rating',
            'potential energy rating': 'potential_energy_rating',
            'energy rating': 'current_energy_rating',
            'property type': 'property_type',
            'total floor area': 'total_floor_area',
            'floor area': 'total_floor_area',
            'postcode district': 'postcode',
            'post code': 'postcode',
            'post_code': 'postcode'
        }
        
        # Create a copy for processing
        df_processed = df.copy()
        
        # Standardize column names
        for old_col, new_col in column_mappings.items():
            if old_col in df_processed.columns:
                df_processed = df_processed.rename(columns={old_col: new_col})
        
        # Calculate improvement potential if possible
        efficiency_cols = ['current_energy_efficiency', 'potential_energy_efficiency']
        if all(col in df_processed.columns for col in efficiency_cols):
            df_processed['efficiency_improvement'] = (
                df_processed['potential_energy_efficiency'] - df_processed['current_energy_efficiency']
            )
            logger.info("Calculated efficiency improvement potential")
        
        # Create EPC numeric score if rating column exists
        if 'current_energy_rating' in df_processed.columns:
            rating_map = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7}
            
            # Convert column to string if needed
            if df_processed['current_energy_rating'].dtype != 'object':
                df_processed['current_energy_rating'] = df_processed['current_energy_rating'].astype(str)
            
            # Check for valid ratings and map them
            valid_ratings = df_processed['current_energy_rating'].str.match('^[A-G]$')
            if valid_ratings.any():
                df_processed.loc[valid_ratings, 'current_rating_score'] = (
                    df_processed.loc[valid_ratings, 'current_energy_rating'].map(rating_map)
                )
                logger.info("Added numeric rating scores")
        
        # Save processed data
        df_processed.to_csv(output_filename, index=False)
        logger.info(f"Saved processed EPC data to {output_filename} with {len(df_processed)} records")
        
        return df_processed
        
    except Exception as e:
        logger.error(f"Error processing EPC data: {e}")
        # Save the raw data anyway
        df.to_csv(output_filename, index=False)
        logger.info(f"Saved raw data as processed due to processing error")
        return df

if __name__ == "__main__":
    # Run the function
    sample_size = 5000  # Limit to 5000 records for testing
    fetch_epc_ratings(sample_size=sample_size)