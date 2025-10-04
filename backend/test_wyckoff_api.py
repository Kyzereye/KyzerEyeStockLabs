#!/usr/bin/env python3
"""
Test script for Wyckoff Analysis API endpoints
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5001"

def test_wyckoff_api():
    """Test Wyckoff Analysis API endpoints"""
    print("🔍 Wyckoff Analysis API Tests")
    print("=" * 50)
    
    # Test 1: Get Wyckoff API info
    print("Testing Wyckoff API info...")
    try:
        response = requests.get(f"{BASE_URL}/api/wyckoff/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Service: {data.get('service', 'N/A')}")
            print(f"Available endpoints: {len(data.get('endpoints', {}))}")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    
    # Test 2: Get quick Wyckoff report
    print("Testing quick Wyckoff report...")
    try:
        response = requests.get(f"{BASE_URL}/api/wyckoff/report")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Report Type: {data.get('report_type', 'N/A')}")
            print(f"Total Symbols Available: {data.get('total_symbols_available', 0)}")
            print(f"Analyzed Symbols: {data.get('analyzed_symbols', 0)}")
            
            if data.get('analysis_results'):
                print("\nQuick Analysis Results:")
                for result in data['analysis_results']:
                    print(f"  {result['symbol']}: {result['current_phase']} | Score: {result['wyckoff_score']} | Signal: {result['signal']}")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    
    # Test 3: Analyze specific symbol (AAPL)
    print("Testing Wyckoff analysis for AAPL...")
    try:
        response = requests.post(f"{BASE_URL}/api/wyckoff/AAPL/analyze")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            analysis = data.get('analysis', {})
            print(f"Symbol: {analysis.get('symbol', 'N/A')}")
            print(f"Current Price: ${analysis.get('current_price', 0):.2f}")
            print(f"Current Phase: {analysis.get('current_phase', {}).get('phase', 'N/A')}")
            print(f"Wyckoff Score: {analysis.get('wyckoff_score', {}).get('total_score', 0)}/100")
            print(f"Primary Signal: {analysis.get('signals', {}).get('primary_signal', 'N/A')}")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    
    # Test 4: Get phases for AAPL
    print("Testing Wyckoff phases for AAPL...")
    try:
        response = requests.get(f"{BASE_URL}/api/wyckoff/AAPL/phases")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            current_phase = data.get('current_phase', {})
            phases = data.get('phases', {})
            print(f"Current Phase: {current_phase.get('phase', 'N/A')}")
            print(f"Confidence: {current_phase.get('confidence', 0):.1%}")
            print(f"Phases Found:")
            for phase_name, phase_list in phases.items():
                print(f"  {phase_name.title()}: {len(phase_list)} periods")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    
    # Test 5: Get signals for AAPL
    print("Testing Wyckoff signals for AAPL...")
    try:
        response = requests.get(f"{BASE_URL}/api/wyckoff/AAPL/signals")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            signals = data.get('signals', {})
            print(f"Primary Signal: {signals.get('primary_signal', 'N/A')}")
            print(f"Confidence: {signals.get('confidence', 0):.1%}")
            print(f"Entry Signal: {signals.get('entry_signal', False)}")
            print(f"Exit Signal: {signals.get('exit_signal', False)}")
            if signals.get('reasoning'):
                print(f"Reasoning: {', '.join(signals['reasoning'])}")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    print("✅ Wyckoff API tests completed!")

if __name__ == "__main__":
    test_wyckoff_api()

