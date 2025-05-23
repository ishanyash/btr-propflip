# BTR Investment Platform Pro

> Professional Buy-to-Rent investment analysis using real UK government data

## ✨ Features

- 🏠 **Real Property Data** - Land Registry, ONS, EPC databases
- 📊 **Professional Reports** - PDF generation with charts and analysis  
- 🎯 **No Fallbacks** - Uses only verified government data sources
- 🇬🇧 **UK-Wide Coverage** - Any valid UK postcode or address
- ⚡ **Fast Analysis** - Reports generated in under 30 seconds

## 🚀 Quick Start

### 1. Get API Keys

- **EPC API**: Register at https://epc.opendatacommunities.org/login
- **Google Maps**: Get from Google Cloud Console
- **OpenAI** (optional): Get from https://platform.openai.com/

### 2. Configure Environment

Add your API keys to `.env`:

```bash
EPC_EMAIL=your-email@example.com
EPC_API_KEY=your-epc-api-key
GOOGLE_MAPS_API_KEY=your-google-maps-key
OPENAI_API_KEY=your-openai-key
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Collect Data

```bash
python scripts/run_data_collection.py --run-now
```

### 5. Launch Application

```bash
streamlit run main_app.py
```

## 📈 Sample Output

**Input**: "SW1A 1AA, London"

**Output**: Professional PDF report with:
- Real property transaction data
- Current rental market analysis
- Energy efficiency ratings
- Local amenities assessment
- BTR investment score (0-100)
- AI-powered investment insights

## 🔧 Development

### Using Docker

```bash
docker-compose up --build
```

### Running Tests

```bash
pytest tests/
```

## 📊 Data Sources

- **Land Registry**: Property transaction data
- **ONS**: Official rental market statistics  
- **EPC Database**: Energy performance certificates
- **OpenStreetMap**: Local amenities data
- **Google Maps**: Address geocoding

## 🆘 Support

1. Check `.env` file has correct API keys
2. Verify data collection completed: `ls data/processed/`
3. Test individual scripts: `python scripts/fetch_*.py`
4. Check logs: `data_collection.log`

## �� License

MIT License

---

Built with ❤️ for UK property investors
