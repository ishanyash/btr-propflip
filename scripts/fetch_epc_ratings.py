import os
import pandas as pd
import requests
import base64
from datetime import datetime
import logging
from io import StringIO

# Set up logging
logger = logging.getLogger('btr_data_collection.epc')

def get_epc_auth_header():
    """Create proper Basic Auth header for EPC API"""
    email = os.environ.get('EPC_EMAIL')
    api_key = os.environ.get('EPC_API_KEY')
    
    if not email or not api_key:
        raise ValueError("EPC_EMAIL and EPC_API_KEY environment variables are required")
    
    # Create credentials string: email:api_key
    credentials = f"{email}:{api_key}"
    # Base64 encode the credentials
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    return f"Basic {encoded_credentials}"

def fetch_epc_ratings(output_dir='data/raw', postcode_area=None, sample_size=1000):
    """
    Fetch EPC (Energy Performance Certificate) data with proper authentication
    
    Args:
        output_dir: Directory to save the output
        postcode_area: Optional postcode area to filter (e.g., 'SW1A')
        sample_size: Maximum number of records to retrieve
    """
    # Create directories
    os.makedirs(output_dir, exist_ok=True)
    processed_dir = output_dir.replace('raw', 'processed')
    os.makedirs(processed_dir, exist_ok=True)
    
    # Filename with date
    today = datetime.now().strftime('%Y%m%d')
    filename = f"{output_dir}/epc_ratings_{today}.csv"
    processed_filename = f"{processed_dir}/epc_ratings_{today}.csv"
    
    logger.info("Fetching EPC ratings data...")
    
    try:
        # Build query parameters
        params = {
            'size': sample_size,
            'from': 0
        }
        
        # Add postcode filter if specified
        if postcode_area:
            params['postcode'] = postcode_area
            logger.info(f"Filtering by postcode area: {postcode_area}")
        
        # Create proper authentication header
        headers = {
            "Accept": "text/csv",
            "Authorization": get_epc_auth_header()
        }
        
        logger.info(f"Making API request for {sample_size} EPC records...")
        
        # Make API request
        response = requests.get(
            "https://epc.opendatacommunities.org/api/v1/domestic/search",
            headers=headers,
            params=params,
            timeout=60
        )
        
        response.raise_for_status()
        
        # Save raw data
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        logger.info(f"Raw EPC data saved to {filename}")
        
        # Process the data
        df = pd.read_csv(filename)
        
        if len(df) == 0:
            logger.warning("No EPC data retrieved")
            return None
        
        logger.info(f"Processing {len(df)} EPC records...")
        
        # Standardize column names (EPC API returns uppercase columns)
        column_mapping = {
            'POSTCODE': 'postcode',
            'ADDRESS1': 'address1',
            'ADDRESS2': 'address2', 
            'ADDRESS3': 'address3',
            'CURRENT_ENERGY_RATING': 'current_energy_rating',
            'POTENTIAL_ENERGY_RATING': 'potential_energy_rating',
            'CURRENT_ENERGY_EFFICIENCY': 'current_energy_efficiency',
            'POTENTIAL_ENERGY_EFFICIENCY': 'potential_energy_efficiency',
            'PROPERTY_TYPE': 'property_type',
            'BUILT_FORM': 'built_form',
            'CONSTRUCTION_AGE_BAND': 'construction_age_band',
            'TOTAL_FLOOR_AREA': 'total_floor_area',
            'INSPECTION_DATE': 'inspection_date',
            'LODGEMENT_DATE': 'lodgement_date'
        }
        
        # Rename columns that exist
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df[new_col] = df[old_col]
        
        # Calculate rating scores (A=1, B=2, ..., G=7)
        rating_map = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7}
        
        if 'current_energy_rating' in df.columns:
            df['current_rating_score'] = df['current_energy_rating'].map(rating_map)
            logger.info("Added numeric rating scores")
        
        if 'potential_energy_rating' in df.columns:
            df['potential_rating_score'] = df['potential_energy_rating'].map(rating_map)
        
        # Calculate efficiency improvement potential
        efficiency_cols = ['current_energy_efficiency', 'potential_energy_efficiency']
        if all(col in df.columns for col in efficiency_cols):
            df['efficiency_improvement'] = (
                df['potential_energy_efficiency'] - df['current_energy_efficiency']
            )
            logger.info("Calculated efficiency improvement potential")
        
        # Calculate investment opportunity score
        # Properties with poor ratings but high improvement potential are good targets
        if 'current_rating_score' in df.columns and 'efficiency_improvement' in df.columns:
            # Normalize improvement score (0-100)
            max_improvement = df['efficiency_improvement'].max()
            if max_improvement > 0:
                df['improvement_score'] = (df['efficiency_improvement'] / max_improvement) * 100
            
            # Weight poor rated properties higher (G=7 gets higher score than A=1)
            df['rating_weight'] = df['current_rating_score'] / 7.0 * 100
            
            # Calculate EPC investment opportunity score (0-100)
            # 60% weight on improvement potential, 40% on current poor rating
            if 'improvement_score' in df.columns:
                df['epc_opportunity_score'] = (
                    df['improvement_score'] * 0.6 + 
                    df['rating_weight'] * 0.4
                )
                logger.info("Calculated EPC investment opportunity scores")
        
        # Add data quality indicators
        df['data_quality'] = 'api_sourced'
        df['collection_date'] = today
        
        # Save processed data
        # Select key columns for the processed dataset
        key_columns = [
            'postcode', 'address1', 'address2', 'address3',
            'current_energy_rating', 'potential_energy_rating',
            'current_energy_efficiency', 'potential_energy_efficiency',
            'efficiency_improvement', 'current_rating_score', 'potential_rating_score',
            'epc_opportunity_score', 'property_type', 'built_form',
            'construction_age_band', 'total_floor_area',
            'inspection_date', 'lodgement_date',
            'data_quality', 'collection_date'
        ]
        
        # Only include columns that exist
        available_columns = [col for col in key_columns if col in df.columns]
        processed_df = df[available_columns]
        
        processed_df.to_csv(processed_filename, index=False)
        logger.info(f"Processed EPC data saved to {processed_filename} with {len(processed_df)} records")
        
        # Log summary statistics
        if 'current_energy_rating' in processed_df.columns:
            rating_counts = processed_df['current_energy_rating'].value_counts()
            logger.info(f"EPC Rating distribution: {rating_counts.to_dict()}")
        
        return processed_df
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching EPC data: {e}", exc_info=True)
        return None

def test_epc_api_connection():
    """Test EPC API connection and authentication"""
    try:
        headers = {
            "Accept": "text/csv",
            "Authorization": get_epc_auth_header()
        }
        
        # Test with minimal query
        params = {'size': 1}
        
        response = requests.get(
            "https://epc.opendatacommunities.org/api/v1/domestic/search",
            headers=headers,
            params=params,
            timeout=30
        )
        
        response.raise_for_status()
        
        logger.info("✅ EPC API connection successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ EPC API connection failed: {e}")
        return False

if __name__ == "__main__":
    # Set up console logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    # Test API connection first
    if test_epc_api_connection():
        # Run the main function with a sample
        sample_size = 100  # Start small for testing
        result = fetch_epc_ratings(sample_size=sample_size)
        
        if result is not None:
            print(f"✅ Successfully collected {len(result)} EPC records")
            print(f"Columns: {list(result.columns)}")
            if len(result) > 0:
                print(f"Sample data:\n{result.head()}")
        else:
            print("❌ Failed to collect EPC data")
    else:
        print("❌ EPC API connection test failed. Check your credentials.")