# BTR Investment Report Generator

A data-driven platform for analyzing Buy-to-Rent (BTR) investment opportunities across the UK using real property data and AI curation.

## Overview

This platform provides instant BTR investment reports for any UK property address. It analyzes data from multiple sources including Land Registry, EPC ratings, and OpenStreetMap amenities to calculate BTR investment scores, renovation scenarios, and rental projections.

## Features

- **Data-Driven Analysis**: Uses real Land Registry, EPC, and OpenStreetMap data
- **AI Curation**: Validates property valuations using OpenAI/Grok APIs
- **BTR Investment Score**: Rates properties on a 0-100 scale with component breakdowns  
- **Renovation Scenarios**: Calculates potential value uplift and ROI for different renovation options
- **Rental Forecasts**: Projects rental income growth over 5 years
- **PDF Reports**: Generates downloadable PDF reports with comprehensive analysis

## Project Structure

```
btr-report-generator/
├── data/                      # Data storage
│   ├── raw/                   # Raw data files
│   └── processed/             # Processed data files
├── scripts/                   # Data collection scripts
│   ├── fetch_land_registry.py
│   ├── fetch_epc_ratings.py
│   ├── fetch_osm_amenities.py
│   └── run_data_collection.py # Main data collection script
├── src/                       # Source code
│   ├── components/            # UI components
│   │   └── report_generator.py
│   ├── utils/                 # Utility functions
│   │   ├── data_processor.py
│   │   ├── llm_client.py
│   │   ├── pdf_generator.py
│   │   └── report_builder.py
│   └── app.py                 # Main Streamlit app
├── .env                       # Environment variables
├── .github/workflows/         # GitHub Actions workflows
├── .gitignore                 # Git ignore file
├── README.md                  # Project documentation
└── requirements.txt           # Python dependencies
```

## Setup Instructions

### Prerequisites

- Python 3.9+
- API keys for LLM integration (optional)
  - OpenAI API key or
  - Grok API key

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/btr-report-generator.git
   cd btr-report-generator
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the project root with the following variables:
   ```
   # Optional: API keys for LLM integration
   OPENAI_API_KEY=your_openai_api_key
   GROK_API_KEY=your_grok_api_key
   
   # Optional: EPC data API key
   EPC_API_KEY=your_epc_api_key
   ```

5. Run data collection:
   ```bash
   python scripts/run_data_collection.py --run-now
   ```

6. Start the Streamlit app:
   ```bash
   streamlit run src/app.py
   ```

### Deployment

To deploy the app on Streamlit Cloud:

1. Push your code to GitHub.

2. Go to [Streamlit Cloud](https://streamlit.io/cloud) and sign in.

3. Click "New app" and select your repository.

4. Set the main file path to `src/app.py`.

5. Add your secrets (API keys) in the Streamlit Cloud dashboard.

6. Deploy the app.

## Data Collection

Data is collected from three primary sources:

1. **Land Registry Price Paid Data**: Historical property transactions
2. **Energy Performance Certificates (EPC)**: Energy efficiency ratings
3. **OpenStreetMap (OSM)**: Location amenities data

Data collection runs weekly via GitHub Actions workflow and can also be triggered manually.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.