import sys
import os
import json
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.utils.smart_client import KnmiClient

logging.basicConfig(level=logging.INFO)

def test_hourly():
    print("--- Testing Hourly Data Fetch (1 Year) ---")
    client = KnmiClient()
    station_id = "0-20000-0-06201"
    year = 2023
    t_start = f"{year}-01-01T00:00:00Z"
    t_end = f"{year}-12-31T23:59:59Z"
    
    try:
        data = client.fetch_data(station_id, t_start, t_end)
        print("✅ Fetched data.")
        
        # Count points
        cov = data['coverages'][0]
        ranges = cov['ranges']
        param = list(ranges.keys())[0]
        count = len(ranges[param]['values'])
        
        print(f"Parameter: {param}")
        print(f"Count: {count}")
        
        expected = 24 * 365
        print(f"Expected: ~{expected}")
        
        if count >= 8760:
            print("🎉 Success! We have hourly resolution.")
        else:
            print("⚠️ Warning: Count looks low for hourly data.")
            
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    test_hourly()
