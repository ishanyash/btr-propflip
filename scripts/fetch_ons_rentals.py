import os
import pandas as pd
import requests
from datetime import datetime
import logging
from io import StringIO, BytesIO
import zipfile

# Set up logging
logger = logging.getLogger('btr_data_collection.ons')

def fetch_ons_rental_data(output_dir='data/raw'):
    """
    Fetch ONS Private Rental Market Statistics using multiple approaches
    
    Args:
        output_dir: Directory to save the output
    """
    # Create directories
    os.makedirs(output_dir, exist_ok=True)
    processed_dir = output_dir.replace('raw', 'processed')
    os.makedirs(processed_dir, exist_ok=True)
    
    # Filename with date
    today = datetime.now().strftime('%Y%m%d')
    filename = f"{output_dir}/ons_rentals_{today}.csv"
    processed_filename = f"{processed_dir}/ons_rentals_{today}.csv"
    
    logger.info("Fetching ONS rental statistics...")
    
    # Try multiple data sources in order of preference
    data_sources = [
        fetch_pipr_data,
        fetch_nomis_rental_data,
        fetch_ons_csv_data
    ]
    
    for fetch_function in data_sources:
        try:
            logger.info(f"Trying data source: {fetch_function.__name__}")
            df = fetch_function()
            
            if df is not None and len(df) > 0:
                # Save raw data
                df.to_csv(filename, index=False)
                logger.info(f"Raw ONS data saved to {filename}")
                
                # Process the data
                processed_df = process_rental_data(df)
                
                # Save processed data
                processed_df.to_csv(processed_filename, index=False)
                logger.info(f"Processed ONS data saved to {processed_filename} with {len(processed_df)} records")
                
                return processed_df
                
        except Exception as e:
            logger.warning(f"Failed to fetch from {fetch_function.__name__}: {e}")
            continue
    
    logger.error("All ONS data sources failed")
    return None

def fetch_pipr_data():
    """Fetch Price Index of Private Rents (PIPR) data from ONS"""
    logger.info("Fetching PIPR data from ONS...")
    
    # ONS PIPR dataset URL (updated regularly)
    pipr_urls = [
        "https://www.ons.gov.uk/file?uri=/economy/inflationandpriceindices/datasets/privaterentandhousepricesuk/current/pipr190225.xlsx",
        "https://www.ons.gov.uk/file?uri=/economy/inflationandpriceindices/datasets/privaterentandhousepricesuk/current/pipr.xlsx"
    ]
    
    for url in pipr_urls:
        try:
            logger.info(f"Trying PIPR URL: {url}")
            
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            # Read Excel file from memory
            excel_data = pd.ExcelFile(BytesIO(response.content))
            logger.info(f"Excel sheets available: {excel_data.sheet_names}")
            
            combined_data = []
            
            # Process relevant sheets
            for sheet_name in excel_data.sheet_names:
                # Look for sheets with rental data
                if any(keyword in sheet_name.lower() for keyword in 
                      ['local', 'regional', 'authority', 'area', 'rent']):
                    
                    logger.info(f"Processing sheet: {sheet_name}")
                    
                    try:
                        # Try different header row positions
                        for header_row in [0, 1, 2, 3, 4, 5]:
                            try:
                                df = pd.read_excel(
                                    BytesIO(response.content), 
                                    sheet_name=sheet_name, 
                                    header=header_row
                                )
                                
                                # Check if this looks like valid data
                                if len(df) > 10 and len(df.columns) > 3:
                                    df['sheet_source'] = sheet_name
                                    df['header_row'] = header_row
                                    combined_data.append(df)
                                    logger.info(f"Successfully read {len(df)} rows from {sheet_name}")
                                    break
                                    
                            except Exception:
                                continue
                                
                    except Exception as e:
                        logger.warning(f"Could not process sheet {sheet_name}: {e}")
                        continue
            
            if combined_data:
                # Combine all valid sheets
                final_df = pd.concat(combined_data, ignore_index=True)
                logger.info(f"Successfully combined {len(final_df)} records from PIPR data")
                return final_df
                
        except Exception as e:
            logger.warning(f"Failed to fetch PIPR from {url}: {e}")
            continue
    
    raise Exception("All PIPR URLs failed")

def fetch_nomis_rental_data():
    """Fetch rental data from Nomis API"""
    logger.info("Fetching rental data from Nomis API...")
    
    # Nomis API endpoints for housing/rental data
    nomis_endpoints = [
        # House prices dataset
        "https://www.nomisweb.co.uk/api/v01/dataset/HOUSE_PRICES.data.csv?geography=TYPE432&time=latest",
        # Private rental market data (if available)
        "https://www.nomisweb.co.uk/api/v01/dataset/NM_141_1.data.csv?geography=TYPE432&time=latest"
    ]
    
    for endpoint in nomis_endpoints:
        try:
            logger.info(f"Trying Nomis endpoint: {endpoint}")
            
            response = requests.get(endpoint, timeout=60)
            response.raise_for_status()
            
            df = pd.read_csv(StringIO(response.text))
            
            if len(df) > 0:
                logger.info(f"Successfully fetched {len(df)} records from Nomis")
                df['data_source'] = 'nomis_api'
                return df
                
        except Exception as e:
            logger.warning(f"Nomis endpoint failed: {e}")
            continue
    
    raise Exception("All Nomis endpoints failed")

def fetch_ons_csv_data():
    """Fetch ONS data from direct CSV downloads"""
    logger.info("Fetching ONS data from CSV downloads...")
    
    # ONS direct CSV downloads
    csv_urls = [
        # Private rental market summary statistics
        "https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/housing/datasets/privaterentalmarketsummarystatisticsinengland/current/prms.csv",
        # Regional rental data
        "https://www.ons.gov.uk/file?uri=/economy/inflationandpriceindices/datasets/privaterentandhousepricesuk/current/regionaldata.csv"
    ]
    
    for url in csv_urls:
        try:
            logger.info(f"Trying CSV URL: {url}")
            
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            df = pd.read_csv(StringIO(response.text))
            
            if len(df) > 0:
                logger.info(f"Successfully fetched {len(df)} records from CSV")
                df['data_source'] = 'ons_csv'
                return df
                
        except Exception as e:
            logger.warning(f"CSV URL failed: {e}")
            continue
    
    raise Exception("All CSV URLs failed")

def process_rental_data(df):
    """Process raw rental data into standardized format"""
    logger.info("Processing rental data...")
    
    processed_df = df.copy()
    
    # Standardize column names
    column_mapping = {
        # Common column name variations
        'Area': 'region',
        'area': 'region',
        'AREA': 'region',
        'Local Authority': 'region',
        'local_authority': 'region',
        'Region': 'region',
        'REGION': 'region',
        
        'Date': 'date',
        'DATE': 'date',
        'Period': 'date',
        'PERIOD': 'date',
        'Time': 'date',
        
        'Value': 'value',
        'VALUE': 'value',
        'Price': 'value',
        'PRICE': 'value',
        'Rent': 'value',
        'RENT': 'value',
        'Monthly Rent': 'value',
        'Average Rent': 'value',
        'Mean Rent': 'value',
        'Median Rent': 'value',
        
        'Change': 'change',
        'CHANGE': 'change',
        'Annual Change': 'annual_change',
        'YoY Change': 'yoy_change',
        'Percentage Change': 'percentage_change'
    }
    
    # Apply column mapping
    for old_col, new_col in column_mapping.items():
        if old_col in processed_df.columns:
            processed_df[new_col] = processed_df[old_col]
    
    # Clean and standardize data
    if 'region' in processed_df.columns:
        # Clean region names
        processed_df['region'] = processed_df['region'].astype(str).str.strip()
        processed_df = processed_df[processed_df['region'].str.len() > 1]  # Remove empty regions
    
    if 'date' in processed_df.columns:
        # Convert dates to standard format
        try:
            processed_df['date'] = pd.to_datetime(processed_df['date'], errors='coerce')
        except:
            pass
    
    if 'value' in processed_df.columns:
        # Convert values to numeric
        processed_df['value'] = pd.to_numeric(processed_df['value'], errors='coerce')
        # Remove zero or negative values
        processed_df = processed_df[processed_df['value'] > 0]
    
    # Calculate year-on-year growth if we have date and value
    if all(col in processed_df.columns for col in ['region', 'date', 'value']):
        try:
            processed_df = processed_df.sort_values(['region', 'date'])
            processed_df['prev_year_value'] = processed_df.groupby('region')['value'].shift(12)
            processed_df['yoy_growth'] = (
                (processed_df['value'] / processed_df['prev_year_value'] - 1) * 100
            )
            logger.info("Calculated year-on-year growth rates")
        except Exception as e:
            logger.warning(f"Could not calculate YoY growth: {e}")
    
    # Add metadata
    processed_df['collection_date'] = datetime.now().strftime('%Y%m%d')
    processed_df['data_quality'] = 'processed'
    
    # Remove rows with all NaN values in key columns
    key_columns = ['region', 'value']
    available_key_columns = [col for col in key_columns if col in processed_df.columns]
    if available_key_columns:
        processed_df = processed_df.dropna(subset=available_key_columns, how='all')
    
    logger.info(f"Processed data: {len(processed_df)} records")
    
    # Log data summary
    if 'region' in processed_df.columns:
        unique_regions = processed_df['region'].nunique()
        logger.info(f"Data covers {unique_regions} unique regions")
    
    if 'value' in processed_df.columns:
        avg_value = processed_df['value'].mean()
        logger.info(f"Average rental value: £{avg_value:.2f}")
    
    return processed_df

def test_ons_data_availability():
    """Test availability of ONS data sources"""
    logger.info("Testing ONS data source availability...")
    
    test_urls = [
        "https://www.ons.gov.uk/economy/inflationandpriceindices/bulletins/privaterentandhousepricesuk/latest",
        "https://www.ons.gov.uk/peoplepopulationandcommunity/housing/datasets/privaterentalmarketsummarystatisticsinengland",
        "https://www.nomisweb.co.uk/api/v01/dataset.json"
    ]
    
    available_sources = []
    
    for url in test_urls:
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                available_sources.append(url)
                logger.info(f"✅ Available: {url}")
            else:
                logger.warning(f"❌ Unavailable ({response.status_code}): {url}")
        except Exception as e:
            logger.warning(f"❌ Error testing {url}: {e}")
    
    return available_sources

if __name__ == "__main__":
    # Set up console logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    # Test data availability first
    available_sources = test_ons_data_availability()
    
    if available_sources:
        logger.info(f"Found {len(available_sources)} available data sources")
        
        # Run the main function
        result = fetch_ons_rental_data()
        
        if result is not None:
            print(f"✅ Successfully collected {len(result)} ONS rental records")
            print(f"Columns: {list(result.columns)}")
            if len(result) > 0:
                print(f"Sample data:\n{result.head()}")
        else:
            print("❌ Failed to collect ONS rental data")
    else:
        print("❌ No ONS data sources are currently available")