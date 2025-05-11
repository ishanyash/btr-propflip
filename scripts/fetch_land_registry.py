import os
import pandas as pd
import requests
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('data_collection.land_registry')

def fetch_land_registry_data(output_dir='data/raw', regions=None):
    """
    Fetch UK HM Land Registry Price Paid Data
    
    Documentation: https://www.gov.uk/guidance/about-the-price-paid-data
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    processed_dir = output_dir.replace('raw', 'processed')
    os.makedirs(processed_dir, exist_ok=True)
    
    # Filename with date
    today = datetime.now().strftime('%Y%m%d')
    filename = f"{output_dir}/land_registry_{today}.csv"
    processed_filename = f"{processed_dir}/land_registry_{today}.csv"
    
    logger.info(f"Downloading Land Registry data to {filename}...")
    
    # URL for the monthly update (public data)
    url = "http://prod.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com/pp-monthly-update-new-version.csv"
    
    # Column names according to documentation
    columns = [
        'transaction_uuid', 'price', 'date_of_transfer', 'postcode', 'property_type',
        'new_build_flag', 'tenure_type', 'primary_addressable_object_name',
        'secondary_addressable_object_name', 'street', 'locality', 'town_city',
        'district', 'county', 'ppd_category_type', 'record_status'
    ]
    
    try:
        # Stream download to handle large files
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        # Load and process
        logger.info(f"Downloaded data, now processing...")
        df = pd.read_csv(filename, header=None, names=columns)
        
        # Filter by region if specified
        if regions:
            df = df[df['county'].isin(regions)]
            logger.info(f"Filtered to regions: {regions}")
        
        # Save processed data
        df.to_csv(processed_filename, index=False)
        
        logger.info(f"Processed {len(df)} records. Saved to {processed_filename}")
        return df
        
    except Exception as e:
        logger.error(f"Error downloading Land Registry data: {e}")
        return None

if __name__ == "__main__":
    # Example usage
    regions = ['GREATER LONDON', 'MANCHESTER', 'BIRMINGHAM']
    fetch_land_registry_data(regions=regions)