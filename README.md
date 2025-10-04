# KyzerEyeStockLabs

A Python-based stock data collection and analysis toolkit that leverages Yahoo Finance to gather historical stock market data for portfolio analysis and research.

## 🚀 Overview

KyzerEyeStockLabs is designed to streamline the process of collecting historical stock data for multiple tickers, making it easy to build datasets for financial analysis, backtesting, and portfolio research. The project uses Yahoo Finance's API through the `yfinance` library to fetch reliable, up-to-date market data.

## 📁 Project Structure

```
KyzeEyeStockLabs/
├── get_stock_data/           # Stock data collection module
│   ├── stock_scraper.py      # Core data scraper class
│   ├── multiple_stocks_example.py  # Example usage script
│   ├── fetch_and_store_data.py     # Fetch data to CSV + Database
│   ├── update_stock_data.py        # Update existing data
│   ├── stock_symbols.txt     # Configuration file for stock symbols
│   ├── requirements.txt      # Python dependencies
│   ├── csv_files/           # Output directory for CSV files
│   │   ├── A_historical_data.csv
│   │   ├── AAPL_historical_data.csv
│   │   ├── GOOGL_historical_data.csv
│   │   ├── MSFT_historical_data.csv
│   │   ├── TSLA_historical_data.csv
│   │   ├── DOMO_historical_data.csv
│   │   └── portfolio_1year_data.csv
│   └── README.md            # Detailed module documentation
├── backend/                 # Flask API backend
│   ├── app.py              # Main Flask application
│   ├── app_config.py       # Configuration settings
│   ├── requirements.txt    # Backend dependencies
│   ├── test_api.py         # API test script
│   ├── test_wyckoff_api.py # Wyckoff API test script
│   ├── calculate_indicators.py # Technical indicators calculator
│   ├── generate_wyckoff_report.py # Wyckoff analysis report generator
│   ├── models/             # Database models
│   ├── services/           # Business logic (stock, indicators, wyckoff)
│   ├── routes/             # API endpoints (stocks, indicators, wyckoff)
│   ├── config/             # Configuration files (indicators)
│   └── utils/              # Database utilities
├── sql_queries.sql         # Database schema
├── remove_adj_close_column.sql  # Database migration script
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## ✨ Features

- **📊 Multi-Stock Data Collection**: Fetch historical data for multiple stocks simultaneously
- **⏰ Flexible Time Periods**: Support for various time periods (1y, 6mo, 3mo, 2y, 5y, max)
- **📝 Symbol Configuration**: Easy-to-edit text file for managing stock symbols
- **💾 Multiple Export Formats**: Save individual CSV files per stock or combined portfolio data
- **🗄️ MySQL Database Integration**: Store data in MySQL database for efficient querying
- **🌐 RESTful API**: Flask-based API for programmatic data access
- **🔄 Smart Updates**: Update system that adds only new data (no duplicates or overwrites)
- **📈 Technical Indicators**: Pre-calculated indicators (RSI, EMA, SMA, ATR, MACD, Bollinger Bands, etc.)
- **🎯 Wyckoff Method Analysis**: Advanced price action and volume analysis for institutional trading patterns
- **🛡️ Error Handling**: Robust error handling with detailed logging and failure reporting
- **⚡ Rate Limiting**: Built-in delays to respect API limits and be a good citizen
- **🧹 Data Cleaning**: Automatic data cleaning and formatting for analysis-ready output

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd KyzeEyeStockLabs
   ```

2. **Install dependencies**:
   ```bash
   cd get_stock_data
   pip install -r requirements.txt
   
   cd ../backend
   pip install -r requirements.txt
   ```

3. **Set up MySQL database**:
   ```bash
   # Create database
   mysql -u root -p -e "CREATE DATABASE kyzereye_stock_data;"
   
   # Create tables
   mysql -u root -p kyzereye_stock_data < sql_queries.sql
   
   # Remove adj_close column if upgrading existing database
   mysql -u root -p kyzereye_stock_data < remove_adj_close_column.sql
   ```

4. **Configure database connection**:
   ```bash
   cd backend
   cp env_example.txt .env
   # Edit .env with your MySQL credentials
   ```

## 🚀 Quick Start

### Basic Usage

```python
from get_stock_data.stock_scraper import StockDataScraper

# Create scraper instance
scraper = StockDataScraper()

# Get data for a single stock
df = scraper.get_stock_data("AAPL", period="1y")
scraper.save_to_csv(df, "AAPL")
```

### Portfolio Analysis

```python
# Load multiple symbols from file
symbols = scraper.load_symbols_from_file("stock_symbols.txt")

# Get 1 year of data for all symbols
portfolio_data = scraper.get_multiple_stocks_data(symbols, period="1y")

# Save individual and combined files
scraper.save_multiple_to_csv(portfolio_data, individual_files=True)
scraper.save_multiple_to_csv(portfolio_data, individual_files=False, combined_file="portfolio_1year_data.csv")
```

### Run the Example

```bash
cd get_stock_data
python multiple_stocks_example.py
```

### Database Integration

**Fetch and store data in both CSV files and MySQL database:**
```bash
cd get_stock_data
python fetch_and_store_data.py
```

**Update existing data (adds only new dates, no duplicates):**
```bash
cd get_stock_data
python update_stock_data.py
```

## 🌐 Flask API Backend

**Start the API server:**
```bash
cd backend
python3 app.py
```

**API will be available at:** http://localhost:5001

**Test the API:**
```bash
cd backend
python3 test_api.py
```

**Key API endpoints:**
- `GET /health` - Health check
- `GET /api` - API documentation
- `GET /api/stocks/` - Get all stock symbols
- `GET /api/stocks/AAPL` - Get stock data for a symbol
- `POST /api/stocks/AAPL/fetch` - Fetch fresh data for a symbol
- `GET /api/stocks/latest` - Get latest data for all stocks

## 📈 Technical Indicators

**Calculate technical indicators for all stocks:**
```bash
cd backend
python3 calculate_indicators.py
```

**Calculate for specific stock:**
```bash
python3 calculate_indicators.py AAPL
```

**Configure indicator periods:**
Edit `backend/config/indicators_config.py` to customize RSI, EMA, SMA periods, etc.

**Available indicators:**
- RSI (Relative Strength Index)
- EMA (Exponential Moving Average) - periods: 11, 21, 50, 200
- SMA (Simple Moving Average)
- ATR (Average True Range)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- Stochastic Oscillator
- Williams %R
- CCI (Commodity Channel Index)
- MFI (Money Flow Index)

## 🎯 Wyckoff Method Analysis

**Generate comprehensive Wyckoff analysis report:**
```bash
cd backend
python3 generate_wyckoff_report.py
```

**Wyckoff Analysis Features:**
- **Phase Detection**: Identifies Accumulation, Distribution, Markup, and Markdown phases
- **Volume-Price Analysis**: Analyzes volume patterns relative to price action
- **Support/Resistance Levels**: Identifies key price levels based on pivot points
- **Trading Signals**: Generates BUY/SELL/HOLD signals based on Wyckoff principles
- **Wyckoff Score**: Overall analysis score (0-100) with letter grades

**API Endpoints for Wyckoff Analysis:**
- `GET /api/wyckoff/` - Wyckoff API information
- `POST /api/wyckoff/analyze-all` - Analyze all stocks using Wyckoff Method
- `POST /api/wyckoff/<symbol>/analyze` - Analyze specific symbol
- `GET /api/wyckoff/report` - Get quick Wyckoff report
- `GET /api/wyckoff/<symbol>/phases` - Get Wyckoff phases for symbol
- `GET /api/wyckoff/<symbol>/signals` - Get trading signals for symbol

**Example Wyckoff Analysis Output:**
```
📊 TSLA
  Current Price: $426.07
  Current Phase: Markup (Confidence: 90.0%)
  Wyckoff Score: 73.9/100 (Grade: B)
  Primary Signal: BUY
  Volume Analysis: Neutral volume-price relationship
  Reasoning: Strong uptrend with volume confirmation
```

## 📊 Data Format

The scraper extracts the following standardized columns:

| Column | Description |
|--------|-------------|
| Date | Trading date (YYYY-MM-DD) |
| Open | Opening price |
| High | Highest price of the day |
| Low | Lowest price of the day |
| Close | Closing price |
| Volume | Trading volume |

## ⚙️ Configuration

### Stock Symbols

Edit `get_stock_data/stock_symbols.txt` to specify which stocks to analyze:

```
# Stock symbols to fetch data for
# One symbol per line, lines starting with # are comments
A
AAPL
GOOGL
MSFT
TSLA
DOMO
```

### Time Periods

Available time periods:
- `1y` - 1 year (default)
- `6mo` - 6 months
- `3mo` - 3 months
- `2y` - 2 years
- `5y` - 5 years
- `max` - Maximum available data

## 🔄 Data Update Workflow

**Initial Data Collection:**
```bash
cd get_stock_data
python fetch_and_store_data.py
```

**Regular Updates (every few days):**
```bash
cd get_stock_data
python update_stock_data.py
```

**What happens during updates:**
- ✅ **Database**: Adds only new dates (no duplicates, no updates)
- ✅ **CSV Files**: Appends only new dates (preserves all historical data)
- ✅ **Smart Filtering**: Automatically skips dates that already exist
- ✅ **Data Integrity**: Never modifies or overwrites existing data

## 📈 Use Cases

- **Portfolio Analysis**: Track historical performance of your investment portfolio
- **Backtesting**: Test trading strategies against historical data
- **Research**: Analyze market trends and stock correlations
- **Data Science**: Build machine learning models for stock prediction
- **Educational**: Learn about financial markets and data analysis
- **API Development**: Build applications that consume stock data via REST API

## 🔧 Advanced Usage

### Custom Output Directory

```python
scraper = StockDataScraper(output_dir="my_custom_folder")
```

### Rate Limiting

```python
# Add 2-second delay between requests
stock_data = scraper.get_multiple_stocks_data(symbols, delay=2.0)
```

### Error Handling

The scraper includes comprehensive error handling:
- Network timeout protection
- Invalid symbol detection
- Empty data validation
- Detailed logging of successes and failures

## 📋 Requirements

- Python 3.7+
- yfinance >= 0.2.0
- pandas >= 1.3.0

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## ⚠️ Important Notes

- **Rate Limiting**: The scraper includes built-in delays to respect Yahoo Finance's terms of service
- **Data Accuracy**: While Yahoo Finance provides reliable data, always verify critical financial decisions with official sources
- **Legal Compliance**: Ensure compliance with your local regulations when using financial data
- **API Changes**: Yahoo Finance may change their API; monitor for updates if data collection fails
- **Data Preservation**: The update system only adds new data - it never modifies or overwrites existing historical data

## 📄 License

This project is for educational and research purposes. Please respect Yahoo Finance's terms of service and use responsibly.

## 🆘 Support

For issues or questions:
1. Check the existing CSV files in `csv_files/` for expected output format
2. Review the `get_stock_data/README.md` for detailed module documentation
3. Ensure your internet connection is stable for data fetching
4. Verify stock symbols are valid and actively traded
