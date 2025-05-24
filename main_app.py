import streamlit as st
import os
import sys
import logging
from datetime import datetime

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir) if 'src' in script_dir else script_dir
sys.path.append(project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import the fixed report generator
try:
    from scripts.fixed_btr_report_generator import display_btr_report_generator
except ImportError:
    st.error("Could not import BTR Report Generator. Please ensure all files are in place.")
    st.stop()

def check_environment_setup():
    """Check if required environment variables are set"""
    required_vars = {
        'EPC_EMAIL': 'Your registered email for EPC API',
        'EPC_API_KEY': 'Your EPC API key'
    }
    
    optional_vars = {
        'OPENAI_API_KEY': 'OpenAI API for enhanced insights (optional)'
    }
    
    missing_required = []
    missing_optional = []
    
    for var, description in required_vars.items():
        if not os.environ.get(var):
            missing_required.append(f"• **{var}**: {description}")
    
    for var, description in optional_vars.items():
        if not os.environ.get(var):
            missing_optional.append(f"• **{var}**: {description}")
    
    return missing_required, missing_optional

def check_data_availability():
    """Check if required data files are available"""
    data_dir = 'data/processed'
    
    if not os.path.exists(data_dir):
        return False, "Data directory not found"
    
    required_prefixes = ['land_registry_', 'ons_rentals_']
    optional_prefixes = ['epc_ratings_', 'osm_amenities_']
    
    missing_required = []
    missing_optional = []
    
    try:
        files = os.listdir(data_dir)
        
        for prefix in required_prefixes:
            if not any(f.startswith(prefix) and f.endswith('.csv') for f in files):
                missing_required.append(prefix.replace('_', ' ').title())
        
        for prefix in optional_prefixes:
            if not any(f.startswith(prefix) and f.endswith('.csv') for f in files):
                missing_optional.append(prefix.replace('_', ' ').title())
        
        if missing_required:
            return False, f"Missing required data: {', '.join(missing_required)}"
        
        return True, f"Data available. Optional data missing: {', '.join(missing_optional) if missing_optional else 'All data present'}"
        
    except Exception as e:
        return False, f"Error checking data: {e}"

def display_setup_instructions():
    """Display setup instructions for missing requirements"""
    st.title("🚧 BTR Investment Platform Setup")
    
    missing_required, missing_optional = check_environment_setup()
    data_ok, data_status = check_data_availability()
    
    if missing_required or not data_ok:
        st.error("Setup incomplete. Please complete the following steps:")
        
        # Environment variables setup
        if missing_required:
            st.subheader("1. Required Environment Variables")
            st.write("Add these environment variables to your `.env` file:")
            
            st.code("""
# .env file
EPC_EMAIL=your-registered-email@example.com
EPC_API_KEY=your-epc-api-key
OPENAI_API_KEY=your-openai-key  # Optional
            """)
            
            st.write("**Missing variables:**")
            for var in missing_required:
                st.write(var)
            
            with st.expander("How to get API keys"):
                st.write("""
                **EPC API Key:**
                1. Register at https://epc.opendatacommunities.org/login
                2. Use the email and API key provided after registration
                
                **OpenAI API Key (Optional):**
                1. Sign up at https://platform.openai.com/
                2. Generate an API key in your account settings
                
                **Note**: Google Maps API is no longer required! We use free geocoding services.
                """)
        
        # Data collection setup
        if not data_ok:
            st.subheader("2. Data Collection")
            st.write(f"**Status:** {data_status}")
            
            st.write("Run the data collection scripts to gather required data:")
            
            st.code("""
# Run all data collection
python scripts/run_data_collection.py --run-now

# Or run individual scripts:
python scripts/fetch_land_registry.py
python scripts/fetch_ons_rentals.py
python scripts/fetch_epc_ratings.py
python scripts/fetch_osm_amenities.py
            """)
            
            if st.button("Test Data Collection Scripts"):
                with st.spinner("Testing data collection..."):
                    test_data_collection()
        
        st.subheader("3. Start the Application")
        st.write("Once setup is complete, refresh this page to access the BTR Report Generator.")
        
    else:
        # Setup is complete
        st.success("✅ Setup complete! All requirements met.")
        
        if missing_optional:
            st.info("Optional features available:")
            for var in missing_optional:
                st.write(f"• {var}")
        
        st.write(f"**Data Status:** {data_status}")
        
        if st.button("Launch BTR Report Generator", type="primary"):
            st.experimental_rerun()

def test_data_collection():
    """Test data collection scripts"""
    st.write("Testing data collection scripts...")
    
    # Test EPC API
    try:
        from scripts.fetch_epc_ratings import test_epc_api_connection
        if test_epc_api_connection():
            st.success("✅ EPC API connection successful")
        else:
            st.error("❌ EPC API connection failed")
    except Exception as e:
        st.error(f"❌ EPC API test failed: {e}")
    
    # Test ONS data
    try:
        from scripts.fetch_ons_rentals import test_ons_data_availability
        available_sources = test_ons_data_availability()
        if available_sources:
            st.success(f"✅ ONS data sources available: {len(available_sources)}")
        else:
            st.error("❌ No ONS data sources available")
    except Exception as e:
        st.error(f"❌ ONS data test failed: {e}")
    
    # Test OSM API
    try:
        from scripts.fetch_osm_amenities import test_overpass_api
        if test_overpass_api():
            st.success("✅ OpenStreetMap API connection successful")
        else:
            st.error("❌ OpenStreetMap API connection failed")
    except Exception as e:
        st.error(f"❌ OSM API test failed: {e}")
    
    # Test Free Geocoding
    try:
        from scripts.free_geocoding_service import geocode_location
        test_result = geocode_location("London SW1A 1AA")
        if test_result:
            st.success("✅ Free geocoding service working")
            st.write(f"Test result: {test_result['formatted_address']}")
        else:
            st.warning("⚠️ Free geocoding service has limited coverage")
    except Exception as e:
        st.error(f"❌ Free geocoding test failed: {e}")

def display_data_collection_status():
    """Display current data collection status"""
    with st.expander("📊 Data Collection Status"):
        data_dir = 'data/processed'
        
        if os.path.exists(data_dir):
            files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
            
            if files:
                st.write(f"**{len(files)} data files available:**")
                
                file_info = []
                for file in sorted(files):
                    file_path = os.path.join(data_dir, file)
                    file_size = os.path.getsize(file_path)
                    file_date = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    file_info.append({
                        'File': file,
                        'Size': f"{file_size / 1024:.1f} KB",
                        'Last Modified': file_date.strftime('%Y-%m-%d %H:%M')
                    })
                
                st.dataframe(file_info, use_container_width=True)
                
                # Data refresh button
                if st.button("🔄 Refresh Data Collection"):
                    with st.spinner("Running data collection..."):
                        try:
                            # Import and run data collection
                            from scripts.run_data_collection import collect_all_data
                            collect_all_data()
                            st.success("✅ Data collection completed")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"❌ Data collection failed: {e}")
            else:
                st.warning("No processed data files found")
        else:
            st.error("Data directory not found")

def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="BTR Investment Platform",
        page_icon="🏘️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-success {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .status-warning {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .status-error {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Check setup status
    missing_required, missing_optional = check_environment_setup()
    data_ok, data_status = check_data_availability()
    
    # Sidebar navigation
    st.sidebar.title("BTR Investment Platform")
    st.sidebar.write("---")
    
    # Add geocoding status
    st.sidebar.info("🌍 Using Free Geocoding\n(No API keys required)")
    
    if missing_required or not data_ok:
        # Setup mode
        st.sidebar.error("⚠️ Setup Required")
        page = st.sidebar.radio(
            "Navigation",
            ["Setup Instructions", "Data Status"]
        )
        
        if page == "Setup Instructions":
            display_setup_instructions()
        else:
            display_data_collection_status()
    
    else:
        # Normal operation mode
        st.sidebar.success("✅ Ready to Use")
        
        page = st.sidebar.radio(
            "Navigation",
            ["BTR Report Generator", "Data Status", "System Info"]
        )
        
        if page == "BTR Report Generator":
            display_btr_report_generator()
        elif page == "Data Status":
            display_data_collection_status()
        else:
            # System info page
            st.title("📋 System Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Environment Status")
                st.write(f"**Required APIs:** ✅ Configured")
                if missing_optional:
                    st.write(f"**Optional APIs:** ⚠️ {len(missing_optional)} missing")
                else:
                    st.write(f"**Optional APIs:** ✅ All configured")
                
                st.write(f"**Data Status:** {data_status}")
                st.write("**Geocoding:** 🌍 Free services (Nominatim + PostCodes.io)")
            
            with col2:
                st.subheader("Application Info")
                st.write(f"**Platform:** BTR Investment Analysis")
                st.write(f"**Version:** 2.0.0 (Free Geocoding)")
                st.write(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}")
                
                st.subheader("Free Services Used")
                st.write("• OpenStreetMap Nominatim API")
                st.write("• PostCodes.io (UK Postcodes)")
                st.write("• Comprehensive UK location database")
    
    # Footer
    st.sidebar.write("---")
    st.sidebar.caption("Built with Streamlit 🎈")
    st.sidebar.caption("Real UK property data analysis")
    st.sidebar.caption("🌍 No paid APIs required!")

if __name__ == "__main__":
    main()