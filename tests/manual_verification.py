import sys
import os
import json
import logging

# Ensure src is in the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.smart_client import KnmiClient

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_verification():
    print("--- Starting KNMI Smart Client Verification ---")
    
    try:
        client = KnmiClient()
    except Exception as e:
        print(f"CRITICAL: Failed to initialize KnmiClient. Check your .env file. Error: {e}")
        return

    # 1. Test Fetch Locations
    print("\n[1/3] Testing 'fetch_locations'...")
    try:
        locations = client.fetch_locations()
        print("✅ Success: Fetched locations.")
        
        # Inspect structure to find a valid station ID
        station_ids = []
        if "features" in locations:
            print(f"Found {len(locations['features'])} stations.")
            for feature in locations["features"][:5]: # Print first 5 to verify structure
                s_id = feature.get("id")
                if not s_id and "properties" in feature:
                    s_id = feature["properties"].get("stationId")
                if s_id:
                    station_ids.append(str(s_id))
            
            if station_ids:
                print(f"Sample IDs found: {station_ids}")
            else:
                print("⚠️ Warning: No station IDs could be parsed from features.")
        else:
            print(f"⚠️ Warning: Response does not look like GeoJSON. Keys: {locations.keys()}")

    except Exception as e:
        print(f"❌ Failed: fetch_locations raised {e}")
        return

    if not station_ids:
        print("❌ Cannot proceed with data tests without a valid station ID.")
        return

    test_station = station_ids[0] # Pick the first one
    
    # 2. Test Fetch Data (One Day)
    # Format: ISO8601 time interval. 
    # OGC EDR usually expects start/end or a specific format.
    # The client currently implements start/end in the datetime param.
    print(f"\n[2/3] Testing 'fetch_data' for ONE DAY (Station: {test_station})...")
    try:
        # Example: Jan 1st 2024
        day_data = client.fetch_data(test_station, "2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z")
        print(f"✅ Success: Fetched daily data. Keys: {day_data.keys() if isinstance(day_data, dict) else type(day_data)}")
    except Exception as e:
        print(f"❌ Failed: fetch_data (daily) raised {e}")

    # 3. Test Fetch Data (One Year)
    print(f"\n[3/3] Testing 'fetch_data' for ONE YEAR (Station: {test_station})...")
    try:
        # Example: Year 2023
        year_data = client.fetch_data(test_station, "2023-01-01T00:00:00Z", "2023-12-31T23:59:59Z")
        print(f"✅ Success: Fetched yearly data. Keys: {year_data.keys() if isinstance(year_data, dict) else type(year_data)}")
    except Exception as e:
        print(f"❌ Failed: fetch_data (yearly) raised {e}")

if __name__ == "__main__":
    run_verification()
