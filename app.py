import streamlit as st
from utils.huggingface import generate_report, test_api_connection
from utils.pdf_generator import create_pdf

st.set_page_config(
    page_title="BTR Investment Report Generator",
    page_icon="🏘️",
    layout="wide"
)

def load_prompt_template():
    return """You are a seasoned, experienced property developer in the UK, qualified as an MRICS Chartered Surveyor and master builder. Your target is to generate a minimum 25% profit on cost per project. You will now receive an address, for which you must create a comprehensive property appraisal, planning analysis, development assessment, and feasibility study focused specifically on Build-to-Rent (BTR) investment potential.

Use the following address as the subject of your report:
**[INSERT_ADDRESS_HERE]**

Create a BTR Investment Report with these sections:

1. **BTR REPORT GENERATED [CURRENT_DATE]**
   Format the date as MMM DD, YYYY (e.g., MAY 05, 2025)

2. **The BTR Potential of**
   [ADDRESS] is [RATING].
   Where RATING is one of: excellent, good, above_average, average, below_average, poor, very_poor

3. **Current Specs | Estimated Value**
   Present in a side-by-side format:
   - Bedrooms/Bathrooms
   - Square footage
   - Price per sqft
   - Estimated current market value

4. **BTR SCORE**
   Provide an overall BTR investment score (0-100) and explain the factors affecting it:
   - Rental yield score (0-25)
   - Property type score (0-20)
   - Area quality score (0-20)
   - Growth potential score (0-20)
   - Renovation potential score (0-15)

5. **Investment Advice**
   2-3 sentences of specific advice for this property as a BTR investment.

6. **Market Commentary**
   2-3 sentences about the BTR market in this location.

7. **RENOVATION SCENARIOS**
   Present 2-3 potential renovation scenarios:
   - Cosmetic Refurbishment
   - Light Refurbishment
   - Extension (if applicable)
   For each include: Cost, New Value, Description, Value uplift (£ and %), ROI

8. **Renovation Advice**
   2-3 sentences of targeted renovation advice for BTR investors.

9. **RENTAL FORECAST**
   Show projected rental growth over 5 years with:
   - Current estimated monthly and annual rent
   - Year 1-5 projections
   - Growth rate percentages

10. **AREA OVERVIEW**
    Brief details about:
    - Crime Rate (Low/Medium/High)
    - School Rating (Outstanding/Good/Requires Improvement/Inadequate)
    - Transport Links (Excellent/Good/Average/Poor)
    
Add a disclaimer at the bottom about the accuracy of the report.
"""

def main():
    # --- Custom CSS ---
    st.markdown("""
    <style>
      .main-header { font-size:3rem; color:#000; }
      .highlight { color:#4CAF50; font-weight:500; }
      .search-container {
        background:#f9f9f9; padding:20px; border-radius:10px; margin-bottom:20px;
      }
      .report-header {
        background:#f5f5f5; padding:20px; border-radius:10px; margin-bottom:20px;
      }
      .stButton>button {
        background-color:#4CAF50; color:#fff; font-weight:bold;
      }
    </style>
    """, unsafe_allow_html=True)

    # --- Header + API check ---
    st.markdown(
        "<h1 class='main-header'>Get instant <span class='highlight'>BTR potential</span> for any home.</h1>",
        unsafe_allow_html=True
    )
    ok, msg = test_api_connection()
    if not ok:
        st.warning(f"⚠️ Hugging Face API issues: {msg}")
        st.info("Ensure HF_API_KEY in your .env has inference permission.")

    # --- Input form ---
    st.markdown("<div class='search-container'>", unsafe_allow_html=True)
    address = st.text_input("", placeholder="SEARCH AN ADDRESS", label_visibility="collapsed")
    col1, col2 = st.columns([5, 1])
    with col2:
        go = st.button("GENERATE", use_container_width=True)
    with col1:
        st.markdown("Enter a UK property address or postcode to generate a BTR investment report.")
    st.info("Tip: You can search single-family homes, apartments, and multi-family properties in the UK.")
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Session state ---
    if 'report_content' not in st.session_state:
        st.session_state.report_content = ""
        st.session_state.pdf_data = None
        st.session_state.address = ""

    # --- Generate on click ---
    if go and address:
        with st.spinner('Analyzing property and generating BTR report...'):
            tpl = load_prompt_template()
            report_md = generate_report(address, tpl)
            st.session_state.report_content = report_md
            st.session_state.address = address
            st.session_state.pdf_data = create_pdf(report_md, address)

    # --- Display & download ---
    if st.session_state.report_content:
        st.markdown("<div class='report-header'>", unsafe_allow_html=True)
        st.markdown(st.session_state.report_content)
        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.pdf_data:
            st.download_button(
                label="Download BTR Report (PDF)",
                data=st.session_state.pdf_data,
                file_name=f"BTR_Report_{st.session_state.address.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
            if st.button("Generate Another Report"):
                for key in ('report_content', 'pdf_data', 'address'):
                    st.session_state[key] = ""
                st.experimental_rerun()

    # --- Footer when no report ---
    if not st.session_state.report_content:
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

if __name__ == "__main__":
    main()
