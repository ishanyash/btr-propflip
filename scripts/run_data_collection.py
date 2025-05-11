#!/usr/bin/env python3
import os
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('btr_data_collection')

# Explicitly load the .env file
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

# Add the project root to the Python path
sys.path.append(project_root)

# Import data collection scripts
from fetch_land_registry import fetch_land_registry_data
from fetch_epc_ratings import fetch_epc_ratings
from fetch_osm_amenities import fetch_osm_amenities

def collect_all_data():
    """Collect data from all sources"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"Starting data collection at {timestamp}")
    
    # Create necessary directories
    Path('data/raw').mkdir(parents=True, exist_ok=True)
    Path('data/processed').mkdir(parents=True, exist_ok=True)
    Path('data/sample').mkdir(parents=True, exist_ok=True)
    
    try:
        # Land Registry data
        logger.info("Collecting Land Registry data...")
        fetch_land_registry_data()
        
        # EPC ratings data
        logger.info("Collecting EPC ratings data...")
        # Print environment variables to debug
        api_email = os.getenv('EPC_API_EMAIL')
        api_key = os.getenv('EPC_API_KEY')
        if api_email and api_key:
            logger.info("EPC API credentials found")
        else:
            logger.warning("EPC API credentials missing")
        
        fetch_epc_ratings(sample_size=10000)  # Limit sample size for regular runs
        
        # OSM amenities
        logger.info("Collecting OpenStreetMap amenities data...")
        fetch_osm_amenities()
        
        logger.info("Data collection completed successfully")
        
    except Exception as e:
        logger.error(f"Error during data collection: {e}", exc_info=True)
        raise

def main():
    parser = argparse.ArgumentParser(description='BTR Data Collection Tool')
    parser.add_argument('--run-now', action='store_true', help='Run data collection immediately')
    args = parser.parse_args()
    
    if args.run_now:
        logger.info("Running data collection immediately...")
        collect_all_data()
    else:
        logger.info("No action specified. Use --run-now to collect data.")

if __name__ == "__main__":
    main()