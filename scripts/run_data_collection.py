#!/usr/bin/env python3
import os
import sys
import logging
import argparse
from datetime import datetime

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.append(project_root)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(project_root, 'data_collection.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('btr_data_collection')

def collect_all_data():
    """Collect data from all sources with improved error handling"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"Starting enhanced data collection at {timestamp}")
    
    # Create necessary directories
    os.makedirs('data/raw', exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)
    
    collection_results = {
        'land_registry': False,
        'ons_rentals': False,
        'planning_applications': False,
        'amenities': False,
        'epc_ratings': False
    }
    
    # 1. Land Registry data (usually works well)
    try:
        logger.info("Collecting Land Registry data...")
        from scripts.fetch_land_registry import fetch_land_registry_data
        result = fetch_land_registry_data()
        collection_results['land_registry'] = result is not None
        if result is not None:
            logger.info(f"✅ Land Registry: {len(result)} records collected")
        else:
            logger.warning("❌ Land Registry: No data collected")
    except Exception as e:
        logger.error(f"❌ Land Registry data collection failed: {e}")
        collection_results['land_registry'] = False
    
    # 2. ONS rental data (using fixed script)
    try:
        logger.info("Collecting ONS rental statistics...")
        # Check if we have the fixed script, otherwise use fallback
        try:
            # Try to import the fixed version first
            sys.path.insert(0, script_dir)
            from fixed_ons_rental_script import fetch_ons_rental_data
            result = fetch_ons_rental_data()
        except ImportError:
            # Fall back to original script
            from scripts.fetch_ons_rentals import fetch_ons_rental_data
            result = fetch_ons_rental_data()
        
        collection_results['ons_rentals'] = result is not None
        if result is not None:
            logger.info(f"✅ ONS Rentals: {len(result)} records collected")
        else:
            logger.warning("❌ ONS Rentals: No data collected")
    except Exception as e:
        logger.error(f"❌ ONS rental data collection failed: {e}")
        collection_results['ons_rentals'] = False
    
    # 3. Planning applications (using fixed script)
    try:
        logger.info("Collecting planning applications data...")
        try:
            # Try to import the fixed version first
            from fixed_planning_script import fetch_planning_applications
            result = fetch_planning_applications()
        except ImportError:
            # Fall back to original script
            from scripts.fetch_planning_applications import fetch_planning_applications
            result = fetch_planning_applications()
        
        collection_results['planning_applications'] = result is not None
        if result is not None:
            logger.info(f"✅ Planning Applications: {len(result)} records collected")
        else:
            logger.warning("❌ Planning Applications: No data collected")
    except Exception as e:
        logger.error(f"❌ Planning applications data collection failed: {e}")
        collection_results['planning_applications'] = False
    
    # 4. OSM amenities data (usually works)
    try:
        logger.info("Collecting OpenStreetMap amenities data...")
        from scripts.fetch_osm_amenities import fetch_osm_amenities
        result = fetch_osm_amenities()
        collection_results['amenities'] = result is not None
        if result is not None:
            logger.info(f"✅ Amenities: {len(result)} records collected")
        else:
            logger.warning("❌ Amenities: No data collected")
    except Exception as e:
        logger.error(f"❌ Amenities data collection failed: {e}")
        collection_results['amenities'] = False
    
    # 5. EPC ratings (using fixed script)
    try:
        logger.info("Collecting EPC ratings data...")
        epc_api_key = os.environ.get('EPC_API_KEY')
        if epc_api_key:
            logger.info("Using provided EPC API key")
        else:
            logger.info("No EPC API key found, will use fallback methods")
        
        try:
            # Try to import the fixed version first
            from fixed_epc_script import fetch_epc_ratings
            result = fetch_epc_ratings(sample_size=5000)
        except ImportError:
            # Fall back to original script
            from scripts.fetch_epc_ratings import fetch_epc_ratings
            result = fetch_epc_ratings(sample_size=5000)
        
        collection_results['epc_ratings'] = result is not None
        if result is not None:
            logger.info(f"✅ EPC Ratings: {len(result)} records collected")
        else:
            logger.warning("❌ EPC Ratings: No data collected")
    except Exception as e:
        logger.error(f"❌ EPC ratings data collection failed: {e}")
        collection_results['epc_ratings'] = False
    
    # Summary
    successful_collections = sum(collection_results.values())
    total_collections = len(collection_results)
    
    logger.info(f"Data collection completed: {successful_collections}/{total_collections} sources successful")
    
    # Print detailed results
    for source, success in collection_results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        logger.info(f"  {source.replace('_', ' ').title()}: {status}")
    
    # Check data files created
    try:
        processed_files = []
        if os.path.exists('data/processed'):
            processed_files = [f for f in os.listdir('data/processed') if f.endswith('.csv')]
        
        logger.info(f"Created {len(processed_files)} processed data files:")
        for file in processed_files:
            file_path = f'data/processed/{file}'
            file_size = os.path.getsize(file_path) / 1024 / 1024  # MB
            logger.info(f"  📊 {file} ({file_size:.2f} MB)")
    
    except Exception as e:
        logger.warning(f"Could not check processed files: {e}")
    
    if successful_collections >= 3:
        logger.info("🎉 Data collection successful! The enhanced BTR platform is ready to use.")
    elif successful_collections >= 1:
        logger.warning("⚠️ Partial data collection. Some features may use estimated data.")
    else:
        logger.error("❌ Data collection mostly failed. The platform will use fallback data.")
    
    return collection_results

def main():
    parser = argparse.ArgumentParser(description='Enhanced BTR Data Collection Tool')
    parser.add_argument('--run-now', action='store_true', help='Run data collection immediately')
    args = parser.parse_args()
    
    if args.run_now:
        logger.info("Running enhanced data collection immediately...")
        results = collect_all_data()
        
        # Print final summary
        print("\n" + "="*60)
        print("📊 DATA COLLECTION SUMMARY")
        print("="*60)
        
        successful = sum(results.values())
        total = len(results)
        
        print(f"Sources collected: {successful}/{total}")
        
        for source, success in results.items():
            status = "✅" if success else "❌"
            print(f"{status} {source.replace('_', ' ').title()}")
        
        print("\n💡 Next steps:")
        print("1. Set OpenAI API key: export OPENAI_API_KEY='your-key'")
        print("2. Start the application: streamlit run enhanced_btr_report_generator.py")
        print("3. Test with a UK address like 'London SW1A 1AA'")
        
        if successful >= 3:
            print("\n🎉 Ready to generate high-quality BTR reports!")
        else:
            print("\n⚠️ Limited data available. Reports will use more estimation.")
            
    else:
        logger.info("No action specified. Use --run-now to collect data.")
        print("Usage: python scripts/run_data_collection.py --run-now")

if __name__ == "__main__":
    main()