-- Remove adj_close column from existing database
-- Run this in MySQL to update your existing database

USE kyzereye_stock_data;

-- Drop the adj_close column from daily_stock_data table
ALTER TABLE daily_stock_data DROP COLUMN IF EXISTS adj_close;

-- Verify the table structure
DESCRIBE daily_stock_data;
