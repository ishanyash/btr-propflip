import streamlit as st
import logging
from pathlib import Path
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('btr_app')

# Configure Streamlit page
st.set_page_config(
    page_title="BTR Investment Report Generator",
    page_icon="🏘️",
    layout="wide"
)

# Import report generator component
from components.report_generator import display_report_generator

def main():
    """Main app function"""
    # Create necessary directories if they don't exist
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    
    # Display the report generator (single-page app)
    display_report_generator()

if __name__ == "__main__":
    main()