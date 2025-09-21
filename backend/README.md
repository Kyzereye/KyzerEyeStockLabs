# KyzerEye Stock Data Backend

Flask-based API backend for managing stock data in MySQL database.

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Create environment file (copy from example)
cp env_example.txt .env
# Edit .env with your MySQL credentials
```

### 2. Configure Database

Edit `.env` file with your MySQL settings:
```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-password
MYSQL_DATABASE=kyzereye_stock_data
```

### 3. Create Database Tables

Run the SQL queries in your MySQL database:
```bash
mysql -u root -p kyzereye_stock_data < ../sql_queries.sql
```

### 4. Start the API Server

```bash
python app.py
```

The API will be available at: http://localhost:5000

## 📡 API Endpoints

### Health Check
- `GET /health` - Check if API is running

### API Information
- `GET /api` - Get API documentation and available endpoints

### Stock Symbols
- `GET /api/stocks/` - Get all stock symbols
- `POST /api/stocks/sync` - Sync symbols from file to database
- `GET /api/stocks/<symbol>/info` - Get symbol information

### Stock Data
- `GET /api/stocks/<symbol>` - Get stock data for a symbol
- `POST /api/stocks/<symbol>/fetch` - Fetch and store data for a symbol
- `POST /api/stocks/fetch-all` - Fetch data for all symbols
- `GET /api/stocks/latest` - Get latest data for all stocks

## 🔧 Usage Examples

### Sync Symbols from File
```bash
curl -X POST http://localhost:5000/api/stocks/sync \
  -H "Content-Type: application/json" \
  -d '{"filename": "../../get_stock_data/stock_symbols.txt"}'
```

### Fetch Data for Single Stock
```bash
curl -X POST http://localhost:5000/api/stocks/AAPL/fetch \
  -H "Content-Type: application/json" \
  -d '{"period": "1y"}'
```

### Get Stock Data
```bash
curl "http://localhost:5000/api/stocks/AAPL?start_date=2023-01-01&end_date=2023-12-31"
```

### Fetch All Stocks Data
```bash
curl -X POST http://localhost:5000/api/stocks/fetch-all \
  -H "Content-Type: application/json" \
  -d '{"period": "1y", "delay": 1.0}'
```

## 🧪 Testing

Run the test script to verify everything works:

```bash
# Make sure the API server is running first
python test_api.py
```

## 📁 Project Structure

```
backend/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── env_example.txt       # Environment variables example
├── test_api.py          # API test script
├── models/
│   └── stock_models.py   # Database models
├── services/
│   └── stock_service.py  # Business logic
├── routes/
│   └── stock_routes.py   # API endpoints
└── utils/
    └── database.py       # Database utilities
```

## 🔄 Integration with Existing Scraper

The backend integrates seamlessly with your existing `get_stock_data` scraper:

- Uses the same `StockDataScraper` class
- Reads from the same `stock_symbols.txt` file
- Maintains the same data format and structure
- Adds database persistence layer

## 🚀 Next Steps

1. **Technical Indicators**: Add RSI, ATR, EMA calculation services
2. **Backtesting**: Create backtesting API endpoints
3. **Scheduling**: Add automated data updates
4. **Frontend**: Build web interface for data visualization

## ⚠️ Notes

- The API respects Yahoo Finance rate limits with configurable delays
- All database operations include error handling and logging
- CORS is enabled for future frontend integration
- The backend is designed to be easily extensible
