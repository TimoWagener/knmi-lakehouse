import sys
import os
import json
import logging
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.utils.smart_client import KnmiClient

logging.basicConfig(level=logging.INFO)

def analyze_de_bilt():
    print("--- Analyzing Collection & De Bilt Station ---")
    client = KnmiClient()
    collection = "hourly-in-situ-meteorological-observations-validated"
    
    # 1. Fetch Collection Metadata (Parameters descriptions)
    print(f"\n[1/3] Fetching Collection Metadata...")
    url = f"{client.settings.KNMI_API_BASE_URL}/collections/{collection}"
    headers = {"Authorization": client.settings.KNMI_API_TOKEN}
    
    try:
        r = requests.get(url, headers=headers, params={"f": "json"})
        r.raise_for_status()
        meta = r.json()
        
        print(f"Title: {meta.get('title')}")
        print(f"Description: {meta.get('description')}")
        
        # List parameters if available in metadata
        if "parameter_names" in meta:
            print(f"\nMetadata Parameters ({len(meta['parameter_names'])}):")
            for p, details in meta["parameter_names"].items():
                desc = details.get("description", "No desc")
                unit = details.get("unit", {}).get("symbol", "-")
                print(f" - {p}: {desc} ({unit})")
                
    except Exception as e:
        print(f"❌ Failed to fetch collection metadata: {e}")

    # 2. Find 'De Bilt' Station ID
    print(f"\n[2/3] Searching for 'De Bilt'...")
    de_bilt_id = None
    try:
        locations = client.fetch_locations()
        if "features" in locations:
            for feat in locations["features"]:
                props = feat.get("properties", {})
                name = props.get("name", "Unknown")
                
                if "bilt" in name.lower():
                    de_bilt_id = feat.get("id")
                    print(f"✅ Found Station: {name}")
                    print(f"   ID: {de_bilt_id}")
                    print(f"   WMO: {props.get('wmoId')}")
                    print(f"   Coords: {feat.get('geometry', {}).get('coordinates')}")
                    break
        
        if not de_bilt_id:
            print("❌ 'De Bilt' not found in station list.")
            return

    except Exception as e:
        print(f"❌ Failed to fetch locations: {e}")
        return

    # 3. Fetch Actual Data for De Bilt (Check Parameters)
    print(f"\n[3/3] Fetching Data for De Bilt (2024-01-01)...")
    try:
        # One day of data to check parameters
        data = client.fetch_data(de_bilt_id, "2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z")
        
        cov = data['coverages'][0]
        ranges = cov['ranges']
        params = list(ranges.keys())
        
        print(f"✅ Data Fetch Successful.")
        print(f"Available Data Parameters ({len(params)}):")
        print(params)
        
    except Exception as e:
        print(f"❌ Failed to fetch data: {e}")

if __name__ == "__main__":
    analyze_de_bilt()
