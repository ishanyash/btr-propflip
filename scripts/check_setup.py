#!/usr/bin/env python3
import os
import sys
import logging
import argparse
import subprocess
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

def run_script_directly(script_path, script_name):
    """Run a Python script directly using subprocess"""
    try:
        logger.info(f"Running {script_name}...")
        
        # Check if script exists
        if not os.path.exists(script_path):
            logger.error(f"❌ Script not found: {script_path}")
            return False
        
        # Run the script using subprocess
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            logger.info(f"✅ {script_name} completed successfully")
            if result.stdout:
                logger.info(f"Output: {result.stdout[:200]}...")  # First 200 chars
            return True
        else:
            logger.error(f"❌ {script_name} failed with return code {result.returncode}")
            if result.stderr:
                logger.error(f"Error: {result.stderr[:500]}...")  # First 500 chars
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"❌ {script_name} timed out after 5 minutes")
        return False
    except Exception as e:
        logger.error(f"❌ {script_name} failed: {e}")
        return False

def collect_all_data():
    """Collect data from all sources using direct script execution"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"Starting enhanced data collection at {timestamp}")
    
    # Create necessary directories
    os.makedirs('data/raw', exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)
    
    # Define scripts and their paths
    scripts = [
        ('scripts/fetch_land_registry.py', 'Land Registry'),
        ('scripts/fetch_ons_rentals.py', 'ONS Rentals'),
        ('scripts/fetch_planning_applications.py', 'Planning Applications'),
        ('scripts/fetch_osm_amenities.py', 'OpenStreetMap Amenities'),
        ('scripts/fetch_epc_ratings.py', 'EPC Ratings')
    ]
    
    results = {}
    successful_count = 0
    
    # Run each script
    for script_path, script_name in scripts:
        full_script_path = os.path.join(project_root, script_path)
        logger.info(f"Collecting {script_name}...")
        
        success = run_script_directly(full_script_path, script_name)
        results[script_name] = success
        
        if success:
            successful_count += 1
    
    # Check what data files were created
    processed_dir = os.path.join(project_root, 'data', 'processed')
    data_files = []
    if os.path.exists(processed_dir):
        data_files = [f for f in os.listdir(processed_dir) if f.endswith('.csv')]
    
    # Log summary
    logger.info(f"Data collection completed: {successful_count}/{len(scripts)} sources successful")
    
    for script_name, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        logger.info(f"  {script_name}: {status}")
    
    logger.info(f"Created {len(data_files)} processed data files:")
    for file in data_files:
        logger.info(f"  📄 {file}")
    
    if successful_count == 0:
        logger.error("❌ Data collection completely failed. Check individual script errors above.")
    elif successful_count < len(scripts):
        logger.warning(f"⚠️ Partial data collection. {successful_count}/{len(scripts)} sources successful.")
    else:
        logger.info("✅ All data sources collected successfully!")
    
    # Print summary
    print("\n" + "="*60)
    print("📊 DATA COLLECTION SUMMARY")
    print("="*60)
    print(f"Sources collected: {successful_count}/{len(scripts)}")
    
    for script_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {script_name}")
    
    if data_files:
        print(f"\n📄 Data files created:")
        for file in data_files:
            file_path = os.path.join(processed_dir, file)
            file_size = os.path.getsize(file_path) / 1024  # KB
            print(f"  • {file} ({file_size:.1f} KB)")
    
    print(f"\n💡 Next steps:")
    if successful_count > 0:
        print("1. Launch the application: streamlit run main_app.py")
        print("2. Test with a UK address like 'London SW1A 1AA'")
        if successful_count < len(scripts):
            print("3. Check failed scripts and API keys if needed")
    else:
        print("1. Check API keys in .env file")
        print("2. Test individual scripts: python scripts/fetch_*.py")
        print("3. Check internet connection and API availability")
    
    return successful_count > 0

def test_individual_scripts():
    """Test each script individually to help with debugging"""
    logger.info("Testing individual data collection scripts...")
    
    scripts = [
        ('scripts/fetch_land_registry.py', 'Land Registry'),
        ('scripts/fetch_ons_rentals.py', 'ONS Rentals'),
        ('scripts/fetch_planning_applications.py', 'Planning Applications'),
        ('scripts/fetch_osm_amenities.py', 'OpenStreetMap Amenities'),
        ('scripts/fetch_epc_ratings.py', 'EPC Ratings')
    ]
    
    for script_path, script_name in scripts:
        full_script_path = os.path.join(project_root, script_path)
        
        print(f"\n🧪 Testing {script_name}...")
        print(f"Script path: {full_script_path}")
        
        if not os.path.exists(full_script_path):
            print(f"❌ Script file not found!")
            continue
        
        try:
            # Quick syntax check
            result = subprocess.run(
                [sys.executable, '-m', 'py_compile', full_script_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✅ Syntax check passed")
            else:
                print(f"❌ Syntax error: {result.stderr}")
                continue
                
        except Exception as e:
            print(f"❌ Error checking script: {e}")

def main():
    parser = argparse.ArgumentParser(description='BTR Data Collection Tool')
    parser.add_argument('--run-now', action='store_true', help='Run data collection immediately')
    parser.add_argument('--test', action='store_true', help='Test individual scripts without running them')
    args = parser.parse_args()
    
    if args.test:
        test_individual_scripts()
    elif args.run_now:
        logger.info("Running enhanced data collection immediately...")
        success = collect_all_data()
        if not success:
            sys.exit(1)
    else:
        logger.info("No action specified. Use --run-now to collect data or --test to test scripts.")
        print("\nUsage:")
        print("  python scripts/run_data_collection.py --run-now    # Run data collection")
        print("  python scripts/run_data_collection.py --test       # Test scripts")

if __name__ == "__main__":
    main()