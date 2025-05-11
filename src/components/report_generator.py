import streamlit as st
import logging
from pathlib import Path
import sys
import os

# Add parent directory to path so we can import our utils
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

from utils.report_builder import build_btr_report, build_report_markdown
from utils.pdf_generator import generate_btr_report_pdf

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('btr_components.report_generator')

def display_report_generator():
    """Display the BTR report generator interface"""
    # Check if data files exist
    data_dir = Path("data/processed")
    data_files = list(data_dir.glob("*.csv")) if data_dir.exists() else []
    
    if not data_files:
        st.warning("""
        Limited data files detected. The BTR Report Generator will use estimated values for many calculations.
        For best results, run the data collection script:
        ```
        python scripts/run_data_collection.py --run-now
        ```
        """)
    
    # Add custom CSS
    st.markdown(
        """
        <style>
        .main-header {
            font-size: 3rem;
            margin-bottom: 0;
            padding-bottom: 0;
            color: black;
        }
        .highlight {
            color: #4CAF50;
            font-weight: 500;
        }
        .search-container {
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .report-header {
            background-color: #f5f5f5;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        </style>
        """, 
        unsafe_allow_html=True
    )
    
    # Header
    st.markdown("<h1 class='main-header'>Get instant <span class='highlight'>BTR potential</span> for any home.</h1>", unsafe_allow_html=True)
    
    # Search box
    st.markdown("<div class='search-container'>", unsafe_allow_html=True)
    
    address_input = st.text_input("", placeholder="SEARCH AN ADDRESS", label_visibility="collapsed")
    
    col1, col2 = st.columns([5, 1])
    
    with col2:
        generate_button = st.button("GENERATE", use_container_width=True)
    
    with col1:
        st.markdown("Enter a UK property address or postcode to generate a BTR investment report.")
    
    st.markdown("<div class='tip-container'>", unsafe_allow_html=True)
    st.info("Tip: You can search single-family homes, apartments, and multi-family properties in the UK.")
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Initialize session state for report data
    if 'report_data' not in st.session_state:
        st.session_state.report_data = None
    
    if 'report_markdown' not in st.session_state:
        st.session_state.report_markdown = None
    
    if 'report_pdf' not in st.session_state:
        st.session_state.report_pdf = None
    
    # Generate report when button is clicked
    if generate_button and address_input:
        with st.spinner('Analyzing property and generating BTR report...'):
            # Process the address and generate report
            try:
                # Build the BTR report
                report_data = build_btr_report(address_input)
                
                # Convert to markdown for display
                report_markdown = build_report_markdown(report_data)
                
                # Generate PDF
                if 'error' not in report_data:
                    report_pdf = generate_btr_report_pdf(report_data)
                else:
                    report_pdf = None
                
                # Store in session state
                st.session_state.report_data = report_data
                st.session_state.report_markdown = report_markdown
                st.session_state.report_pdf = report_pdf
                
            except Exception as e:
                st.error(f"An error occurred while generating the report: {str(e)}")
                logger.error(f"Error in report generation: {e}", exc_info=True)
    
    # Display report if available
    if st.session_state.report_markdown:
        st.markdown("<div class='report-header'>", unsafe_allow_html=True)
        
        # Display markdown report
        st.markdown(st.session_state.report_markdown)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Download PDF button
        if st.session_state.report_pdf:
            address = st.session_state.report_data.get('address', '').replace(' ', '_')
            download_name = f"BTR_Report_{address}.pdf"
            
            st.download_button(
                label="Download BTR Report (PDF)",
                data=st.session_state.report_pdf,
                file_name=download_name,
                mime="application/pdf"
            )
        
        # Generate new report button
        if st.button("Generate Another Report"):
            # Reset session state
            st.session_state.report_data = None
            st.session_state.report_markdown = None
            st.session_state.report_pdf = None
            # Rerun to refresh the app
            st.experimental_rerun()
    
    # Show info section if no report is being displayed
    elif not (generate_button and address_input):
        st.subheader("What is a BTR Investment Report?")
        st.write("""
        Our BTR (Buy-to-Rent) Investment Report provides a comprehensive analysis of a property's potential as a rental investment. 
        The report includes:
        
        - Property valuation and specifications
        - BTR investment score with component breakdowns
        - Rental income potential and yield calculations
        - Area analysis with amenities ratings
        - Renovation scenarios and their impact on value
        - Future rental income projections
        - Expert insights on the investment potential
        
        Simply enter a UK property address or postcode above and click "GENERATE" to get your free report.
        """)