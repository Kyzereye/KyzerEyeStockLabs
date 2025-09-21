-- KyzerEye Stock Data Database Schema
-- Database: kyzereye_stock_data
-- Tables for stock symbols, daily OHLCV data, and technical indicators
use kyzereye_stock_data;

-- Drop tables if they exist (in reverse order due to foreign key constraints)
DROP TABLE IF EXISTS technical_indicators;
DROP TABLE IF EXISTS daily_stock_data;
DROP TABLE IF EXISTS stock_symbols;

-- Create database (uncomment if needed)
-- CREATE DATABASE IF NOT EXISTS kyzereye_stock_data;
-- USE kyzereye_stock_data;

-- Table 1: Stock Symbols/Tickers
CREATE TABLE IF NOT EXISTS stock_symbols (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    company_name VARCHAR(255),
    market_cap BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_symbol (symbol)
);

-- Table 2: Daily Stock Data (OHLCV)
CREATE TABLE IF NOT EXISTS daily_stock_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol_id INT NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol_id) REFERENCES stock_symbols(id) ON DELETE CASCADE,
    UNIQUE KEY unique_symbol_date (symbol_id, date),
    INDEX idx_symbol_id (symbol_id),
    INDEX idx_date (date),
    INDEX idx_symbol_date (symbol_id, date)
);

-- Table 3: Technical Indicators (Future-ready)
CREATE TABLE IF NOT EXISTS technical_indicators (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol_id INT NOT NULL,
    date DATE NOT NULL,
    indicator_name VARCHAR(50) NOT NULL,  -- 'RSI', 'ATR', 'EMA_20', 'SMA_50', etc.
    value DECIMAL(15,6),
    period INT,  -- For indicators like EMA_20, RSI_14, SMA_50
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol_id) REFERENCES stock_symbols(id) ON DELETE CASCADE,
    UNIQUE KEY unique_symbol_date_indicator_period (symbol_id, date, indicator_name, period),
    INDEX idx_symbol_id (symbol_id),
    INDEX idx_date (date),
    INDEX idx_indicator_name (indicator_name),
    INDEX idx_symbol_indicator (symbol_id, indicator_name)
);

-- Insert some sample stock symbols (optional - you can populate this from your stock_symbols.txt)
INSERT IGNORE INTO stock_symbols (symbol, company_name) VALUES
('A', 'Agilent Technologies Inc.'),
('AAPL', 'Apple Inc.'),
('GOOGL', 'Alphabet Inc. Class A'),
('MSFT', 'Microsoft Corporation'),
('TSLA', 'Tesla Inc.'),
('DOMO', 'Domo Inc.');

-- Useful queries for reference:

-- Get all stock symbols
-- SELECT * FROM stock_symbols ORDER BY symbol;

-- Get daily data for a specific stock
-- SELECT d.*, s.symbol 
-- FROM daily_stock_data d 
-- JOIN stock_symbols s ON d.symbol_id = s.id 
-- WHERE s.symbol = 'AAPL' 
-- ORDER BY d.date DESC;

-- Get technical indicators for a specific stock and indicator
-- SELECT t.*, s.symbol 
-- FROM technical_indicators t 
-- JOIN stock_symbols s ON t.symbol_id = s.id 
-- WHERE s.symbol = 'AAPL' AND t.indicator_name = 'RSI' 
-- ORDER BY t.date DESC;

-- Get latest data for all stocks
-- SELECT s.symbol, d.date, d.close, d.volume 
-- FROM stock_symbols s 
-- LEFT JOIN daily_stock_data d ON s.id = d.symbol_id 
-- WHERE d.date = (SELECT MAX(date) FROM daily_stock_data WHERE symbol_id = s.id) 
-- ORDER BY s.symbol;
