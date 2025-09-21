#!/usr/bin/env python3
"""
Test script for Technical Indicators API
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:5001"

def test_indicators_api():
    """Test the indicators API endpoints"""
    print("🧪 Testing Technical Indicators API")
    print("=" * 50)
    
    # Test 1: Get enabled indicators
    print("\n1. Testing GET /api/indicators/")
    try:
        response = requests.get(f"{BASE_URL}/api/indicators/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data['count']} enabled indicators")
            print(f"   Indicators: {', '.join(data['enabled_indicators'])}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Get indicators configuration
    print("\n2. Testing GET /api/indicators/config")
    try:
        response = requests.get(f"{BASE_URL}/api/indicators/config")
        if response.status_code == 200:
            data = response.json()
            print("✅ Success: Retrieved indicators configuration")
            print(f"   Available indicators: {len(data['config'])}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Get indicators for a specific symbol (if data exists)
    print("\n3. Testing GET /api/indicators/AAPL")
    try:
        response = requests.get(f"{BASE_URL}/api/indicators/AAPL")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: Found {data['count']} indicator records for AAPL")
        elif response.status_code == 404:
            print("⚠️  No indicators found for AAPL (this is expected if not calculated yet)")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Calculate indicators for a specific symbol
    print("\n4. Testing POST /api/indicators/AAPL/calculate")
    try:
        response = requests.post(f"{BASE_URL}/api/indicators/AAPL/calculate")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data['message']}")
            print(f"   Data points processed: {data['data_points']}")
        elif response.status_code == 404:
            print("⚠️  No stock data found for AAPL")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Get latest indicators for a symbol
    print("\n5. Testing GET /api/indicators/latest/AAPL")
    try:
        response = requests.get(f"{BASE_URL}/api/indicators/latest/AAPL")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: Found {data['count']} latest indicator values for AAPL")
        elif response.status_code == 404:
            print("⚠️  No latest indicators found for AAPL")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 6: Test indicators with parameters
    print("\n6. Testing GET /api/indicators/AAPL?indicator=RSI&limit=5")
    try:
        response = requests.get(f"{BASE_URL}/api/indicators/AAPL?indicator=RSI&limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: Found {data['count']} RSI records for AAPL")
        elif response.status_code == 404:
            print("⚠️  No RSI data found for AAPL")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_calculate_all_indicators():
    """Test calculating indicators for all symbols"""
    print("\n7. Testing POST /api/indicators/calculate-all")
    try:
        response = requests.post(f"{BASE_URL}/api/indicators/calculate-all")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data['message']}")
            results = data['results']
            print(f"   Total symbols: {results['total_symbols']}")
            print(f"   Successful: {len(results['success'])}")
            print(f"   Failed: {len(results['failed'])}")
            
            if results['success']:
                print("   Successful symbols:")
                for symbol_data in results['success'][:5]:  # Show first 5
                    print(f"     - {symbol_data['symbol']}: {symbol_data['data_points']} points")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main test function"""
    print("🚀 Starting Indicators API Tests...")
    
    # Test basic indicators API
    test_indicators_api()
    
    # Ask user if they want to test calculate-all (this can take a while)
    print("\n" + "=" * 50)
    response = input("Test calculate-all indicators? This may take a while (y/N): ")
    if response.lower() in ['y', 'yes']:
        test_calculate_all_indicators()
    
    print("\n🎉 Indicators API testing completed!")

if __name__ == "__main__":
    main()
