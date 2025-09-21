"""
Test script for the Flask API
"""
import requests
import json
import time

BASE_URL = "http://localhost:5001"

def test_health_check():
    """Test health check endpoint"""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_api_info():
    """Test API info endpoint"""
    print("Testing API info...")
    response = requests.get(f"{BASE_URL}/api")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_sync_symbols():
    """Test syncing symbols from file"""
    print("Testing symbol sync...")
    response = requests.post(f"{BASE_URL}/api/stocks/sync", 
                           json={"filename": "../../get_stock_data/stock_symbols.txt"})
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_get_all_symbols():
    """Test getting all symbols"""
    print("Testing get all symbols...")
    response = requests.get(f"{BASE_URL}/api/stocks/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_fetch_single_stock():
    """Test fetching data for a single stock"""
    print("Testing fetch single stock (AAPL)...")
    response = requests.post(f"{BASE_URL}/api/stocks/AAPL/fetch", 
                           json={"period": "1y"})
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_get_stock_data():
    """Test getting stock data"""
    print("Testing get stock data for AAPL...")
    response = requests.get(f"{BASE_URL}/api/stocks/AAPL")
    print(f"Status: {response.status_code}")
    data = response.json()
    if data['success']:
        print(f"Found {data['count']} records for AAPL")
        if data['data']:
            print(f"Latest record: {data['data'][0]}")
    else:
        print(f"Error: {data['error']}")
    print()

def test_get_latest_data():
    """Test getting latest data for all stocks"""
    print("Testing get latest data...")
    response = requests.get(f"{BASE_URL}/api/stocks/latest")
    print(f"Status: {response.status_code}")
    data = response.json()
    if data['success']:
        print(f"Found latest data for {data['count']} stocks")
        for stock in data['data'][:3]:  # Show first 3
            print(f"  {stock['symbol']}: ${stock['close']} on {stock['date']}")
    else:
        print(f"Error: {data['error']}")
    print()

def main():
    """Run all tests"""
    print("=== KyzerEye Stock API Tests ===\n")
    
    try:
        # Test basic endpoints
        test_health_check()
        test_api_info()
        
        # Test symbol operations
        test_sync_symbols()
        test_get_all_symbols()
        
        # Test data operations
        test_fetch_single_stock()
        time.sleep(2)  # Give it time to process
        test_get_stock_data()
        test_get_latest_data()
        
        print("=== All tests completed ===")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API server.")
        print("Make sure the Flask app is running on http://localhost:5000")
    except Exception as e:
        print(f"Error during testing: {e}")

if __name__ == "__main__":
    main()
